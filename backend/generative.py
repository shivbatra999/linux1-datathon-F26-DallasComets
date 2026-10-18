"""Owner-only business summary generation backed by the local Granite service."""
from __future__ import annotations

from collections import Counter
import re

import httpx

from .config import (
    SIMPLECATER_LLM_MODEL,
    SIMPLECATER_LLM_REASONING_FORMAT,
    SIMPLECATER_LLM_TIMEOUT_SECONDS,
    SIMPLECATER_LLM_URL,
)
from .predictive import ModelUnavailable, load_model, recommend


class GenerationUnavailable(RuntimeError):
    """The configured Granite service could not produce a summary."""


def _final_model_text(content):
    cleaned = re.sub(r"<think>.*?</think>", "", content, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r"</?think>", "", cleaned, flags=re.IGNORECASE)
    answer_boundaries = list(re.finditer(
        r"(?:final answer|final response|answer):\s*",
        cleaned,
        flags=re.IGNORECASE,
    ))
    if answer_boundaries:
        cleaned = cleaned[answer_boundaries[-1].end():]
    else:
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", cleaned) if part.strip()]
        if len(paragraphs) > 1:
            instruction_pattern = re.compile(
                r"(?:we need to|write exactly|verified completed|prediction basis|"
                r"return only|do not mention|use only|the prompt|hidden reasoning)",
                flags=re.IGNORECASE,
            )
            candidates = [paragraph for paragraph in paragraphs if not instruction_pattern.search(paragraph)]
            if candidates:
                cleaned = candidates[-1]
    cleaned = re.sub(
        r"\bprediction basis\b.*$",
        "",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )
    cleaned = re.sub(
        r"^(?:we need to write|write exactly|instructions?:?)[^.]*\.\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    return cleaned.strip()


def _prediction(menu_rows, history):
    if not menu_rows:
        return []

    bundle = load_model()
    trained_ids = {int(value) for value in bundle["item_ids"]}
    available = {
        row["id"]: row for row in menu_rows
        if row["is_available"]
    }
    mapping = {
        row["id"]: row["model_item_id"]
        for row in available.values()
        if row.get("model_item_id") in trained_ids
    }

    if len(set(mapping.values())) != len(mapping):
        raise GenerationUnavailable("Menu model mapping is ambiguous.")

    # Businesses without mapped items get measured popularity only.
    if not mapping:
        counts = Counter(
            item_id
            for order in history
            for item_id in set(order)
            if item_id in available
        )
        return [
            {
                "item_id": item_id,
                "reason": (
                    f'{available[item_id]["name"]}: ordered in '
                    f'{count} of {len(history)} completed orders.'
                ),
                "source": "fallback",
            }
            for item_id, count in counts.most_common(2)
        ]

    categories = {1: "Lunch", 2: "Lunch", 3: "Lunch",
                  4: "Breakfast", 5: "Drinks", 6: "Desserts"}
    features = [
        {
            "id": model_id,
            "category": categories.get(model_id, "Other"),
            "available": True,
        }
        for model_id in mapping.values()
    ]
    scoped_history = [
        [mapping[item_id] for item_id in set(order) if item_id in mapping]
        for order in history
    ]
    scoped_history = [order for order in scoped_history if order]

    counts = Counter(item for order in scoped_history for item in order)
    selected_id = (
        counts.most_common(1)[0][0] if counts
        else min(mapping.values())
    )
    picks = recommend(features, scoped_history, selected_id, [])

    database_ids = {
        model_id: database_id
        for database_id, model_id in mapping.items()
    }
    return [
        {
            "item_id": database_ids[pick["item_id"]],
            "reason": (
                available[database_ids[pick["item_id"]]]["name"]
                + ": " + pick["reason"]
            ),
            "source": pick["source"],
        }
        for pick in picks
        if pick["item_id"] != selected_id
    ]


def _summary_prompt(total, order_count, prediction):
    return (
        "Write two short sentences for a restaurant owner. "
        "Sentence one: summarize the sales. Sentence two: give one practical tip. "
        "Use only the facts below. Start your response with 'Final answer:'.\n"
        f"Verified completed order count: {order_count}\n"
        f"Verified completed sales total in USD: {total / 100:.2f}\n"
        f"Predictive result: {prediction}\n"
    )


def generate_summary(total, order_count, prediction) -> str:
    if not SIMPLECATER_LLM_URL or not SIMPLECATER_LLM_MODEL:
        raise GenerationUnavailable("Granite is not configured.")
    payload = {
        "model": SIMPLECATER_LLM_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You summarize verified business aggregates for an owner.",
            },
            {"role": "user", "content": _summary_prompt(total, order_count, prediction)},
        ],
        "temperature": 0.2,
        "max_tokens": 48,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    if SIMPLECATER_LLM_REASONING_FORMAT.lower() not in {"", "none"}:
        payload["reasoning_format"] = SIMPLECATER_LLM_REASONING_FORMAT
    try:
        response = httpx.post(
            f"{SIMPLECATER_LLM_URL}/chat/completions",
            json=payload,
            timeout=min(SIMPLECATER_LLM_TIMEOUT_SECONDS, 180),
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as error:
        detail = error.response.text[:200].strip()
        suffix = f" ({detail})" if detail else ""
        raise GenerationUnavailable(
            f"Granite rejected the summary request with HTTP {error.response.status_code}{suffix}."
        ) from error
    except httpx.TimeoutException as error:
        raise GenerationUnavailable(
            "Granite timed out while generating the summary at "
            f"{SIMPLECATER_LLM_URL}. LinuxONE is reachable, but inference did not "
            "finish before the timeout."
        ) from error
    except httpx.RequestError as error:
        raise GenerationUnavailable(
            f"Granite could not be reached at {SIMPLECATER_LLM_URL}."
        ) from error
    except httpx.HTTPError as error:
        raise GenerationUnavailable("Granite did not return a usable summary.") from error
    except (KeyError, IndexError, TypeError, ValueError) as error:
        raise GenerationUnavailable("Granite returned an invalid response shape.") from error
    if not isinstance(content, str):
        raise GenerationUnavailable("Granite returned an empty summary.")
    content = _final_model_text(content)
    if (
        not content
        or re.search(
            r"(?:we need to|write exactly|verified completed|prediction basis|"
            r"return only|do not mention|use only|sentence one:|sentence two:|"
            r"write two short sentences)",
            content,
            flags=re.IGNORECASE,
        )
    ):
        raise GenerationUnavailable(
            "Granite returned instructions instead of a final store assistant answer."
        )
    return content


def owner_summary(client, business_id):
    completed = (
        client.table("orders")
        .select("id,total")
        .eq("business_id", str(business_id))
        .ilike("status", "completed")
        .execute()
    ).data or []
    menu = (
        client.table("menu_items")
        .select("id,name,is_available,model_item_id")
        .eq("business_id", str(business_id))
        .eq("is_available", True)
        .order("name")
        .execute()
    ).data or []
    order_ids = [row["id"] for row in completed]
    lines = []
    if order_ids:
        lines = (
            client.table("order_items")
            .select("order_id,menu_item_id")
            .in_("order_id", order_ids)
            .execute()
        ).data or []
    history_by_order = {}
    for line in lines:
        history_by_order.setdefault(line["order_id"], []).append(line["menu_item_id"])
    try:
        prediction = _prediction(menu, list(history_by_order.values()))
    except ModelUnavailable as error:
        raise GenerationUnavailable(str(error)) from error
    total = sum(round(float(row["total"]) * 100) for row in completed)
    text = generate_summary(total, len(completed), prediction)
    return {
        "text": text,
        "prediction_reason": prediction,
        "source": "model",
    }

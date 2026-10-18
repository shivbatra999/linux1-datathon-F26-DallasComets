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
    bundle = load_model()
    item_ids = [int(item_id) for item_id in bundle["item_ids"]]
    if not menu_rows:
        raise GenerationUnavailable("No menu data is available for prediction.")

    # The main-branch schema predates model_item_id. Keep the mapping local to
    # this request and use the model's persisted feature order, never a client
    # supplied identifier.
    ordered = sorted(menu_rows, key=lambda row: (row["name"], row["id"]))
    model_by_database_id = {
        row["id"]: item_ids[index]
        for index, row in enumerate(ordered)
        if index < len(item_ids)
    }
    features = [
        {
            "id": model_by_database_id[row["id"]],
            "category": "Lunch",
            "available": bool(row["is_available"]),
        }
        for row in ordered
        if row["id"] in model_by_database_id
    ]
    scoped_history = [
        [model_by_database_id[item_id] for item_id in order if item_id in model_by_database_id]
        for order in history
    ]
    scoped_history = [order for order in scoped_history if order]
    selected = Counter(item for order in scoped_history for item in order).most_common(1)
    selected_id = selected[0][0] if selected else features[0]["id"]
    picks = recommend(features, scoped_history, selected_id, [])
    menu_by_database_id = {row["id"]: row for row in ordered}
    names = {
        model_id: menu_by_database_id[database_id]["name"]
        for database_id, model_id in model_by_database_id.items()
    }
    friendly = []
    for pick in picks:
        name = names.get(pick["item_id"], "a menu item")
        reason = pick.get("reason", "")
        if reason.startswith("Popular choice:"):
            reason = f"{name} is a popular choice based on the completed order history."
        elif reason.startswith("Appeared together"):
            reason = f"{name} is often chosen alongside another menu favorite."
        elif reason == "Random suggestion.":
            reason = f"Consider testing {name} as another menu option."
        friendly.append({
            "item_id": pick["item_id"],
            "reason": reason,
            "source": pick["source"],
        })
    return friendly


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
        .select("id,name,is_available")
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

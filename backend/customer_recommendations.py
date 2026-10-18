"""Customer recommendations using explicit model mappings and scoped history."""
from collections import Counter

from .predictive import load_model, recommend


def customer_picks(menu_rows, history, selected_id, cart_ids):
    available = {
        row["id"]: row for row in menu_rows
        if row["is_available"]
    }
    excluded = set(cart_ids) | {selected_id}

    if selected_id not in available:
        raise ValueError("Selected menu item is unavailable.")
    if any(item_id not in available for item_id in cart_ids):
        raise ValueError("Cart contains unavailable menu items.")

    bundle = load_model()
    trained_ids = set(bundle["item_ids"])
    mapping = {
        row["id"]: row["model_item_id"]
        for row in available.values()
        if row.get("model_item_id") in trained_ids
    }
    if len(set(mapping.values())) != len(mapping):
        raise ValueError("Menu model mapping is ambiguous.")

    # An unmapped selection has no trained meaning. Use measured history only.
    if selected_id not in mapping:
        counts = Counter(
            item_id
            for order in history
            for item_id in set(order)
            if item_id in available and item_id not in excluded
        )
        return [
            {
                "item_id": item_id,
                "source": "fallback",
                "reason": (
                    f"Ordered in {count} of your {len(history)} "
                    "completed orders from this business."
                ),
            }
            for item_id, count in counts.most_common(2)
        ]

    categories = {
        1: "Lunch", 2: "Lunch", 3: "Lunch",
        4: "Breakfast", 5: "Drinks", 6: "Desserts",
    }
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

    picks = recommend(
        features,
        scoped_history,
        mapping[selected_id],
        [mapping[item_id] for item_id in cart_ids if item_id in mapping],
    )
    database_ids = {
        model_id: database_id
        for database_id, model_id in mapping.items()
    }

    return [
        {
            "item_id": database_ids[pick["item_id"]],
            "source": pick["source"],
            "reason": (
                "Based on your completed orders from this business: "
                + pick["reason"]
                if pick["source"] != "random"
                else "Explore another available item; no supporting order evidence."
            ),
        }
        for pick in picks
        if pick["item_id"] in database_ids
        and database_ids[pick["item_id"]] not in excluded
    ]

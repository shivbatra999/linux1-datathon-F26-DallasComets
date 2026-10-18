"""Pairing recommender shared by customer suggestions and the owner summary.

The trained BernoulliNB (model/recommender.joblib, from evaluation/train_recommender.py)
only ranks candidates. Every reason is a count measured in the scoped order history the
caller passes in, never a model probability. Only when no measured evidence is left
does it fill the remaining slots with random items, labeled source='random'.
"""
import random
from collections import Counter
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np

MODEL_PATH = Path(__file__).resolve().parent / 'model' / 'recommender.joblib'
MAX_PICKS = 2
MIN_TOGETHER = 3  # fewer shared orders than this is too sparse to call a pairing


class ModelUnavailable(RuntimeError):
    pass


@lru_cache(maxsize=1)
def load_model() -> dict:
    """Return {'model', 'item_ids'}; loaded once per process."""
    try:
        return joblib.load(MODEL_PATH)
    except OSError as e:
        raise ModelUnavailable('Recommendation model is not installed.') from e


def _fill(picks, ranked, menu, avoid_categories, make):
    """Append make(item) picks in ranked order: unused categories first, then any."""
    for strict in (True, False):
        for item in ranked:
            if len(picks) == MAX_PICKS:
                return
            taken = avoid_categories | {menu[p['item_id']]['category'] for p in picks}
            if any(p['item_id'] == item for p in picks) or (strict and menu[item]['category'] in taken):
                continue
            pick = make(item)
            if pick:
                picks.append(pick)


def recommend(menu_features, scoped_order_history, selected_item_id, cart_item_ids) -> list[dict]:
    """Return at most two {item_id, reason, source} suggestions.

    menu_features: [{id, category, available}] for the scoped business only.
    scoped_order_history: one collection of menu item IDs per past order, no customer data.
    """
    bundle = load_model()
    model, item_ids = bundle['model'], bundle['item_ids']
    menu = {m['id']: m for m in menu_features if m['available']}
    chosen = set(cart_item_ids) | {selected_item_id}
    orders = [set(o) for o in scoped_order_history]
    with_selected = [o for o in orders if selected_item_id in o]
    sold = Counter(i for o in orders for i in o)

    cart = np.array([[int(i in chosen) for i in item_ids]])
    score = dict(zip((int(c) for c in model.classes_), model.predict_proba(cart)[0]))
    candidates = sorted((i for i in menu if i not in chosen), key=lambda i: (-score.get(i, 0.0), i))
    cart_categories = {menu[i]['category'] for i in chosen if i in menu}

    def paired(item):
        together = sum(item in o for o in with_selected)
        if together >= MIN_TOGETHER:
            return {'item_id': item, 'source': 'model',
                    'reason': f'Appeared together in {together} of {len(with_selected)} qualifying orders.'}

    def popular(item):
        if sold[item]:
            return {'item_id': item, 'source': 'fallback',
                    'reason': f'Popular choice: ordered in {sold[item]} of {len(orders)} past orders.'}

    picks = []
    _fill(picks, candidates, menu, cart_categories, paired)
    _fill(picks, sorted(candidates, key=lambda i: (-sold[i], i)), menu, cart_categories, popular)
    # No measured evidence left (empty history, or everything already chosen): random items.
    pool = [i for i in (candidates or list(menu)) if all(p['item_id'] != i for p in picks)]
    for item in random.sample(pool, min(MAX_PICKS - len(picks), len(pool))):
        picks.append({'item_id': item, 'source': 'random', 'reason': 'Random suggestion.'})
    return picks

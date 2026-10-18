"""Build a separate synthetic training database (data/synthetic.db) and export CSVs.

Usage: python evaluation/seed_synthetic.py [--db PATH] [--orders N] [--menu N] [--reset]

This never touches the app database (SIMPLECATER_DB). The six website cards (MENU) are
extended with random menu items composed from MENU_PARTS, plus synthetic customers and orders
(orders.is_synthetic = 1). Baskets mix noise (RANDOM_PICK) with the planted signal: a
narrow random item popularity plus the COMBO_BOOST and CATEGORY_BOOST tables, so a model
trained on this data can at best rediscover those. State that next to any reported evaluation.
"""
import argparse
import csv
import datetime as dt
import math
import os
import random
import sqlite3
from pathlib import Path

from faker import Faker

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / 'backend' / 'schema.sql'
HISTORY_END = dt.date(2026, 10, 16)
HISTORY_DAYS = 365

# Mirrors frontend/fixtures.js so the training data uses the same cards as the website.
# (id, name, description, price_cents, category, tag, serves, img)
MENU = [
    (1, 'Mediterranean bowls', 'Roasted vegetables, hummus & herbed grains.', 1600, 'Lunch', 'Crowd favorite', 1, 'photo-1512621776951-a57141f2eefd'),
    (2, 'Artisan sandwich box', 'Freshly baked bread, seasonal fillings & chips.', 1400, 'Lunch', 'Serves 1', 1, 'photo-1528735602780-2552fd46c7af'),
    (3, 'Garden harvest salad', 'Crisp greens, avocado & house vinaigrette.', 1200, 'Lunch', 'Plant based', 1, 'photo-1511690743698-d9d85f2fbf38'),
    (4, 'Morning pastry box', 'Buttery croissants & a little something sweet.', 2800, 'Breakfast', 'Serves 6', 6, 'photo-1555507036-ab1f4038808a'),
    (5, 'Fresh iced tea pitcher', 'House-brewed black tea with fresh lemon.', 1200, 'Drinks', 'Serves 6', 6, 'photo-1556679343-c7306c1976bc'),
    (6, 'Chocolate brownie box', 'Rich chocolate brownies, baked in small batches.', 2400, 'Desserts', 'Serves 6', 6, 'photo-1606313564200-e75d5e30476c'),
]

# Random extra dishes are "<flavour> <format>". Formats: (name, serves, min_cents, max_cents).
MENU_PARTS = {
    'Lunch': (['Grilled chicken', 'Roasted tofu', 'Lemon salmon', 'Smoky beef', 'Falafel', 'Paneer tikka', 'Turkey pesto', 'Garlic shrimp'],
              [('bowls', 1, 1200, 1900), ('wrap box', 1, 1100, 1600), ('pasta tray', 10, 7000, 12000), ('taco bar', 10, 8000, 13000)]),
    'Breakfast': (['Classic', 'Seasonal', 'Mini', 'Assorted'],
                  [('bagel box', 8, 2400, 3600), ('muffin box', 6, 2000, 3000), ('breakfast burrito tray', 8, 4000, 6000), ('yogurt parfait cups', 6, 2200, 3200)]),
    'Drinks': (['Cold brew', 'Lemonade', 'Hot coffee', 'Hibiscus tea', 'Orange juice', 'Sparkling water'],
               [('pitcher', 6, 1000, 1800), ('carafe', 10, 1800, 3000)]),
    'Desserts': (['Salted caramel', 'Double chocolate', 'Berry', 'Lemon', 'Cinnamon'],
                 [('cookie tray', 12, 2000, 3200), ('bar box', 6, 2200, 3000), ('mini tart box', 6, 2600, 3800)]),
    'Sides': (['Herbed', 'Crispy', 'Seasonal', 'Garlic'],
              [('potato wedges', 8, 1600, 2600), ('roasted vegetables', 8, 1800, 2800), ('pasta salad', 8, 1600, 2400)]),
}
# Placeholder photos reused per category; replace before showing generated items publicly.
PHOTOS = {
    'Lunch': ['photo-1512621776951-a57141f2eefd', 'photo-1528735602780-2552fd46c7af'],
    'Breakfast': ['photo-1555507036-ab1f4038808a'],
    'Drinks': ['photo-1556679343-c7306c1976bc'],
    'Desserts': ['photo-1606313564200-e75d5e30476c'],
    'Sides': ['photo-1511690743698-d9d85f2fbf38'],
}
SINGLE_TAGS = ['Serves 1', 'Crowd favorite', 'Chef pick', 'New']

BASKET_SIZES = {1: 25, 2: 35, 3: 22, 4: 12, 5: 6}  # relative weights
POPULARITY_RANGE = (0.8, 1.25)  # per-item base weight; narrow so no category wins by luck
RANDOM_PICK = 0.25  # chance an added item ignores every boost (pure noise)
# Planted combos: once the key item is in a basket, each listed partner's pick weight is
# multiplied by the boost. CATEGORY_BOOST does the same per category pair, and covers
# every category as a partner so none is starved.
COMBO_BOOST = {
    4: {5: 4.0},          # pastry box -> iced tea
    2: {6: 3.0},          # sandwich box -> brownies
    1: {3: 3.0},          # bowls -> salad
    3: {5: 2.5},          # salad -> iced tea
}
CATEGORY_BOOST = {
    ('Breakfast', 'Drinks'): 2.5,
    ('Breakfast', 'Breakfast'): 2.0,
    ('Drinks', 'Breakfast'): 2.0,
    ('Lunch', 'Sides'): 2.5,
    ('Sides', 'Lunch'): 1.5,
    ('Lunch', 'Desserts'): 1.8,
    ('Lunch', 'Drinks'): 1.8,
    ('Desserts', 'Drinks'): 1.5,
}
# CSV exports. Sessions and password/profile columns are never exported.
EXPORTS = {
    'businesses': 'SELECT * FROM businesses',
    'users': 'SELECT id, username, role, business_id, created_at FROM users',
    'menu_items': 'SELECT * FROM menu_items',
    'orders': 'SELECT * FROM orders',
    'order_items': 'SELECT * FROM order_items',
    'ml_order_lines': 'SELECT * FROM ml_order_lines',
}


def random_menu(rng, count, first_id):
    """Return `count` extra (id, name, desc, price, category, tag, serves, img, available) rows."""
    options = [(cat, f'{flavour} {fmt}', serves, lo, hi)
               for cat, (flavours, formats) in MENU_PARTS.items()
               for flavour in flavours for fmt, serves, lo, hi in formats]
    if count > len(options):
        raise SystemExit(f'--menu can be at most {len(options)}.')
    rows = []
    for item_id, (cat, name, serves, lo, hi) in enumerate(rng.sample(options, count), start=first_id):
        tag = f'Serves {serves}' if serves > 1 else rng.choice(SINGLE_TAGS)
        rows.append((item_id, name, f'{cat} catering, serves {serves}.', rng.randrange(lo, hi + 1, 50),
                     cat, tag, serves, rng.choice(PHOTOS[cat]), int(rng.random() < 0.9)))
    return rows


def basket(rng, category, popularity):
    """Return (headcount, item IDs) for one synthetic catering order."""
    headcount = rng.randint(6, 40)
    size = rng.choices(list(BASKET_SIZES), weights=list(BASKET_SIZES.values()))[0]
    items = []
    while len(items) < size:
        candidates = [c for c in popularity if c not in items]
        if items and rng.random() < RANDOM_PICK:
            items.append(rng.choice(candidates))
            continue
        weights = [popularity[c] * math.prod(COMBO_BOOST.get(i, {}).get(c, 1.0)
                                             * CATEGORY_BOOST.get((category[i], category[c]), 1.0) for i in items)
                   for c in candidates]
        items.append(rng.choices(candidates, weights=weights)[0])
    return headcount, set(items)


def quantity(serves, headcount, mains):
    if serves == 1:
        return max(1, round(headcount / mains))
    return math.ceil(headcount / serves)


def export_csv(db, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, sql in EXPORTS.items():
        cur = db.execute(sql)
        with open(out_dir / f'{name}.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(col[0] for col in cur.description)
            writer.writerows(cur)


def main():
    ap = argparse.ArgumentParser(description='Build the synthetic training database and CSVs.')
    ap.add_argument('--db', default=str(ROOT / 'data' / 'synthetic.db'))
    ap.add_argument('--csv-dir', default=str(ROOT / 'data' / 'csv'))
    ap.add_argument('--orders', type=int, default=5000)
    ap.add_argument('--customers', type=int, default=250)
    ap.add_argument('--menu', type=int, default=50, help='random menu items added after the six website cards')
    ap.add_argument('--seed', type=int, default=26)
    ap.add_argument('--reset', action='store_true', help='delete the database file first')
    args = ap.parse_args()

    path = Path(args.db).resolve()
    app_db = os.environ.get('SIMPLECATER_DB')
    if app_db and Path(app_db).resolve() == path:
        raise SystemExit('Refusing to write synthetic data into the app database (SIMPLECATER_DB).')
    if args.reset:
        path.unlink(missing_ok=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    fake = Faker()
    fake.seed_instance(args.seed)
    db = sqlite3.connect(path)
    db.executescript(SCHEMA.read_text())
    db.execute('PRAGMA foreign_keys = ON')
    if db.execute('SELECT 1 FROM menu_items LIMIT 1').fetchone():
        raise SystemExit(f'{path} already has data; pass --reset to rebuild it.')

    menu = [m + (1,) for m in MENU] + random_menu(rng, args.menu, len(MENU) + 1)
    prices = {m[0]: m[3] for m in menu}
    category = {m[0]: m[4] for m in menu}
    serves = {m[0]: m[6] for m in menu}
    popularity = {m[0]: rng.uniform(*POPULARITY_RANGE) for m in menu}
    with db:
        db.execute('INSERT INTO businesses (id, name) VALUES (1, ?)', ('SimpleCater Demo Kitchen',))
        db.executemany('INSERT INTO menu_items (id, business_id, name, description, price_cents, category, tag, serves, img, available) '
                       'VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?, ?)', menu)
        db.executemany("INSERT INTO users (username, role) VALUES (?, 'customer')",
                       [(fake.unique.user_name(),) for _ in range(args.customers)])
        customer_ids = [r[0] for r in db.execute("SELECT id FROM users WHERE role = 'customer'")]
        for _ in range(args.orders):
            headcount, items = basket(rng, category, popularity)
            mains = sum(serves[i] == 1 for i in items) or 1
            lines = [(i, quantity(serves[i], headcount, mains)) for i in sorted(items)]
            pickup = fake.date_between(HISTORY_END - dt.timedelta(days=HISTORY_DAYS - 1), HISTORY_END)
            cur = db.execute('INSERT INTO orders (business_id, customer_id, pickup_date, status, total_cents, is_synthetic) '
                             "VALUES (1, ?, ?, 'Completed', ?, 1)",
                             (rng.choice(customer_ids), pickup.isoformat(), sum(prices[i] * q for i, q in lines)))
            db.executemany('INSERT INTO order_items (order_id, business_id, menu_item_id, quantity, unit_price_cents) '
                           'VALUES (?, 1, ?, ?, ?)', [(cur.lastrowid, i, q, prices[i]) for i, q in lines])
    export_csv(db, Path(args.csv_dir))
    counts = {t: db.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
              for t in ('businesses', 'users', 'menu_items', 'orders', 'order_items')}
    db.close()
    print(f'Seeded {path}: {counts}')
    print(f'CSV files written to {args.csv_dir}')


if __name__ == '__main__':
    main()

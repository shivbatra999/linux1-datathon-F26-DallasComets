"""10-fold cross-validation of the catering pairing recommender: BernoulliNB + Laplace smoothing.

Usage: python evaluation/train_recommender.py [--alpha 1.0 [2.0 ...]] [--folds 10]

Reads data/csv/ml_order_lines.csv and data/csv/menu_items.csv, which are synthetic
(evaluation/seed_synthetic.py), so these results only show the model recovering the
planted combos. Each order with >= 2 distinct items yields one example per item: that
item is the target and the order's other items are the binary features (the "cart").
Folds split by whole order (GroupKFold), so no order is in both training and test data.
Written for scikit-learn 1.4.1 (the Ubuntu 24.04 s390x package used on LinuxONE).
Like the API, ranking excludes items already in the cart.
Writes metrics.json and confusion-matrix plots to evaluation/results/, then fits the
final model on all examples and saves it to backend/model/recommender.joblib.
"""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix
from sklearn.model_selection import GroupKFold
from sklearn.naive_bayes import BernoulliNB

ROOT = Path(__file__).resolve().parent.parent
TOP_K = 2
SEED = 26


def load(csv_dir):
    with open(csv_dir / 'menu_items.csv', newline='', encoding='utf-8') as f:
        menu = {int(r['id']): r for r in csv.DictReader(f)}
    orders = defaultdict(set)
    with open(csv_dir / 'ml_order_lines.csv', newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            orders[int(r['order_id'])].add(int(r['menu_item_id']))
    return menu, orders


def examples(item_ids, orders):
    """Hold out each item of each multi-item order; the rest of the order is the cart."""
    col = {item: i for i, item in enumerate(item_ids)}
    X, y, groups = [], [], []
    for order_id, items in orders.items():
        if len(items) < 2:
            continue
        for target in items:
            row = np.zeros(len(item_ids), dtype=np.int8)
            row[[col[i] for i in items - {target}]] = 1
            X.append(row)
            y.append(target)
            groups.append(order_id)
    return np.array(X), np.array(y), np.array(groups)


def top_k(scores, X, item_ids, k=TOP_K):
    """Item IDs of the k best scores per row, never recommending a cart item."""
    scores = np.where(X == 1, -np.inf, scores)
    return np.asarray(item_ids)[np.argsort(-scores, axis=1, kind='stable')[:, :k]]


def nb_scores(model, X, item_ids):
    """predict_proba mapped onto every menu column (items never seen as targets score 0)."""
    full = np.zeros((len(X), len(item_ids)))
    col = {item: i for i, item in enumerate(item_ids)}
    full[:, [col[c] for c in model.classes_]] = model.predict_proba(X)
    return full


def shuffled_groups(groups, seed=SEED):
    """Relabel orders randomly so GroupKFold folds are shuffled (its shuffle= needs sklearn >= 1.6)."""
    _, inverse = np.unique(groups, return_inverse=True)
    return np.random.default_rng(seed).permutation(inverse.max() + 1)[inverse]


def cross_validate(X, y, groups, item_ids, alpha, folds):
    per_fold = defaultdict(list)
    oof_pred = np.empty_like(y)
    for train, test in GroupKFold(n_splits=folds).split(X, y, shuffled_groups(groups)):
        model = BernoulliNB(alpha=alpha).fit(X[train], y[train])
        counts = np.array([(y[train] == item).sum() for item in item_ids], dtype=float)
        nb = top_k(nb_scores(model, X[test], item_ids), X[test], item_ids)
        pop = top_k(np.tile(counts, (len(test), 1)), X[test], item_ids)
        truth = y[test]
        oof_pred[test] = nb[:, 0]
        available = len(item_ids) - X[test].sum(axis=1)
        per_fold['nb_top1'].append(float((nb[:, 0] == truth).mean()))
        per_fold['nb_hit_at_2'].append(float((nb == truth[:, None]).any(axis=1).mean()))
        per_fold['popularity_top1'].append(float((pop[:, 0] == truth).mean()))
        per_fold['popularity_hit_at_2'].append(float((pop == truth[:, None]).any(axis=1).mean()))
        per_fold['random_hit_at_2'].append(float((np.minimum(TOP_K, available) / available).mean()))
    return per_fold, oof_pred


def plot_confusion(y_true, y_pred, labels, display_labels, title, path, values):
    cm = confusion_matrix(y_true, y_pred, labels=labels, normalize='true')
    size = max(6, len(labels) * 0.25)
    fig, ax = plt.subplots(figsize=(size + 2, size))
    ConfusionMatrixDisplay(cm, display_labels=display_labels).plot(
        ax=ax, include_values=values, values_format='.2f', cmap='Blues', colorbar=True, xticks_rotation=90)
    ax.set_title(title)
    ax.set_xlabel('Predicted top-1 item' if len(labels) > 10 else 'Predicted category')
    ax.set_ylabel('Held-out item' if len(labels) > 10 else 'Held-out category')
    if len(labels) > 10:
        ax.tick_params(labelsize=6)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def save_model(X, y, item_ids, alpha, path):
    """Fit on every example and save the model with its feature column order."""
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({'model': BernoulliNB(alpha=alpha).fit(X, y), 'item_ids': [int(i) for i in item_ids]}, path)
    return path


def main():
    ap = argparse.ArgumentParser(description='Cross-validate the BernoulliNB pairing recommender.')
    ap.add_argument('--csv-dir', default=str(ROOT / 'data' / 'csv'))
    ap.add_argument('--out', default=str(ROOT / 'evaluation' / 'results'))
    ap.add_argument('--model', default=str(ROOT / 'backend' / 'model' / 'recommender.joblib'))
    ap.add_argument('--alpha', type=float, nargs='+', default=[1.0], help='1.0 is Laplace smoothing')
    ap.add_argument('--folds', type=int, default=10)
    args = ap.parse_args()

    menu, orders = load(Path(args.csv_dir))
    item_ids = sorted(menu)
    X, y, groups = examples(item_ids, orders)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    print(f'{len(orders)} orders, {len(set(groups))} with 2+ items -> {len(y)} held-out examples, '
          f'{len(item_ids)} items, {args.folds}-fold GroupKFold by order\n')

    results, best = {}, None
    for alpha in args.alpha:
        per_fold, oof_pred = cross_validate(X, y, groups, item_ids, alpha, args.folds)
        summary = {name: {'mean': float(np.mean(v)), 'std': float(np.std(v)), 'folds': v}
                   for name, v in per_fold.items()}
        results[str(alpha)] = summary
        print(f'alpha={alpha}')
        for name, s in summary.items():
            print(f'  {name:<22} {s["mean"]:.3f} +/- {s["std"]:.3f}')
        if best is None or summary['nb_hit_at_2']['mean'] > results[str(best[0])]['nb_hit_at_2']['mean']:
            best = (alpha, oof_pred)

    alpha, oof_pred = best
    plot_confusion(y, oof_pred, item_ids, item_ids,
                   f'BernoulliNB (alpha={alpha}) out-of-fold top-1, row-normalized', out / 'confusion_items.png', values=False)
    categories = sorted({m['category'] for m in menu.values()})
    to_cat = np.vectorize(lambda i: menu[i]['category'])
    plot_confusion(to_cat(y), to_cat(oof_pred), categories, categories,
                   f'BernoulliNB (alpha={alpha}) top-1 by category, row-normalized', out / 'confusion_categories.png', values=True)
    (out / 'metrics.json').write_text(json.dumps({
        'data': 'synthetic (evaluation/seed_synthetic.py)', 'folds': args.folds, 'split': 'GroupKFold by order_id',
        'examples': int(len(y)), 'orders_with_2plus_items': int(len(set(groups))), 'items': len(item_ids),
        'best_alpha_by_hit_at_2': alpha, 'results': results}, indent=2))
    print(f'\nPlots and metrics.json written to {out} (confusion matrices use alpha={alpha})')
    print(f'Final model (alpha={alpha}, all {len(y)} examples) saved to {save_model(X, y, item_ids, alpha, Path(args.model))}')


if __name__ == '__main__':
    main()

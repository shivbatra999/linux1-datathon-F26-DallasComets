# Secure AI verification record

Updated 2026-10-18. These results summarize checks performed by the team on LinuxONE and reported during integration. They are manual/integration evidence, not a newly executed automated regression suite or an independent security certification. Numerical examples are snapshots of changing demonstration data.

## Results

| Check | Reported result | Scope |
|---|---|---|
| Login, me, logout, repeated logout | Passed | Session cookie lifecycle; post-logout browser session returned 401 |
| Customer/owner page and AI restrictions | Passed | Wrong-role requests returned 403 |
| Customer profile/order RLS | Passed | Unfiltered own rows only; explicit known-other-customer queries returned no records |
| Customer order-item RLS | Passed | Visible lines belonged to visible own orders; known foreign order lines hidden |
| Owner business/order-item RLS | Passed | Store 1 owner saw only Store 1 orders and lines; Store 2 orders hidden |
| Encryption | Passed | Round-trip, tamper rejection, wrong-user AAD rejection, fresh ciphertext |
| Persistence | Passed | API/browser saves and decryption after process/container restart |
| Checkout | Passed | Database totals and atomic saves; client-supplied total/unit_price rejected |
| Predictive runtime | Passed | Saved estimator loaded and predict_proba ran using pinned packages in s390x container |
| Stable mapping | Passed | Six explicit mappings, correct output UUIDs/names; rename/reorder did not change IDs; duplicate mapping rejected |
| Customer recommendations | Passed | API 200, invalid item 400, extra customer_id 422, available/cart exclusions, browser flow |
| Owner summary | Passed | Real Granite inference and separately checked database count/value |
| Granite request boundary | Passed | Allowed-column test; intercepted request excluded account email, token, UUIDs, and prediction ID fields |
| Tool interface | Passed | No tools/functions supplied in intercepted model request |
| Network binding | Passed | App port 8000 and Granite port 8080 bound to loopback; Granite became healthy after reload |

Owner isolation was tested in the Store 1 → Store 2 direction. Store 2 had an existing order with nine lines, so the negative query was against real records. No Store 2 owner account was available in the audited profile list; reverse owner isolation is not claimed.

## Important distinctions

The initial outbound prompt test failed after mappings began returning menu UUIDs. `_summary_prompt` was changed to project each prediction to reason/source only. The repeated interception passed. A separate earlier test verified that summary preparation queried only approved business columns; interception did not run real Granite inference.

Completed-order snapshots progressed from 4 orders/$225.00 to 7/$411.00. These are order values, not collected payments. The later prompt used six qualifying mapped-history baskets for recommendation evidence; that denominator need not equal the seven orders counted in the summary. Do not hard-code these numbers into a demo claim.

Live examples used `fallback` popularity suggestions. Controlled fictional baskets exercised `model`-ranked pairings. Loading an estimator, running it, or displaying an outer summary `source=model` does not prove the displayed recommendation was model-ranked.

The model evaluation JSON reports approximately 5.82% hit@2 versus 5.05% popularity and 3.72% random, on synthetic data with order-grouped folds. It is not real-user validation or the accuracy of every deployed fallback.

## AI boundary

Predictive functions receive authorized item features/baskets. Owner preparation reads completed order IDs/totals, available menu IDs/names/mappings, and matching order/menu IDs for lines. Granite receives count, total, and reason/source strings. Profile, session, key, address, and phone columns are outside that preparation path. Structural projection removes identifier fields; it is not a general-purpose PII scrubber for arbitrary text inside menu names/reasons.

The model is not given database credentials or executable application tools. Generated recommendations remain advice; numerical verification and instruction constraints do not guarantee factual correctness or safety against every malicious menu name/prompt injection.

## Still required

- Save repeatable current-auth regression tests; old SQLite role tests are obsolete.
- Add automated captured-prompt regression tests, cross-business recommendation inputs, and permission/write checks.
- Verify reverse owner isolation with a separate Store 2 owner if one is provisioned.
- Recheck production RLS/grants and export a complete schema/policy bootstrap.
- Record final deployed image/model revisions, package inventory, actual GitHub Actions result, and live LinuxONE demo evidence.
- Do not claim HTTPS deployment, Telum acceleration, zero data egress, general quantum-safe networking, or a complete penetration test.

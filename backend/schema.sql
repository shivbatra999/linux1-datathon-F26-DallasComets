-- SimpleCater SQLite schema: the six tables in ARCHITECTURE.md plus one model-input view.
-- Money is integer cents. Dates are ISO YYYY-MM-DD. Timestamps are Unix seconds.
-- Avoids unixepoch() so older SQLite builds on LinuxONE still accept it.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS businesses (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    created_at  INTEGER NOT NULL DEFAULT (CAST(strftime('%s', 'now') AS INTEGER))
);

CREATE TABLE IF NOT EXISTS users (
    id                      INTEGER PRIMARY KEY,
    username                TEXT NOT NULL UNIQUE,
    password_hash           TEXT,       -- Argon2id. NULL means the account cannot sign in (synthetic history customers).
    role                    TEXT NOT NULL CHECK (role IN ('customer', 'owner')),
    business_id             INTEGER REFERENCES businesses(id),
    profile_ciphertext      BLOB,       -- AES-256-GCM ciphertext || tag of {name,email,phone}
    profile_kem_ciphertext  BLOB,       -- ML-KEM-768 encapsulation
    profile_nonce           BLOB,
    profile_key_version     INTEGER,
    created_at              INTEGER NOT NULL DEFAULT (CAST(strftime('%s', 'now') AS INTEGER)),
    CHECK ((role = 'owner') = (business_id IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS sessions (
    token_hash  TEXT PRIMARY KEY,       -- SHA-256 hex of the opaque cookie token
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at  INTEGER NOT NULL,
    created_at  INTEGER NOT NULL DEFAULT (CAST(strftime('%s', 'now') AS INTEGER))
);
CREATE INDEX IF NOT EXISTS sessions_user ON sessions(user_id);

CREATE TABLE IF NOT EXISTS menu_items (
    id           INTEGER PRIMARY KEY,
    business_id  INTEGER NOT NULL REFERENCES businesses(id),
    name         TEXT NOT NULL,
    description  TEXT NOT NULL DEFAULT '',   -- API field `desc`
    price_cents  INTEGER NOT NULL CHECK (price_cents > 0),
    category     TEXT NOT NULL,
    tag          TEXT NOT NULL DEFAULT '',
    serves       INTEGER NOT NULL DEFAULT 1 CHECK (serves > 0),
    img          TEXT NOT NULL,              -- Unsplash photo ID
    available    INTEGER NOT NULL DEFAULT 1 CHECK (available IN (0, 1)),
    UNIQUE (id, business_id)
);

CREATE TABLE IF NOT EXISTS orders (
    id            INTEGER PRIMARY KEY,       -- displayed as 'SC-' || id
    business_id   INTEGER NOT NULL REFERENCES businesses(id),
    customer_id   INTEGER NOT NULL REFERENCES users(id),
    pickup_date   TEXT NOT NULL CHECK (pickup_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    status        TEXT NOT NULL DEFAULT 'Confirmed' CHECK (status IN ('Confirmed', 'Completed')),
    total_cents   INTEGER NOT NULL CHECK (total_cents >= 0),
    is_synthetic  INTEGER NOT NULL DEFAULT 0 CHECK (is_synthetic IN (0, 1)),
    created_at    INTEGER NOT NULL DEFAULT (CAST(strftime('%s', 'now') AS INTEGER)),
    UNIQUE (id, business_id)
);
CREATE INDEX IF NOT EXISTS orders_business ON orders(business_id, pickup_date);
CREATE INDEX IF NOT EXISTS orders_customer ON orders(customer_id);

-- business_id is repeated so the composite keys reject an item from another business.
CREATE TABLE IF NOT EXISTS order_items (
    order_id          INTEGER NOT NULL,
    business_id       INTEGER NOT NULL,
    menu_item_id      INTEGER NOT NULL,
    quantity          INTEGER NOT NULL CHECK (quantity > 0),
    unit_price_cents  INTEGER NOT NULL CHECK (unit_price_cents > 0),   -- price at order time
    PRIMARY KEY (order_id, menu_item_id),
    FOREIGN KEY (order_id, business_id) REFERENCES orders(id, business_id) ON DELETE CASCADE,
    FOREIGN KEY (menu_item_id, business_id) REFERENCES menu_items(id, business_id)
);
CREATE INDEX IF NOT EXISTS order_items_item ON order_items(menu_item_id);

-- The only order data the predictive model receives: no customer, profile or session columns.
CREATE VIEW IF NOT EXISTS ml_order_lines AS
SELECT o.business_id, o.id AS order_id, o.pickup_date, oi.menu_item_id, oi.quantity
FROM orders o
JOIN order_items oi ON oi.order_id = o.id AND oi.business_id = o.business_id;

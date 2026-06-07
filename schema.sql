-- =====================================================================
-- Product Verification System — database schema (PostgreSQL)
--
-- Running this script creates every table and index the application uses:
--
--     psql "$DATABASE_URL" -f schema.sql
--
-- The app also auto-creates these tables on startup, so this script is only
-- needed when provisioning a database up front (the PostgreSQL target). It
-- mirrors the ORM entities in src/models/db_entities/ and serves as the
-- human-readable source of truth for the schema.
--
-- IDs are application-generated UUID strings (VARCHAR(36)). The boolean-style
-- columns (is_active, expiry_is_valid) are stored as 'true'/'false' text flags
-- for cross-engine portability with the bundled SQLite mode.
-- =====================================================================


-- Users -----------------------------------------------------------------
CREATE TABLE users (
    id            VARCHAR(36)  PRIMARY KEY,
    username      VARCHAR(100) NOT NULL UNIQUE,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(20)  NOT NULL CHECK (role IN ('admin', 'operator', 'qa_manager')),
    full_name     VARCHAR(255),
    is_active     VARCHAR(5)   NOT NULL DEFAULT 'true',
    created_at    TIMESTAMP    NOT NULL DEFAULT now(),
    updated_at    TIMESTAMP    NOT NULL DEFAULT now()
);

CREATE INDEX idx_users_username   ON users (username);
CREATE INDEX idx_users_email      ON users (email);
CREATE INDEX idx_users_created_at ON users (created_at);


-- Upload jobs (CSV ingestion tracking) ----------------------------------
CREATE TABLE upload_jobs (
    id             VARCHAR(36)  PRIMARY KEY,
    filename       VARCHAR(255) NOT NULL,
    status         VARCHAR(50)  NOT NULL DEFAULT 'pending'
                       CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    total_rows     INTEGER      NOT NULL DEFAULT 0,
    processed_rows INTEGER      NOT NULL DEFAULT 0,
    failed_rows    INTEGER      NOT NULL DEFAULT 0,
    error_message  TEXT,
    uploaded_by    VARCHAR(36),
    created_at     TIMESTAMP    NOT NULL DEFAULT now(),
    updated_at     TIMESTAMP    NOT NULL DEFAULT now(),
    completed_at   TIMESTAMP
);

CREATE INDEX idx_upload_jobs_status     ON upload_jobs (status);
CREATE INDEX idx_upload_jobs_created_at ON upload_jobs (created_at);


-- Products (warehouse inventory) ----------------------------------------
CREATE TABLE products (
    id                 VARCHAR(36)  PRIMARY KEY,
    wid                VARCHAR(50)  NOT NULL UNIQUE,   -- Warehouse ID
    ean                VARCHAR(50)  NOT NULL,          -- European Article Number
    manufacturing_date TIMESTAMP    NOT NULL,
    expiry_date        TIMESTAMP    NOT NULL,
    batch_id           VARCHAR(100),
    quantity           INTEGER      NOT NULL DEFAULT 1,
    location           VARCHAR(255),
    upload_job_id      VARCHAR(36),                    -- source CSV job, if any
    created_at         TIMESTAMP    NOT NULL DEFAULT now(),
    updated_at         TIMESTAMP    NOT NULL DEFAULT now()
);

CREATE INDEX idx_products_wid           ON products (wid);
CREATE INDEX idx_products_ean           ON products (ean);
CREATE INDEX idx_products_expiry_date   ON products (expiry_date);
CREATE INDEX idx_products_batch_id      ON products (batch_id);
CREATE INDEX idx_products_upload_job_id ON products (upload_job_id);
CREATE INDEX idx_products_created_at    ON products (created_at);


-- Verification logs (on-floor verification events) ----------------------
CREATE TABLE verification_logs (
    id                  VARCHAR(36)  PRIMARY KEY,
    product_id          VARCHAR(36)  NOT NULL REFERENCES products (id),
    operator_id         VARCHAR(36)  NOT NULL REFERENCES users (id),
    image_path          VARCHAR(500),
    expiry_extracted    VARCHAR(50),               -- date read from the label (optional AI step)
    expiry_is_valid     VARCHAR(5),                -- 'true' / 'false'
    notes               TEXT,
    verification_status VARCHAR(50)  NOT NULL DEFAULT 'pending'
                            CHECK (verification_status IN ('pending', 'verified', 'failed')),
    created_at          TIMESTAMP    NOT NULL DEFAULT now(),
    updated_at          TIMESTAMP    NOT NULL DEFAULT now()
);

CREATE INDEX idx_verification_logs_product_id  ON verification_logs (product_id);
CREATE INDEX idx_verification_logs_operator_id ON verification_logs (operator_id);
CREATE INDEX idx_verification_logs_status      ON verification_logs (verification_status);
CREATE INDEX idx_verification_logs_created_at  ON verification_logs (created_at);

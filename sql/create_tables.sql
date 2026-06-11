-- Real Estate Financial Assistant Database Schema

CREATE TABLE IF NOT EXISTS properties (
    property_id     SERIAL PRIMARY KEY,
    address         VARCHAR(255) NOT NULL,
    metro_area      VARCHAR(100) NOT NULL,
    sq_footage      INTEGER NOT NULL,
    property_type   VARCHAR(50) NOT NULL  -- Industrial, Office, Retail, Multifamily
);

CREATE TABLE IF NOT EXISTS financials (
    financial_id    SERIAL PRIMARY KEY,
    property_id     INTEGER NOT NULL REFERENCES properties(property_id) ON DELETE CASCADE,
    fiscal_year     INTEGER NOT NULL,
    fiscal_quarter  TEXT,              -- NULL means annual; quarterly values: Q1, Q2, Q3, Q4
    revenue         NUMERIC(15, 2) NOT NULL,
    net_income      NUMERIC(15, 2) NOT NULL,
    expenses        NUMERIC(15, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS press_releases (
    release_id      SERIAL PRIMARY KEY,
    title           VARCHAR(500) NOT NULL,
    publish_date    DATE NOT NULL,
    category        VARCHAR(100),
    summary         TEXT,
    content         TEXT,
    source_url      VARCHAR(500)
);

CREATE INDEX IF NOT EXISTS idx_financials_property ON financials(property_id);
CREATE INDEX IF NOT EXISTS idx_properties_metro    ON properties(metro_area);
CREATE INDEX IF NOT EXISTS idx_properties_type     ON properties(property_type);
CREATE INDEX IF NOT EXISTS idx_releases_date       ON press_releases(publish_date DESC);

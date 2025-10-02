-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Airports table
CREATE TABLE IF NOT EXISTS airports (
    iata VARCHAR(3) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    city VARCHAR(255) NOT NULL,
    country VARCHAR(100) NOT NULL,
    timezone VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Carriers table
CREATE TABLE IF NOT EXISTS carriers (
    iata VARCHAR(2) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    alliance VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Offers table
CREATE TABLE IF NOT EXISTS offers (
    id VARCHAR(100) PRIMARY KEY,
    source VARCHAR(50) NOT NULL,
    offer_type VARCHAR(20) NOT NULL CHECK (offer_type IN ('cash', 'miles')),
    cabin VARCHAR(20) NOT NULL,

    -- Cash fields
    currency VARCHAR(3),
    price_cents BIGINT,

    -- Miles fields
    miles BIGINT,
    miles_program VARCHAR(50),
    taxes_cents BIGINT,

    -- Common fields
    baggage_included BOOLEAN DEFAULT false,
    segments JSONB NOT NULL,
    out_date DATE NOT NULL,
    ret_date DATE,

    -- Metadata
    origin VARCHAR(3) NOT NULL,
    destination VARCHAR(3) NOT NULL,
    total_duration_minutes INT,
    stops_count INT,
    fare_rules JSONB,
    ancillaries_available BOOLEAN DEFAULT false,

    -- Cache control
    hash VARCHAR(64) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,

    FOREIGN KEY (origin) REFERENCES airports(iata),
    FOREIGN KEY (destination) REFERENCES airports(iata)
);

CREATE INDEX idx_offers_route_date ON offers(origin, destination, out_date, ret_date);
CREATE INDEX idx_offers_expires ON offers(expires_at);
CREATE INDEX idx_offers_hash ON offers(hash);

-- Queries cache table
CREATE TABLE IF NOT EXISTS queries_cache (
    id SERIAL PRIMARY KEY,
    origin VARCHAR(3) NOT NULL,
    destination VARCHAR(3) NOT NULL,
    out_date DATE NOT NULL,
    ret_date DATE,
    pax_adults INT NOT NULL DEFAULT 1,
    pax_children INT DEFAULT 0,
    pax_infants INT DEFAULT 0,
    cabin VARCHAR(20) NOT NULL,
    filters JSONB,

    result_offer_ids TEXT[],
    last_refreshed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_query UNIQUE (origin, destination, out_date, ret_date, pax_adults, pax_children, pax_infants, cabin)
);

CREATE INDEX idx_queries_route ON queries_cache(origin, destination, out_date);

-- Bookings table
CREATE TABLE IF NOT EXISTS bookings (
    id SERIAL PRIMARY KEY,
    booking_reference VARCHAR(50) UNIQUE,
    offer_id VARCHAR(100) NOT NULL,
    pnr VARCHAR(20),
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'held', 'confirmed', 'cancelled', 'failed')),

    passenger_data JSONB NOT NULL,
    contact_email VARCHAR(255) NOT NULL,
    contact_phone VARCHAR(50),

    payment_method VARCHAR(50),
    payment_status VARCHAR(20),

    selected_seats JSONB,
    selected_baggage JSONB,

    deeplink_url TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (offer_id) REFERENCES offers(id)
);

CREATE INDEX idx_bookings_reference ON bookings(booking_reference);
CREATE INDEX idx_bookings_email ON bookings(contact_email);

-- Users table (for v1)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    auth_provider VARCHAR(50),
    auth_id VARCHAR(255),

    preferences JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Price alerts table (for v1)
CREATE TABLE IF NOT EXISTS price_alerts (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    origin VARCHAR(3) NOT NULL,
    destination VARCHAR(3) NOT NULL,
    out_date_start DATE NOT NULL,
    out_date_end DATE NOT NULL,
    ret_date_start DATE,
    ret_date_end DATE,

    max_price_cents BIGINT,
    max_miles BIGINT,

    active BOOLEAN DEFAULT true,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- FAQ/Policies embeddings (optional vector table)
CREATE TABLE IF NOT EXISTS knowledge_base (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    metadata JSONB,
    embedding vector(1536),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ON knowledge_base USING ivfflat (embedding vector_cosine_ops);

-- Audit log
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    trace_id VARCHAR(100),
    service VARCHAR(50) NOT NULL,
    action VARCHAR(100) NOT NULL,
    user_id INT,
    metadata JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_trace ON audit_log(trace_id);
CREATE INDEX idx_audit_service ON audit_log(service, created_at);

-- Sample data: Brazilian airports
INSERT INTO airports (iata, name, city, country, timezone) VALUES
('GRU', 'São Paulo/Guarulhos International Airport', 'São Paulo', 'Brazil', 'America/Sao_Paulo'),
('CGH', 'Congonhas Airport', 'São Paulo', 'Brazil', 'America/Sao_Paulo'),
('GIG', 'Rio de Janeiro/Galeão International Airport', 'Rio de Janeiro', 'Brazil', 'America/Sao_Paulo'),
('SDU', 'Santos Dumont Airport', 'Rio de Janeiro', 'Brazil', 'America/Sao_Paulo'),
('BSB', 'Brasília International Airport', 'Brasília', 'Brazil', 'America/Sao_Paulo'),
('REC', 'Recife/Guararapes International Airport', 'Recife', 'Brazil', 'America/Recife'),
('SSA', 'Salvador Deputado Luís Eduardo Magalhães International Airport', 'Salvador', 'Brazil', 'America/Bahia'),
('FOR', 'Fortaleza Pinto Martins International Airport', 'Fortaleza', 'Brazil', 'America/Fortaleza'),
('POA', 'Porto Alegre Salgado Filho International Airport', 'Porto Alegre', 'Brazil', 'America/Sao_Paulo'),
('CWB', 'Curitiba Afonso Pena International Airport', 'Curitiba', 'Brazil', 'America/Sao_Paulo'),
('MAO', 'Manaus Eduardo Gomes International Airport', 'Manaus', 'Brazil', 'America/Manaus'),
('BEL', 'Belém Val de Cans International Airport', 'Belém', 'Brazil', 'America/Belem')
ON CONFLICT (iata) DO NOTHING;

-- Sample data: Carriers
INSERT INTO carriers (iata, name, alliance) VALUES
('LA', 'LATAM Airlines', 'Oneworld'),
('G3', 'Gol Linhas Aéreas', NULL),
('AD', 'Azul Brazilian Airlines', NULL),
('JJ', 'LATAM Brasil', 'Oneworld'),
('AA', 'American Airlines', 'Oneworld'),
('UA', 'United Airlines', 'Star Alliance'),
('DL', 'Delta Air Lines', 'SkyTeam'),
('CM', 'Copa Airlines', 'Star Alliance'),
('AR', 'Aerolineas Argentinas', 'SkyTeam')
ON CONFLICT (iata) DO NOTHING;

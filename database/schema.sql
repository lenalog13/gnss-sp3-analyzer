CREATE TABLE experiments (
    id SERIAL PRIMARY KEY,
    name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- Файлы (SP3, CLK)
CREATE TABLE files (
    id SERIAL PRIMARY KEY,
    experiment_id INTEGER REFERENCES experiments(id),
    type TEXT, -- calc_sp3, ref_sp3, clk
    path TEXT
);

-- Данные по эпохам
CREATE TABLE epochs (
    id SERIAL PRIMARY KEY,
    experiment_id INTEGER REFERENCES experiments(id),

    epoch_time DOUBLE PRECISION,
    satellite TEXT,

    dx DOUBLE PRECISION,
    dy DOUBLE PRECISION,
    dz DOUBLE PRECISION,

    dr DOUBLE PRECISION,
    dt DOUBLE PRECISION,
    dn DOUBLE PRECISION,

    clock_error DOUBLE PRECISION
);

-- Итоговая статистика
CREATE TABLE statistics (
    id SERIAL PRIMARY KEY,
    experiment_id INTEGER REFERENCES experiments(id),

    rms_x DOUBLE PRECISION,
    rms_y DOUBLE PRECISION,
    rms_z DOUBLE PRECISION,
    rms_3d DOUBLE PRECISION,

    rms_r DOUBLE PRECISION,
    rms_t DOUBLE PRECISION,
    rms_n DOUBLE PRECISION,

    mean_error DOUBLE PRECISION,
    max_error DOUBLE PRECISION,

    clock_rms DOUBLE PRECISION
);
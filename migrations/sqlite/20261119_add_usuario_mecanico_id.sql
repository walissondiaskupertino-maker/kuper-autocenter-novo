-- Apply once to an existing SQLite installation before deploying the matching code.
ALTER TABLE usuarios
    ADD COLUMN mecanico_id INTEGER
    REFERENCES mecanicos(id)
    ON DELETE SET NULL
    ON UPDATE CASCADE;

CREATE UNIQUE INDEX uq_usuarios_mecanico_id ON usuarios(mecanico_id);

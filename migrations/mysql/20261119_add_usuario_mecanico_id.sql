-- Apply once to an existing MySQL installation before deploying the matching code.
ALTER TABLE usuarios
    ADD COLUMN mecanico_id INT NULL,
    ADD CONSTRAINT fk_usuario_mecanico
        FOREIGN KEY (mecanico_id)
        REFERENCES mecanicos(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    ADD UNIQUE KEY uq_usuarios_mecanico_id (mecanico_id);

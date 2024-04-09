CREATE TABLE country_names
(
    id      TEXT NOT NULL
        CONSTRAINT country_names_pk
            PRIMARY KEY,
    code    TEXT NOT NULL,
    name    TEXT NOT NULL
);

CREATE TABLE country_facts
(
    id         TEXT NOT NULL
        CONSTRAINT country_facts_pk
            PRIMARY KEY,
    country_id TEXT NOT NULL
        CONSTRAINT country_facts_country_names_id_fk
            REFERENCES country_names
            ON DELETE SET NULL,
    tags       TEXT NOT NULL,
    content    TEXT NOT NULL
);

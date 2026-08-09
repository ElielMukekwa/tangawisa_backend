from sqlalchemy import Engine, inspect, text


def apply_local_schema_upgrades(engine: Engine) -> None:
    """Apply additive upgrades required by existing local SQLite databases."""
    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    upgrades = {
        "products": {
            "is_featured": "BOOLEAN NOT NULL DEFAULT 0",
            "is_new_arrival": "BOOLEAN NOT NULL DEFAULT 0",
        },
        "messages": {
            "reply_to_message_id": "VARCHAR(50)",
            "reply_to_preview": "TEXT",
        },
    }
    with engine.begin() as connection:
        for table_name, columns in upgrades.items():
            if table_name not in inspector.get_table_names():
                continue
            existing = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, definition in columns.items():
                if column_name not in existing:
                    connection.execute(
                        text(f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" {definition}')
                    )

        if "products" in inspector.get_table_names():
            connection.execute(
                text(
                    "UPDATE products SET is_featured = 1 "
                    "WHERE name IN ('Smartphone Nova X12', 'Robe Amani Classic', 'Tissage Heritage')"
                )
            )
            connection.execute(
                text(
                    "UPDATE products SET is_new_arrival = 1 "
                    "WHERE name IN ('Pack Jus Nature', 'Ensemble Beige Urbain', 'PowerBank River 20K')"
                )
            )

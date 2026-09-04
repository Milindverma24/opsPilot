"""
Database initializer for OpsPilot.
Creates all database tables and ensures schema synchronization for local SQLite / PostgreSQL.
"""
import sqlite3
from sqlalchemy import text, inspect
from apps.api.app.core.database import engine, Base
import apps.api.app.models  # Ensure all models are imported and registered with Base.metadata


def init_db():
    print("Creating all OpsPilot database tables...")
    Base.metadata.create_all(bind=engine)

    # Sync missing columns for SQLite local development
    try:
        with engine.connect() as conn:
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()

            for table_name, table in Base.metadata.tables.items():
                if table_name in existing_tables:
                    existing_cols = {col["name"] for col in inspector.get_columns(table_name)}
                    for col in table.columns:
                        if col.name not in existing_cols:
                            # Map SQLAlchemy type to SQLite column type
                            col_type = col.type.compile(engine.dialect)
                            alter_stmt = f'ALTER TABLE "{table_name}" ADD COLUMN "{col.name}" {col_type}'
                            try:
                                conn.execute(text(alter_stmt))
                                conn.commit()
                                print(f"  + Added column {table_name}.{col.name} ({col_type})")
                            except Exception as e:
                                pass
    except Exception as e:
        print(f"Warning during schema column check: {e}")

    print("Database tables initialized successfully!")


def drop_db():
    print("Dropping all OpsPilot database tables...")
    Base.metadata.drop_all(bind=engine)
    print("Database tables dropped successfully!")


if __name__ == "__main__":
    init_db()

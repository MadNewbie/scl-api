"""
Migration: create_tokens_table
Created: 2026-06-18 13:18:31.202010
"""

from sqlalchemy import text
from app.database import engine

description = "create_tokens_table"

def up():
    """Apply migration"""
    # TODO: Write your migration code here
    with engine.connect() as conn:
        # Example: conn.execute(text(
        #   "ALTER TABLE users ADD COLUMN new_column VARCHAR(100)"
        # ))
        conn.execute(text(
            """CREATE TABLE IF NOT EXISTS tokens (
                id SERIAL PRIMARY KEY,
                secret VARCHAR NOT NULL,
                user_id VARCHAR NOT NULL,
                token TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )"""
        ))
        conn.commit()

def down():
    """Rollback migration"""
    # TODO: Write rollback code here
    with engine.connect() as conn:
        # Example: conn.execute(text(
        #   "ALTER TABLE users DROP COLUMN new_column"
        # ))
        conn.commit()

from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy import text, inspect
from app.database import engine, Base
from datetime import datetime
import os
import importlib
import sys

env_path = Path(__file__).resolve().parent.parent / '.env'

load_dotenv(dotenv_path=env_path)

class MigrationManager:
    def __init__(self):
        self.versions_dir = "migrations/versions"
        self.migration_table = os.getenv("MIGRATION_TABLENAME")
        self._ensure_migration_table()

    def _ensure_migration_table(self):
        """Create migration history table if not exists"""
        with engine.connect() as conn:
            inspector = inspect(conn)
            if not inspector.has_table(self.migration_table):
                conn.execute(text(f"""
                    CREATE TABLE {self.migration_table} (
                        id SERIAL PRIMARY KEY,
                        version VARCHAR(50) NOT NULL UNIQUE,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        description TEXT
                    )
                """))
                conn.commit()

    def _get_applied_migrations(self):
        """Get list of already applied migrations"""
        with engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT version FROM {self.migration_table} ORDER BY id")
            )
            return [row[0] for row in result]
        
    def _get_available_migrations(self):
        """Get list of available migrations files"""
        migrations = []
        if not os.path.exists(self.versions_dir):
            return migrations
        
        for file in sorted(os.listdir(self.versions_dir)):
            if file.endswith(".py") and not file.startswith("__"):
                migrations.append(file[:-3]) # remove file ext
        return migrations

    def apply_migration(self, version):
        """Apply a specific migration"""
        try:
            # Import the migration module
            module_name = f"migrations.versions.{version}"
            module = importlib.import_module(module_name)

            # Check if migration has up() function
            if not hasattr(module, 'up'):
                print(f"Migration {version} doesn't have 'up' function")
                return False
            
            print(f"Applying migration: {version}")

            # Execute the migration
            module.up()

            # Record in History
            with engine.connect() as conn:
                conn.execute(
                    text(f"""
                        INSERT INTO {self.migration_table} (version, description)
                        VALUES (:version, :description)
                    """),
                    {
                        "version": version,
                        "description": getattr(module, 'description', '')
                    }
                )
                conn.commit()

            print(f"Migration {version} applied successfully")
            return True
        except Exception as e:
            print(f"Error applying migration {version}: {str(e)}")
            return False
    
    def rollback_migration(self, version):
        """Rollback a specific migration"""
        try:
            module_name = f"migrations.versions.{version}"
            module = importlib.import_module(module_name)

            if not hasattr(module,'down'):
                print(f"Migration {version} doesn't have 'down' function")
                return False
            
            print(f"Rolling back migration: {version}")
            module.down()

            with engine.connect() as conn:
                conn.execute(text(f"""
                    DELETE FROM {self.migration_table} WHERE version = :version
                """),{
                    "version": version
                })
                conn.commit()

        except Exception as e:
            print(f"Error rolling back migration {version}: {str(e)}")
            return False
    
    def migrate(self, target=None):
        """Apply all pending migrations or up to target"""
        applied = self._get_applied_migrations()
        available = self._get_available_migrations()

        pending = [v for v in available if v not in applied]

        if target:
            pending = [v for v in pending if v <= target]

        if not pending:
            print("No pending migrations")
            return
        
        print(f"Found {len(pending)} pending migration")

        for version in pending:
            if not self.apply_migration(version):
                return False
            
        print("All migrations applied successfully")
        return True
    
    def rollback(self, steps=1):
        """Rollback last N migrations"""
        applied = self._get_applied_migrations()

        if not applied:
            print("No migrations to rollback")
            return
        
        rollback_versions = applied[-steps:]

        for version in reversed(rollback_versions):
            self.rollback_migration(version)

        print(f"Rollback completed: {len(rollback_versions)} migrations")

    def status(self):
        """Show migration status"""
        applied = self._get_applied_migrations()
        available = self._get_available_migrations()

        print("\n Migration Status")
        print("-"*50)

        for version in available:
            status = " Applied" if version in applied else " Pending"
            print(f"{version}: {status}")

        print("-"*50)
        print(f"Total: {len(available)} | Applied: {len(applied)} | Pending: {len(available)-len(applied)}")
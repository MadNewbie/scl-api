import sys
import argparse
from migrations.migration_manager import MigrationManager

def main():
    parser = argparse.ArgumentParser(description="Alat Migrasi Basis Data")
    parser.add_argument(
        "command",
        choices=["up","down","status","create"],
        help="perintah migrasi yang bisa dijalankan"
    )
    parser.add_argument(
        "--target", "-t",
        help="Versi migrasi yang ditargetkan (utk perintah up)"
    )
    parser.add_argument(
        "--steps", "-s",
        type=int,
        default=1,
        help="Banyaknya migrasi yang ingin dirollback (utk perintah down)"
    )
    parser.add_argument(
        "--name", "-n",
        help="Nama migrasi (utk perintah create)"
    )

    args = parser.parse_args()
    manager = MigrationManager()

    if args.command == "up":
        manager.migrate(args.target)
    elif args.command == "down":
        manager.rollback(args.steps)
    elif args.command == "status":
        manager.status()
    elif args.command == "create":
        if not args.name:
            print("Tolong berikan nama pada migrasinya dengan argumen --name")
            return
        
        #Membuat file migrasi baru
        timestamp = __import__('datetime').datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"migrations/versions/{timestamp}_{args.name}.py"
        template = f'''"""
Migration: {args.name}
Created: {__import__('datetime').datetime.now()}
"""

from sqlalchemy import text
from app.database import engine

description = "{args.name}"

def up():
    """Apply migration"""
    # TODO: Write your migration code here
    with engine.connect() as conn:
        # Example: conn.execute(text(
        #   "ALTER TABLE users ADD COLUMN new_column VARCHAR(100)"
        # ))
        conn.commit()

def down():
    """Rollback migration"""
    # TODO: Write rollback code here
    with engine.connect() as conn:
        # Example: conn.execute(text(
        #   "ALTER TABLE users DROP COLUMN new_column"
        # ))
        conn.commit()
'''

        with open(filename, 'w') as f:
            f.write(template)

        print(f"File migrasi sudah terbentuk: {filename}")

if __name__ == "__main__":
    main()
"""
Database Migration Script
Safe creation and migration of PostgreSQL schema
"""

import os
import sys
from sqlalchemy import create_engine, text
import argparse


def create_database_if_not_exists(db_url: str):
    """Create database if it doesn't exist"""
    # Parse URL to get database name
    from urllib.parse import urlparse
    
    parsed = urlparse(db_url)
    db_name = parsed.path.lstrip('/')
    
    # Connect to postgres database to create new database
    base_url = f"{parsed.scheme}://{parsed.netloc}/postgres"
    
    try:
        engine = create_engine(base_url, isolation_level="AUTOCOMMIT")
        with engine.connect() as conn:
            # Check if database exists
            result = conn.execute(
                text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
            )
            exists = result.fetchone()
            
            if not exists:
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                print(f"✅ Created database: {db_name}")
            else:
                print(f"ℹ️ Database already exists: {db_name}")
        
        engine.dispose()
        return True
    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        return False


def run_migrations(db_url: str):
    """Run migrations to create tables"""
    try:
        from .models import create_tables
        
        engine = create_tables(db_url)
        print("✅ Tables created successfully")
        
        # Verify tables
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]
            print(f"📊 Tables present: {', '.join(tables)}")
        
        engine.dispose()
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


def verify_connection(db_url: str):
    """Verify database connection"""
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL: {version[:50]}...")
        engine.dispose()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Database migration tool")
    parser.add_argument(
        "--create",
        action="store_true",
        help="Create database and run migrations"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify database connection"
    )
    parser.add_argument(
        "--db-url",
        type=str,
        default=os.getenv("DATABASE_URL"),
        help="Database URL (default: from DATABASE_URL env var)"
    )
    
    args = parser.parse_args()
    
    if not args.db_url:
        print("❌ No DATABASE_URL provided")
        print("Set DATABASE_URL environment variable or use --db-url flag")
        sys.exit(1)
    
    print(f"📦 Database URL: {args.db_url.replace(args.db_url.split('@')[0].split(':')[-1], '***')}")
    
    if args.verify:
        if verify_connection(args.db_url):
            print("✅ Database is ready")
            sys.exit(0)
        else:
            sys.exit(1)
    
    if args.create:
        print("🔨 Creating database and running migrations...")
        
        # Step 1: Create database
        if not create_database_if_not_exists(args.db_url):
            sys.exit(1)
        
        # Step 2: Run migrations
        if not run_migrations(args.db_url):
            sys.exit(1)
        
        # Step 3: Verify
        if not verify_connection(args.db_url):
            sys.exit(1)
        
        print("✅ Migration complete!")
        sys.exit(0)
    
    parser.print_help()


if __name__ == "__main__":
    main()

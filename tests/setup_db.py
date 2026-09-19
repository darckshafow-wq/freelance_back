#!/usr/bin/env python3
"""
Setup script for PostgreSQL database and seed test data
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Connect to default postgres DB to create user and DB
def setup_database():
    """Create PostgreSQL user and database if they don't exist"""
    
    # Try to connect as postgres (system user)
    try:
        # Use peer authentication (local socket)
        engine = create_engine(
            "postgresql+psycopg2://postgres@/postgres",
            echo=False
        )
        
        with engine.connect() as conn:
            conn.execution_options(autocommit=True)
            
            # Create user
            try:
                conn.execute(text("CREATE USER admin WITH PASSWORD 'mohamed';"))
                print("✓ Created user: admin")
            except Exception as e:
                if "already exists" in str(e):
                    print("✓ User admin already exists")
                else:
                    print(f"⚠ User creation warning: {e}")
            
            # Create database
            try:
                conn.execute(text("CREATE DATABASE freelance_db OWNER admin;"))
                print("✓ Created database: freelance_db")
            except Exception as e:
                if "already exists" in str(e):
                    print("✓ Database freelance_db already exists")
                else:
                    print(f"⚠ Database creation warning: {e}")
            
            # Grant privileges
            try:
                conn.execute(text("GRANT ALL PRIVILEGES ON DATABASE freelance_db TO admin;"))
                print("✓ Granted privileges to admin")
            except Exception as e:
                print(f"⚠ Privilege grant: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to setup database: {e}")
        print("\nTrying alternative approach...")
        return False

if __name__ == "__main__":
    if setup_database():
        print("\n✅ Database setup complete!")
        sys.exit(0)
    else:
        print("\n⚠ Database setup partial - manual intervention may be needed")
        sys.exit(1)

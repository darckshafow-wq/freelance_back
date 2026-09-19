#!/bin/bash

# PostgreSQL Setup Script for Freelance Project
# This script configures PostgreSQL with admin user and freelance database

set -e

echo "🔧 PostgreSQL Configuration Script"
echo "===================================="
echo ""

# Variables
POSTGRES_HOST="localhost"
POSTGRES_PORT="5432"
POSTGRES_USER="admin"
POSTGRES_PASSWORD="mohamed"
POSTGRES_DB="freelance_db"
POSTGRES_ADMIN_USER="postgres"

echo "📝 Configuration Details:"
echo "   Host: $POSTGRES_HOST"
echo "   Port: $POSTGRES_PORT"
echo "   Admin User: $POSTGRES_USER"
echo "   Database: $POSTGRES_DB"
echo ""

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is not installed!"
    echo "   Install with: sudo apt-get install postgresql postgresql-contrib"
    exit 1
fi

echo "✓ PostgreSQL found"
echo ""

# Check if PostgreSQL service is running
if ! systemctl is-active --quiet postgresql; then
    echo "⚠️  PostgreSQL service is not running"
    echo "   Starting PostgreSQL..."
    sudo systemctl start postgresql || echo "⚠️  Could not start PostgreSQL automatically. Please run: sudo systemctl start postgresql"
fi

echo ""
echo "🔐 Creating user and database..."
echo ""

# Create SQL script
SETUP_SQL=$(cat <<EOF
-- Create admin role if not exists
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${POSTGRES_USER}') THEN
        CREATE ROLE ${POSTGRES_USER} WITH LOGIN PASSWORD '${POSTGRES_PASSWORD}' CREATEDB CREATEROLE;
        GRANT ALL PRIVILEGES ON DATABASE ${POSTGRES_DB} TO ${POSTGRES_USER};
        GRANT ALL ON SCHEMA public TO ${POSTGRES_USER};
        GRANT ALL ON ALL TABLES IN SCHEMA public TO ${POSTGRES_USER};
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ${POSTGRES_USER};
        RAISE NOTICE 'User ${POSTGRES_USER} created successfully';
    ELSE
        -- Update password
        ALTER ROLE ${POSTGRES_USER} WITH PASSWORD '${POSTGRES_PASSWORD}';
        RAISE NOTICE 'User ${POSTGRES_USER} password updated';
    END IF;
END
\$\$;

-- Create database if not exists
SELECT 'CREATE DATABASE ${POSTGRES_DB} OWNER ${POSTGRES_USER}'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${POSTGRES_DB}')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE ${POSTGRES_DB} TO ${POSTGRES_USER};
GRANT ALL ON SCHEMA public TO ${POSTGRES_USER};

-- Set default schema privileges
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ${POSTGRES_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ${POSTGRES_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO ${POSTGRES_USER};

SELECT 'Setup complete!';
EOF
)

# Execute SQL as postgres user
echo "$SETUP_SQL" | sudo -u postgres psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" || {
    echo "❌ Failed to configure PostgreSQL"
    echo "   Try running: sudo -u postgres psql -h localhost"
    exit 1
}

echo ""
echo "✅ PostgreSQL Configuration Complete!"
echo ""
echo "📊 Connection Details:"
echo "   Host:     $POSTGRES_HOST"
echo "   Port:     $POSTGRES_PORT"
echo "   Username: $POSTGRES_USER"
echo "   Password: $POSTGRES_PASSWORD"
echo "   Database: $POSTGRES_DB"
echo ""
echo "🧪 Test connection:"
echo "   psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c 'SELECT version();'"
echo ""
echo "✨ Setup script finished successfully!"

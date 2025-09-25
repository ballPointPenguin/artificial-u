#!/bin/bash

# PostgreSQL Restore Script for Dockerized Database
# Usage: ./restore_db.sh <backup_file>

set -e

CONTAINER_NAME="artificial_u_postgres"
DB_NAME="artificial_u_dev"
DB_USER="postgres"

if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_file>"
    echo ""
    echo "Examples:"
    echo "  $0 backups/backup_20250925_123456.sql"
    echo "  $0 backups/backup_20250925_123456.sql.gz"
    echo "  $0 backups/backup_20250925_123456.dump"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file '$BACKUP_FILE' not found"
    exit 1
fi

# Check if container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "Error: PostgreSQL container '$CONTAINER_NAME' is not running"
    echo "Start it with: docker-compose up -d postgres"
    exit 1
fi

echo "WARNING: This will replace all data in database '$DB_NAME'"
read -p "Are you sure? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled"
    exit 0
fi

# Determine backup type and restore accordingly
if [[ "$BACKUP_FILE" == *.sql.gz ]]; then
    echo "Restoring from compressed SQL backup..."
    # Drop and recreate database
    docker exec $CONTAINER_NAME psql -U $DB_USER -c "DROP DATABASE IF EXISTS $DB_NAME;"
    docker exec $CONTAINER_NAME psql -U $DB_USER -c "CREATE DATABASE $DB_NAME;"
    # Restore
    gunzip -c "$BACKUP_FILE" | docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME
    
elif [[ "$BACKUP_FILE" == *.dump ]]; then
    echo "Restoring from custom format backup..."
    # Drop and recreate database
    docker exec $CONTAINER_NAME psql -U $DB_USER -c "DROP DATABASE IF EXISTS $DB_NAME;"
    docker exec $CONTAINER_NAME psql -U $DB_USER -c "CREATE DATABASE $DB_NAME;"
    # Copy backup file to container and restore
    docker cp "$BACKUP_FILE" $CONTAINER_NAME:/tmp/restore.dump
    docker exec $CONTAINER_NAME pg_restore -U $DB_USER -d $DB_NAME -v /tmp/restore.dump
    docker exec $CONTAINER_NAME rm /tmp/restore.dump
    
elif [[ "$BACKUP_FILE" == *.sql ]]; then
    if [[ $(basename "$BACKUP_FILE") == backup_all_* ]]; then
        echo "Restoring all databases..."
        echo "WARNING: This will restore ALL databases, users, and permissions!"
        read -p "Continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Restore cancelled"
            exit 0
        fi
        cat "$BACKUP_FILE" | docker exec -i $CONTAINER_NAME psql -U $DB_USER
    else
        echo "Restoring from SQL backup..."
        # Drop and recreate database
        docker exec $CONTAINER_NAME psql -U $DB_USER -c "DROP DATABASE IF EXISTS $DB_NAME;"
        docker exec $CONTAINER_NAME psql -U $DB_USER -c "CREATE DATABASE $DB_NAME;"
        # Restore
        cat "$BACKUP_FILE" | docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME
    fi
else
    echo "Error: Unknown backup file format. Supported: .sql, .sql.gz, .dump"
    exit 1
fi

echo "Restore completed successfully!"

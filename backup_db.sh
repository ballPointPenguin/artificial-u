#!/bin/bash

# PostgreSQL Backup Script for Dockerized Database
# Usage: ./backup_db.sh [backup_type]
# Types: sql, compressed, custom, all

set -e

CONTAINER_NAME="artificial_u_postgres"
DB_NAME="artificial_u_dev"
DB_USER="postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Check if container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "Error: PostgreSQL container '$CONTAINER_NAME' is not running"
    echo "Start it with: docker-compose up -d postgres"
    exit 1
fi

BACKUP_TYPE=${1:-compressed}

case $BACKUP_TYPE in
    "sql")
        echo "Creating SQL backup..."
        BACKUP_FILE="$BACKUP_DIR/backup_${TIMESTAMP}.sql"
        docker exec $CONTAINER_NAME pg_dump -U $DB_USER -d $DB_NAME > "$BACKUP_FILE"
        echo "Backup created: $BACKUP_FILE"
        ;;
    
    "compressed")
        echo "Creating compressed backup..."
        BACKUP_FILE="$BACKUP_DIR/backup_${TIMESTAMP}.sql.gz"
        docker exec $CONTAINER_NAME pg_dump -U $DB_USER -d $DB_NAME | gzip > "$BACKUP_FILE"
        echo "Backup created: $BACKUP_FILE"
        ;;
    
    "custom")
        echo "Creating custom format backup..."
        BACKUP_FILE="$BACKUP_DIR/backup_${TIMESTAMP}.dump"
        docker exec $CONTAINER_NAME pg_dump -U $DB_USER -d $DB_NAME -Fc > "$BACKUP_FILE"
        echo "Backup created: $BACKUP_FILE"
        ;;
    
    "all")
        echo "Creating backup of all databases..."
        BACKUP_FILE="$BACKUP_DIR/backup_all_${TIMESTAMP}.sql"
        docker exec $CONTAINER_NAME pg_dumpall -U $DB_USER > "$BACKUP_FILE"
        echo "Backup created: $BACKUP_FILE"
        ;;
    
    *)
        echo "Usage: $0 [sql|compressed|custom|all]"
        echo ""
        echo "Backup types:"
        echo "  sql        - Plain SQL dump (human readable)"
        echo "  compressed - Gzipped SQL dump (saves space)"
        echo "  custom     - PostgreSQL custom format (flexible restore)"
        echo "  all        - All databases including roles and permissions"
        echo ""
        echo "Default: compressed"
        exit 1
        ;;
esac

# Display backup info
if [ -f "$BACKUP_FILE" ]; then
    SIZE=$(ls -lh "$BACKUP_FILE" | awk '{print $5}')
    echo "Backup size: $SIZE"
    echo "To restore: see restore_db.sh"
fi

# Database Setup and Migrations

This document explains how the database is set up and managed in ArtificialU.

## Overview

ArtificialU uses PostgreSQL for its database and Alembic for database migrations. This combination provides a robust and reliable way to manage database schema changes over time.

## Setup

### Local Development

1. Start the PostgreSQL database:

   ```sh
   docker compose up postgres
   ```

2. Initialize the database and run migrations:

   ```sh
   python initialize_db.py
   ```

### Production/Staging

For production or staging environments, the database is automatically initialized when the application is deployed using the migrations service in docker-compose.yml.

## Creating New Migrations

When you need to make changes to the database schema:

1. Make changes to your SQLAlchemy models in the `artificial_u/models/` directory

2. Generate a new migration:

   ```sh
   alembic revision --autogenerate -m "Description of changes"
   ```

3. Review the generated migration file in `alembic/versions/`

4. Apply the migration:

   ```sh
   alembic upgrade head
   ```

## Testing

When running tests, the test database is automatically created and migrations are applied:

```sh
python scripts/setup_test_db.py
```

## How It Works

1. **Models**: SQLAlchemy models define the database schema in Python code.
2. **Alembic**: Automatically generates migrations by comparing your models to the current database state.
3. **initialize_db.py**: Creates the database if it doesn't exist and runs all migrations.
4. **Docker**: The migrations service ensures the database is properly initialized when using Docker.

## Migration File Structure

- `alembic.ini`: Configuration file for Alembic
- `alembic/`: Contains all migration-related files
  - `env.py`: Environment configuration for Alembic
  - `versions/`: Contains individual migration files

## Benefits of This Approach

1. **Single Source of Truth**: Models define the schema, and migrations are generated from them
2. **Version Control**: All schema changes are tracked in version control
3. **Rollbacks**: Can easily roll back to previous schema versions
4. **Automation**: Migrations are automatically applied during deployment

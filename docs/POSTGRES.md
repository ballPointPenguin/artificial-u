# PostgreSQL Setup Guide

This guide explains how to set up PostgreSQL for ArtificialU.

## Running PostgreSQL with Docker Compose

The easiest way to run PostgreSQL for development is using the provided Docker Compose configuration:

1. Make sure Docker and Docker Compose are installed on your system
2. Start the PostgreSQL container:

```bash
docker-compose up -d
```

This will start a PostgreSQL instance with the following configuration:

- Username: postgres
- Password: postgres
- Database: artificial_u_dev
- Port: 5432 (standard PostgreSQL port)
- Data volume: postgres_data (persistent between restarts)

## Database Configuration

1. Copy the example environment file to create your .env file:

```bash
cp .env.example .env
```

2. The .env file should contain the DATABASE_URL for PostgreSQL:

```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/artificial_u_dev
```

3. If you've changed any of the PostgreSQL connection details (username, password, etc.) in the docker-compose.yml, update the URL accordingly.

## Initializing the Database

After setting up the PostgreSQL container, you need to initialize the database schema:

```bash
python initialize_db.py
```

This script will create all the necessary tables and indices in your PostgreSQL database.

## Working with the Database

### Connecting to PostgreSQL

To run manual SQL commands or inspect the database:

```bash
docker-compose exec postgres psql -U postgres -d artificial_u_dev
```

### Basic PostgreSQL Commands

Once connected, you can use these common commands:

- List all tables: `\dt`
- Describe a table: `\d table_name`
- Execute SQL: `SELECT * FROM professors;`
- Exit: `\q`

## Database Architecture

ArtificialU uses these main tables:

- **professors**: Stores professor information including personalities
- **courses**: Stores course details and syllabi
- **lectures**: Stores lecture content and links to audio files
- **departments**: Stores academic department information

## Troubleshooting

### Connection Issues

If you encounter connection issues:

1. Verify the PostgreSQL container is running:

```bash
docker-compose ps
```

2. Check the container logs:

```bash
docker-compose logs postgres
```

3. Verify your DATABASE_URL is correct in the .env file

## Production Considerations

For a production environment, you might want to:

1. Use a managed PostgreSQL service (AWS RDS, DigitalOcean managed databases, etc.)
2. Set up proper credentials with strong passwords
3. Enable TLS for secure connections
4. Set up regular backups

When deploying to production, make sure to update your DATABASE_URL with appropriate credentials and host.

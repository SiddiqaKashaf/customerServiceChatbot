# PostgreSQL Setup Guide

The RAG chatbot backend now supports both SQLite (for development) and PostgreSQL (for production). Here's how to set up and use PostgreSQL.

## Automatic Database Detection

The system automatically detects which database to use:
- **PostgreSQL**: If `DATABASE_URL` or `POSTGRES_URL` environment variable is set
- **SQLite**: If no PostgreSQL URL is provided (fallback for development)

## PostgreSQL Setup Options

### Option 1: Local PostgreSQL Installation

#### Install PostgreSQL
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# macOS
brew install postgresql
brew services start postgresql

# Windows
# Download from https://www.postgresql.org/download/windows/
```

#### Create Database and User
```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE rag_chatbot_db;
CREATE USER rag_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE rag_chatbot_db TO rag_user;
\q
```

#### Set Environment Variable
```bash
export DATABASE_URL=postgresql://rag_user:your_password@localhost:5432/rag_chatbot_db
```

### Option 2: Docker PostgreSQL

#### Docker Compose Setup
Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: rag_chatbot_db
      POSTGRES_USER: rag_user
      POSTGRES_PASSWORD: your_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

#### Start PostgreSQL
```bash
docker-compose up -d
export DATABASE_URL=postgresql://rag_user:your_password@localhost:5432/rag_chatbot_db
```

### Option 3: Cloud PostgreSQL Services

#### Heroku Postgres
```bash
# Add Heroku Postgres addon
heroku addons:create heroku-postgresql:hobby-dev

# Get database URL
heroku config:get DATABASE_URL
```

#### AWS RDS
```bash
# Create RDS instance and get connection string
export DATABASE_URL=postgresql://username:password@your-rds-endpoint:5432/dbname
```

#### Google Cloud SQL
```bash
# Create Cloud SQL instance and get connection string
export DATABASE_URL=postgresql://username:password@your-cloud-sql-ip:5432/dbname
```

#### Supabase (Free Tier)
```bash
# Sign up at supabase.com and get connection string
export DATABASE_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres
```

## Environment Configuration

### Development (.env file)
```env
# For PostgreSQL
DATABASE_URL=postgresql://rag_user:your_password@localhost:5432/rag_chatbot_db

# For SQLite (comment out DATABASE_URL)
# DATABASE_URL=
```

### Production
```bash
# Set environment variable
export DATABASE_URL=postgresql://username:password@host:port/database

# Or use POSTGRES_URL (alternative)
export POSTGRES_URL=postgresql://username:password@host:port/database
```

## Database Schema

The system automatically creates the required tables:

### Conversations Table (PostgreSQL)
```sql
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(255) NOT NULL,
    user_message TEXT NOT NULL,
    bot_response TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE INDEX idx_conversation_id ON conversations(conversation_id);
CREATE INDEX idx_timestamp ON conversations(timestamp);
```

### Conversations Table (SQLite - Fallback)
```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    user_message TEXT NOT NULL,
    bot_response TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT
);
```

## Testing Database Connection

### Test Configuration
```python
# Test database configuration
python -c "
import sys
sys.path.insert(0, '.')
from src.config.database import DatabaseConfig
print('Database URL:', DatabaseConfig.get_database_url())
print('Is PostgreSQL:', DatabaseConfig.is_postgresql())
"
```

### Test Connection
```python
# Test actual database connection
python -c "
import sys
sys.path.insert(0, '.')
from src.services.conversation_service import ConversationService
service = ConversationService()
print('Database connection successful!')
"
```

## Migration from SQLite to PostgreSQL

### Export SQLite Data
```python
import sqlite3
import json

# Connect to SQLite
conn = sqlite3.connect('src/database/conversations.db')
cursor = conn.cursor()

# Export conversations
cursor.execute('SELECT * FROM conversations')
rows = cursor.fetchall()

# Save to JSON
with open('conversations_backup.json', 'w') as f:
    json.dump(rows, f)

conn.close()
```

### Import to PostgreSQL
```python
import psycopg2
import json

# Load backup data
with open('conversations_backup.json', 'r') as f:
    rows = json.load(f)

# Connect to PostgreSQL
conn = psycopg2.connect("postgresql://user:pass@localhost:5432/dbname")
cursor = conn.cursor()

# Import conversations
for row in rows:
    cursor.execute('''
        INSERT INTO conversations (conversation_id, user_message, bot_response, timestamp, metadata)
        VALUES (%s, %s, %s, %s, %s)
    ''', row[1:])  # Skip the id column

conn.commit()
conn.close()
```

## Performance Optimization

### PostgreSQL Configuration
```sql
-- Optimize for read-heavy workloads
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET random_page_cost = 1.1;

-- Reload configuration
SELECT pg_reload_conf();
```

### Connection Pooling
For production, consider using connection pooling:

```python
# Install pgbouncer or use SQLAlchemy pooling
pip install sqlalchemy[postgresql]

# In your app configuration
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)
```

## Monitoring and Maintenance

### Check Database Size
```sql
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public';
```

### Monitor Connections
```sql
SELECT count(*) as active_connections 
FROM pg_stat_activity 
WHERE state = 'active';
```

### Backup Database
```bash
# Create backup
pg_dump $DATABASE_URL > backup.sql

# Restore backup
psql $DATABASE_URL < backup.sql
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   ```bash
   # Check if PostgreSQL is running
   sudo systemctl status postgresql
   
   # Start PostgreSQL
   sudo systemctl start postgresql
   ```

2. **Authentication Failed**
   ```bash
   # Check pg_hba.conf configuration
   sudo nano /etc/postgresql/15/main/pg_hba.conf
   
   # Ensure md5 or trust authentication is enabled
   ```

3. **Database Does Not Exist**
   ```sql
   -- Connect as superuser and create database
   sudo -u postgres createdb rag_chatbot_db
   ```

4. **Permission Denied**
   ```sql
   -- Grant permissions to user
   GRANT ALL PRIVILEGES ON DATABASE rag_chatbot_db TO rag_user;
   GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO rag_user;
   ```

### Debug Mode
```python
# Enable SQLAlchemy logging
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

## Production Deployment

### Environment Variables
```bash
# Required
export DATABASE_URL=postgresql://user:pass@host:port/dbname

# Optional
export FLASK_ENV=production
export SECRET_KEY=your-production-secret-key
```

### SSL Configuration
```python
# For production with SSL
DATABASE_URL=postgresql://user:pass@host:port/dbname?sslmode=require
```

### Health Checks
```python
# Add health check endpoint
@app.route('/health')
def health_check():
    try:
        # Test database connection
        service = ConversationService()
        return {'status': 'healthy', 'database': 'connected'}
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}, 500
```

## Benefits of PostgreSQL

1. **Scalability**: Better performance with large datasets
2. **ACID Compliance**: Data integrity and consistency
3. **JSON Support**: Native JSONB support for metadata
4. **Concurrent Access**: Better handling of multiple users
5. **Advanced Features**: Full-text search, indexing, etc.
6. **Production Ready**: Suitable for production deployments

The system will automatically use PostgreSQL when available and fall back to SQLite for development, making it flexible for different deployment scenarios.


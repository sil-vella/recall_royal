# Recall API

A Flask-based API service with PostgreSQL database and Redis caching.

## Features

- Flask REST API with modular plugin architecture
- PostgreSQL database with connection pooling
- Redis caching and rate limiting
- JWT-based authentication
- Docker containerization
- Health checks and monitoring
- Secure secret management

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- PostgreSQL 13+
- Redis 6+

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Create a `.env` file with the following variables:
```bash
POSTGRES_USER=recall_postgress_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=recall_postgres_db
DB_HOST=recall_db
DB_PORT=5432
RATE_LIMIT_STORAGE_URL=redis://recall_redis:6379/0
```

3. Build and start the containers:
```bash
docker-compose up -d
```

## Project Structure

```
.
├── app.py                  # Main application entry point
├── docker-compose.yml      # Docker Compose configuration
├── Dockerfile             # Docker build instructions
├── requirements.txt       # Python dependencies
├── plugins/              # Plugin modules
│   └── main_plugin/     # Main plugin with core functionality
├── tools/               # Utility tools and helpers
└── utils/              # Common utilities and configurations
```

## Development

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run tests:
```bash
pytest
```

## API Documentation

### Authentication
- POST `/auth/login`: Login with username and password
- POST `/auth/register`: Register a new user

### Health Check
- GET `/health`: API health status

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
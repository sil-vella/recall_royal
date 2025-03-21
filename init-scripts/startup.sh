#!/bin/bash

# Function to generate a secure random key
generate_secret_key() {
    openssl rand -hex 32
}

# Function to generate a Fernet key
generate_encryption_key() {
    python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
}

# Create secrets directory if it doesn't exist
mkdir -p /app/secrets

# Generate development secrets if they don't exist
if [ ! -f "/app/secrets/secret_key.dev" ]; then
    echo "Generating new SECRET_KEY..."
    generate_secret_key > /app/secrets/secret_key.dev
    echo "✅ SECRET_KEY generated"
fi

if [ ! -f "/app/secrets/encryption_key.dev" ]; then
    echo "Generating new ENCRYPTION_KEY..."
    generate_encryption_key > /app/secrets/encryption_key.dev
    echo "✅ ENCRYPTION_KEY generated"
fi

# Make sure the secret files are only readable by the application user
chmod 600 /app/secrets/secret_key.dev /app/secrets/encryption_key.dev

echo "✨ Secrets are ready"

# Start the Flask application
echo "🚀 Starting Flask application..."
python3 app.py 
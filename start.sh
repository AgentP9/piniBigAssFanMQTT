#!/bin/bash

# Haiku Fan MQTT Bridge - Quick Start Script

set -e

echo "======================================"
echo "Haiku Fan MQTT Bridge - Quick Start"
echo "======================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  Please edit .env and set your fan's IP address!"
    echo "   File: .env"
    echo ""
    read -p "Press Enter to continue after editing .env, or Ctrl+C to exit..."
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Build and start services
echo "Building and starting services..."
docker compose up -d --build

echo ""
echo "✅ Services started successfully!"
echo ""
echo "Access points:"
echo "  🌐 Web Interface: http://localhost:1919"
echo "  🔌 API Documentation: http://localhost:8000/docs"
echo "  📡 MQTT Broker: localhost:1883"
echo ""
echo "To view logs:"
echo "  docker compose logs -f"
echo ""
echo "To stop services:"
echo "  docker compose down"
echo ""

#!/bin/bash

# Simple script to simulate real-time traffic and anomalous logs for Mastra Sentinel

echo "Simulating traffic to Mastra Sentinel Pipeline..."
echo "Target: http://localhost:8000/api/v1/ingestion/logs"

# Simulate some normal traffic
echo "Sending normal INFO log..."
curl -X 'POST' \
  'http://localhost:8000/api/v1/ingestion/logs' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '[
  {
    "service": "payment-gateway",
    "level": "INFO",
    "message": "Payment processed successfully for order #8841",
    "component": "stripe-connector"
  }
]'

sleep 2

echo ""
echo "Sending anomaly (ERROR) log to trigger an incident..."
curl -X 'POST' \
  'http://localhost:8000/api/v1/ingestion/logs' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '[
  {
    "service": "auth-service",
    "level": "ERROR",
    "message": "Database connection timeout while fetching user profile. Retrying...",
    "component": "pg-pool"
  },
  {
    "service": "auth-service",
    "level": "CRITICAL",
    "message": "Max retry limit reached. Unable to connect to postgres-auth-db-1",
    "component": "pg-pool"
  }
]'

echo ""
echo "Traffic simulation complete. Check your dashboard!"

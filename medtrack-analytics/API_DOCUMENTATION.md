# MedTrack Analytics API Documentation

## Base URL
http://localhost:5000/api

## Authentication
Currently, the API runs without authentication for development purposes.

## Endpoints

### Health Check
- GET /health

### Drugs
- GET /drugs
- GET /drugs/{id}
- POST /drugs
- PUT /drugs/{id}
- GET /drugs/low-stock
- GET /drugs/inventory/value
- GET /drugs/expiring-soon
- POST /drugs/{id}/stock
- POST /drugs/batch-update
- GET /drugs/search

### Sales
- GET /sales
- GET /sales/{id}
- POST /sales
- GET /sales/analytics/daily
- GET /sales/analytics/period
- GET /sales/analytics/top-drugs
- GET /sales/analytics/revenue-trend
- GET /sales/analytics/pharmacy-performance
- GET /sales/analytics/payment-methods

### Analytics
- GET /analytics/dashboard
- GET /analytics/patient-demographics
- GET /analytics/prescription-patterns
- GET /analytics/inventory-health
- GET /analytics/predictive/low-stock-forecast
- POST /analytics/reports/custom

### Patients
- GET /patients
- GET /patients/{id}
- POST /patients
- PUT /patients/{id}
- GET /patients/{id}/prescriptions
- POST /patients/{id}/prescriptions
- GET /patients/search

## Sample Requests

### Create a Drug
```bash
curl -X POST http://localhost:5000/api/drugs \
  -H "Content-Type: application/json" \
  -d '{
    "drug_code": "TEST001",
    "drug_name": "Test Drug",
    "manufacturer": "Test Pharma",
    "category": "Prescription",
    "unit_price": 25.99,
    "stock_quantity": 100,
    "expiry_date": "2025-12-31"
  }'
```

### Create a Sale
```bash
curl -X POST http://localhost:5000/api/sales \
  -H "Content-Type: application/json" \
  -d '{
    "drug_id": 1,
    "quantity": 5,
    "unit_price": 10.99,
    "pharmacy_id": 101,
    "payment_method": "Credit Card"
  }'
```

### Get Dashboard Analytics
```bash
curl http://localhost:5000/api/analytics/dashboard
```

### Get Low Stock Forecast
```bash
curl "http://localhost:5000/api/analytics/predictive/low-stock-forecast?days=30"
```

## Error Responses
All errors return JSON in the format:
```json
{
  "success": false,
  "error": "Error message here"
}
```

## Status Codes
- 200: Success
- 201: Created
- 400: Bad Request
- 404: Not Found
- 500: Internal Server Error

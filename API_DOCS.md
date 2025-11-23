# Logical Version ERP API Documentation v5.2.1

**Version:** 5.2.1 (Stable)
**Date:** November 23, 2025
**Base URL:** /api/v1

## Overview
This API provides access to the Logical Version ERP system features, including Inventory, Sales, Accounting, Performance Monitoring, and System Management.

## Authentication
All API endpoints require a valid JWT token in the Authorization header.
Authorization: Bearer <token>

### Login
**POST** /auth/login
- **Body:**
  `json
  {
    "username": "admin",
    "password": "password123"
  }
  ` 
- **Response:**
  `json
  {
    "access_token": "eyJhbGciOiJIUzI1Ni...",
    "token_type": "bearer",
    "expires_in": 3600
  }
  ` 

---

## Performance & Monitoring (New in v5.2.0)

### Get Current Metrics
**GET** /performance/metrics/current
- **Description:** Retrieve real-time system performance metrics.
- **Response:**
  `json
  {
    "cpu_usage": 12.5,
    "memory_usage_mb": 145.2,
    "db_size_mb": 50.1,
    "active_connections": 5,
    "timestamp": "2025-11-23T14:30:00"
  }
  ` 

### Get Slow Queries
**GET** /performance/slow-queries
- **Description:** List recent slow database queries.
- **Parameters:**
  - limit (optional): Number of records (default: 50)
- **Response:**
  `json
  [
    {
      "query": "SELECT * FROM sales WHERE...",
      "duration_ms": 150.5,
      "timestamp": "2025-11-23T14:25:10"
    }
  ]
  ` 

### Export Metrics
**GET** /performance/export
- **Parameters:**
  - format: json or csv
- **Response:** File download.

---

## Backup & Recovery (Enhanced in v5.2.1)

### Create Backup
**POST** /system/backup
- **Body:**
  `json
  {
    "type": "full",  // or "incremental"
    "compress": true,
    "encrypt": true,
    "description": "Manual backup before update"
  }
  ` 
- **Response:**
  `json
  {
    "success": true,
    "backup_id": "backup_20251123_143000",
    "path": "/data/backups/backup_20251123_143000.zip",
    "size_bytes": 1048576
  }
  ` 

### List Backups
**GET** /system/backups
- **Response:**
  `json
  [
    {
      "id": "backup_20251123_143000",
      "type": "full",
      "created_at": "2025-11-23T14:30:00",
      "size": "1.0 MB",
      "encrypted": true
    }
  ]
  ` 

---

## Security (Enhanced in v5.2.0)

### Enable 2FA
**POST** /auth/2fa/enable
- **Response:**
  `json
  {
    "secret": "JBSWY3DPEHPK3PXP",
    "qr_code_url": "otpauth://totp/LogicalERP:admin?secret=..."
  }
  ` 

### Verify 2FA
**POST** /auth/2fa/verify
- **Body:** {"code": "123456"}

---

## Core Modules (v3.5.0+)

### Products
- **GET** /products: List all products
- **POST** /products: Create new product
- **GET** /products/{id}: Get product details
- **PUT** /products/{id}: Update product
- **DELETE** /products/{id}: Delete product

### Sales
- **POST** /sales: Create new sale invoice
- **GET** /sales: List sales history
- **GET** /sales/{id}: Get invoice details

### Reports
- **GET** /reports/sales: Sales summary report
- **GET** /reports/inventory: Inventory status report
- **GET** /reports/profit-loss: Profit & Loss statement

---

## Error Handling
All endpoints return standard HTTP status codes:
- 200 OK: Success
- 400 Bad Request: Invalid input
- 401 Unauthorized: Invalid or missing token
- 403 Forbidden: Insufficient permissions
- 404 Not Found: Resource not found
- 500 Internal Server Error: System error

For detailed schema definitions, please refer to the openapi.json file.

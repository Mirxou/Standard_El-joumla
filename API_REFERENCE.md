# API Documentation - Logical Version ERP v3.5.1

## 🚀 Quick Start

### Base URL
```
Production: https://your-domain.com/api
Development: http://localhost:8000
```

### Authentication

All API endpoints (except `/auth/login` and `/health`) require JWT authentication.

#### 1. Login
```http
POST /auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": 1,
  "username": "admin",
  "role": "admin"
}
```

#### 2. Use Token
```http
GET /products
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 📦 Products API

### List Products
```http
GET /products?page=1&page_size=20&tag=electronics
Authorization: Bearer {token}
```

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "Laptop HP",
      "sku": "LAP-001",
      "price": 3500.00,
      "stock": 15,
      "category": "Electronics"
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "pages": 8
}
```

### Create Product
```http
POST /products
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Laptop Dell XPS 15",
  "sku": "LAP-002",
  "description": "High-performance laptop",
  "price": 4500.00,
  "cost": 3200.00,
  "stock": 10,
  "min_stock": 2,
  "category": "Electronics",
  "tags": ["laptop", "dell", "premium"]
}
```

### Create Product Variant
```http
POST /products/{product_id}/variants
Authorization: Bearer {token}

{
  "sku": "LAP-002-16GB-512",
  "attributes": {
    "RAM": "16GB",
    "Storage": "512GB SSD",
    "Color": "Silver"
  },
  "price": 4800.00,
  "stock": 5
}
```

---

## 🛒 Sales API

### Create Sales Order
```http
POST /sales/orders
Authorization: Bearer {token}

{
  "customer_id": 15,
  "items": [
    {
      "product_id": 1,
      "quantity": 2,
      "unit_price": 3500.00,
      "discount": 100.00
    }
  ],
  "payment_method": "credit_card",
  "notes": "Urgent delivery"
}
```

**Response:**
```json
{
  "order_id": 1001,
  "total_amount": 6900.00,
  "status": "pending",
  "created_at": "2025-11-21T10:30:00Z"
}
```

### Create Quote
```http
POST /quotes
Authorization: Bearer {token}

{
  "customer_id": 15,
  "valid_until": "2025-12-31",
  "items": [
    {
      "product_id": 1,
      "quantity": 5,
      "unit_price": 3500.00
    }
  ]
}
```

---

## 📊 Inventory API

### Get Stock Levels
```http
GET /inventory/stock?location_id=1
Authorization: Bearer {token}
```

### Transfer Stock
```http
POST /inventory/transfer
Authorization: Bearer {token}

{
  "product_id": 1,
  "from_location": 1,
  "to_location": 2,
  "quantity": 10,
  "reason": "Restock branch"
}
```

### ABC Analysis
```http
GET /inventory/abc-analysis
Authorization: Bearer {token}
```

**Response:**
```json
{
  "A_class": [
    {
      "product_id": 1,
      "value": 52500.00,
      "percentage": 35.2
    }
  ],
  "B_class": [...],
  "C_class": [...]
}
```

---

## 🤖 AI Features API

### AI Chatbot
```http
POST /ai/chat
Authorization: Bearer {token}

{
  "message": "What are my top selling products?",
  "customer_id": 1,
  "language": "ar"
}
```

**Response:**
```json
{
  "response": "أفضل 3 منتجات مبيعاً هذا الشهر هي: Laptop HP (150 وحدة), Mouse Wireless (120 وحدة), Keyboard Gaming (95 وحدة)",
  "intent": "sales",
  "confidence": 0.95,
  "conversation_id": "conv-123"
}
```

### Sales Forecast
```http
GET /ai/forecast/sales?period=30
Authorization: Bearer {token}
```

### Product Recommendations
```http
GET /ai/recommendations/{customer_id}
Authorization: Bearer {token}
```

---

## 🎁 Loyalty Program API

### Earn Points
```http
POST /loyalty/earn
Authorization: Bearer {token}

{
  "customer_id": 15,
  "amount": 500.00,
  "transaction_type": "purchase",
  "reference_id": "ORD-1001"
}
```

### Redeem Points
```http
POST /loyalty/redeem
Authorization: Bearer {token}

{
  "customer_id": 15,
  "points": 100,
  "transaction_type": "discount"
}
```

### Check Balance
```http
GET /loyalty/balance/{customer_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "customer_id": 15,
  "total_points": 2500,
  "tier": "Gold",
  "cashback_rate": 0.03,
  "tier_benefits": "3% cashback on all purchases"
}
```

---

## 📄 E-Invoicing API

### Generate E-Invoice
```http
POST /einvoice/generate/{invoice_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "invoice_id": 1001,
  "einvoice_id": "E-INV-2025-1001",
  "qr_code": "data:image/png;base64,iVBOR...",
  "digital_signature": "a3f5b...",
  "xml_content": "<?xml version='1.0'?>...",
  "status": "approved"
}
```

### Get E-Invoice XML
```http
GET /einvoice/{invoice_id}/xml
Authorization: Bearer {token}
```

---

## 📢 Marketing API

### Create Campaign
```http
POST /marketing/campaigns
Authorization: Bearer {token}

{
  "name": "Summer Sale 2025",
  "campaign_type": "EMAIL",
  "start_date": "2025-06-01",
  "end_date": "2025-06-30",
  "budget": 10000.00,
  "target_segment": "premium_customers"
}
```

### Send Campaign
```http
POST /marketing/campaigns/{id}/send
Authorization: Bearer {token}
```

### Get Analytics
```http
GET /marketing/campaigns/{id}/analytics
Authorization: Bearer {token}
```

**Response:**
```json
{
  "campaign_id": 1,
  "sent": 1500,
  "delivered": 1485,
  "opened": 890,
  "clicked": 245,
  "conversions": 67,
  "revenue": 25600.00,
  "roi": 2.56,
  "open_rate": 0.599,
  "click_rate": 0.275
}
```

---

## 🏪 Vendor Portal API

### Get Vendor Dashboard
```http
GET /vendor/dashboard/{vendor_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "orders": {
    "total": 45,
    "pending": 5,
    "approved": 12,
    "completed": 28
  },
  "unread_messages": 3,
  "performance": {
    "quality": 4.5,
    "delivery": 4.8,
    "communication": 4.7,
    "overall": 4.67
  }
}
```

### Send Message
```http
POST /vendor/message
Authorization: Bearer {token}

{
  "vendor_id": 10,
  "subject": "Delivery Schedule Update",
  "message": "Please confirm delivery date",
  "priority": "high"
}
```

---

## 🛡️ MFA API

### Enable MFA
```http
POST /auth/mfa/enable
Authorization: Bearer {token}

{
  "methods": ["TOTP", "SMS"],
  "phone": "+966501234567"
}
```

**Response:**
```json
{
  "totp_secret": "JBSWY3DPEHPK3PXP",
  "qr_code_url": "otpauth://totp/LogicalVersion:admin?secret=JBSWY...",
  "backup_codes": [
    "1a2b3c4d",
    "5e6f7g8h",
    ...
  ]
}
```

### Verify MFA
```http
POST /auth/mfa/verify
Authorization: Bearer {token}

{
  "code": "123456",
  "method": "TOTP"
}
```

---

## 📈 Reports API

### Sales Summary
```http
POST /reports/sales-summary
Authorization: Bearer {token}

{
  "start_date": "2025-01-01",
  "end_date": "2025-01-31",
  "group_by": "product"
}
```

### Inventory Report
```http
GET /reports/inventory/current
Authorization: Bearer {token}
```

### Financial Report
```http
GET /reports/financial?type=balance_sheet&period=monthly
Authorization: Bearer {token}
```

---

## 🔍 Advanced Search API

### Search Across System
```http
POST /search
Authorization: Bearer {token}

{
  "query": "laptop",
  "filters": {
    "category": "Electronics",
    "price_min": 2000,
    "price_max": 5000
  },
  "sort": "price_desc",
  "page": 1,
  "page_size": 20
}
```

---

## ⚡ Rate Limits

| Endpoint Type | Rate Limit |
|--------------|------------|
| Auth endpoints | 3 requests/minute |
| General API | 60 requests/minute |
| AI endpoints | 20 requests/minute |
| Reports | 10 requests/minute |

---

## 🐛 Error Handling

### Error Response Format
```json
{
  "detail": "Product not found",
  "error_code": "PRODUCT_NOT_FOUND",
  "status_code": 404
}
```

### Common Error Codes
- `401 UNAUTHORIZED`: Invalid or missing token
- `403 FORBIDDEN`: Insufficient permissions
- `404 NOT_FOUND`: Resource not found
- `422 VALIDATION_ERROR`: Invalid input data
- `429 TOO_MANY_REQUESTS`: Rate limit exceeded
- `500 INTERNAL_ERROR`: Server error

---

## 📚 Interactive Documentation

Visit `/docs` for interactive Swagger UI:
- http://localhost:8000/docs

OpenAPI spec available at:
- http://localhost:8000/openapi.json

---

## 💡 Best Practices

1. **Always use HTTPS in production**
2. **Store JWT tokens securely** (httpOnly cookies recommended)
3. **Implement token refresh** mechanism
4. **Handle rate limits** with exponential backoff
5. **Validate all input** on client side
6. **Use pagination** for large datasets
7. **Cache frequently accessed** data
8. **Monitor API usage** and errors
9. **Keep API version** in sync
10. **Test with Postman** collection (see `api_postman_collection.json`)

---

For more examples, see:
- `api_samples.http` - VS Code REST Client examples
- `api_postman_collection.json` - Postman collection
- `/docs` - Interactive API documentation

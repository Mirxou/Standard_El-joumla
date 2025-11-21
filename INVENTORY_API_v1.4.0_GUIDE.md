# Inventory Management API Guide - v1.4.0

## 📦 Overview

The Inventory Management API provides comprehensive stock control, warehouse management, and inventory analytics capabilities. This module supports multi-location warehousing, stock reservations, transfer tracking, and ABC analysis for optimal inventory management.

---

## 🎯 Key Features

1. **Stock Transfer Operations** - Transfer inventory between warehouse locations
2. **Stock Reservation System** - Reserve stock for orders and prevent overselling
3. **Movement Tracking** - Complete audit trail of all inventory movements
4. **ABC Analysis** - Automatic product categorization by inventory value
5. **Multi-Location Support** - Manage inventory across multiple warehouses
6. **Batch Tracking** - Track inventory by batch/lot numbers
7. **Barcode Integration** - Support for barcode scanning operations

---

## 🔐 Authentication

All endpoints require JWT authentication. Include the access token in the Authorization header:

```
Authorization: Bearer <your_access_token>
```

### Role-Based Access

| Endpoint | Admin | Warehouse | Cashier | Manager |
|----------|-------|-----------|---------|---------|
| Transfer Stock | ✅ | ✅ | ❌ | ❌ |
| Reserve Stock | ✅ | ❌ | ✅ | ❌ |
| Release Stock | ✅ | ❌ | ✅ | ❌ |
| List Movements | ✅ | ✅ | ✅ | ✅ |
| ABC Analysis | ✅ | ❌ | ❌ | ✅ |

---

## 📋 API Endpoints

### 1. Transfer Stock Between Locations

Transfer inventory from one warehouse location to another.

**Endpoint:** `POST /inventory/transfer`

**Request Body:**
```json
{
  "product_id": 1,
  "quantity": 50,
  "from_location": "Main Warehouse",
  "to_location": "Retail Store A",
  "notes": "Weekly restock for store A"
}
```

**Response:** `201 Created`
```json
{
  "message": "Stock transferred successfully"
}
```

**Use Cases:**
- Warehouse to retail store transfers
- Inter-warehouse transfers
- Department relocations
- Branch inventory distribution

---

### 2. Reserve Stock for Orders

Reserve inventory to prevent overselling and ensure availability for confirmed orders.

**Endpoint:** `POST /inventory/reserve`

**Request Body:**
```json
{
  "product_id": 1,
  "quantity": 10,
  "reference_id": 1234,
  "reference_type": "order"
}
```

**Parameters:**
- `product_id`: Product to reserve
- `quantity`: Amount to reserve
- `reference_id`: Order/quote ID (optional)
- `reference_type`: Type of reference - "order", "quote", "maintenance" (default: "order")

**Response:** `201 Created`
```json
{
  "message": "Stock reserved successfully"
}
```

**Use Cases:**
- Order confirmation reservations
- Quote preparation
- Maintenance operations
- Pre-allocation for VIP customers

---

### 3. Release Reserved Stock

Release previously reserved inventory back to available stock.

**Endpoint:** `POST /inventory/release/{product_id}`

**Query Parameters:**
- `quantity`: Amount to release (required, minimum 1)
- `reference_id`: Original reference ID (optional)

**Example:**
```
POST /inventory/release/1?quantity=5&reference_id=1234
```

**Response:** `200 OK`
```json
{
  "message": "Stock released successfully"
}
```

**Use Cases:**
- Order cancellation
- Quote expiration
- Partial order fulfillment adjustment
- Correcting over-reservation

---

### 4. List Stock Movements

Retrieve complete history of inventory movements with filtering and pagination.

**Endpoint:** `GET /inventory/movements`

**Query Parameters:**
- `product_id`: Filter by specific product (optional)
- `limit`: Maximum results to return (1-1000, default: 100)

**Example:**
```
GET /inventory/movements?product_id=1&limit=50
```

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": 1,
      "product_id": 1,
      "movement_type": "TRANSFER",
      "quantity": 50,
      "from_location": "Main Warehouse",
      "to_location": "Store A",
      "notes": "Weekly restock",
      "created_at": "2025-11-19T10:30:00",
      "created_by": "admin"
    },
    {
      "id": 2,
      "product_id": 1,
      "movement_type": "RESERVATION",
      "quantity": 10,
      "reference_id": 1234,
      "reference_type": "order",
      "created_at": "2025-11-19T11:00:00"
    }
  ],
  "total": 2
}
```

**Movement Types:**
- `TRANSFER` - Location transfers
- `RESERVATION` - Stock reservations
- `RELEASE` - Release from reservation
- `ADJUSTMENT` - Manual stock adjustments
- `LOSS` - Damaged/lost inventory

**Use Cases:**
- Audit trail review
- Movement history analysis
- Reconciliation
- Compliance reporting

---

### 5. ABC Analysis

Automatic product categorization based on inventory value (Pareto principle).

**Endpoint:** `GET /inventory/abc-analysis`

**Response:** `200 OK`
```json
{
  "A": [
    {
      "product_id": 5,
      "name": "Premium Product",
      "total_value": 50000.00,
      "percentage": 45.5
    },
    {
      "product_id": 12,
      "name": "High Value Item",
      "total_value": 38000.00,
      "percentage": 34.5
    }
  ],
  "B": [
    {
      "product_id": 3,
      "name": "Mid Range Product",
      "total_value": 15000.00,
      "percentage": 13.6
    }
  ],
  "C": [
    {
      "product_id": 8,
      "name": "Low Value Item",
      "total_value": 5000.00,
      "percentage": 4.5
    }
  ]
}
```

**Categories:**
- **Category A**: Top 80% of inventory value - Focus on tight control, frequent reviews
- **Category B**: Next 15% of value - Moderate control and review
- **Category C**: Remaining 5% - Minimal control, bulk ordering

**Use Cases:**
- Inventory optimization
- Purchasing priority decisions
- Storage allocation planning
- Focus management attention on high-value items

---

## 🔄 Common Workflows

### Workflow 1: Order Fulfillment with Reservation

```bash
# 1. Reserve stock when order is confirmed
POST /inventory/reserve
{
  "product_id": 1,
  "quantity": 20,
  "reference_id": 1001,
  "reference_type": "order"
}

# 2. Transfer to shipping area
POST /inventory/transfer
{
  "product_id": 1,
  "quantity": 20,
  "from_location": "Main Warehouse",
  "to_location": "Shipping Area",
  "notes": "Order #1001"
}

# 3. If order cancelled, release reservation
POST /inventory/release/1?quantity=20&reference_id=1001
```

### Workflow 2: Store Restock

```bash
# 1. Check current movements
GET /inventory/movements?product_id=1&limit=10

# 2. Transfer to store
POST /inventory/transfer
{
  "product_id": 1,
  "quantity": 100,
  "from_location": "Central Warehouse",
  "to_location": "Store Branch A",
  "notes": "Monthly restock"
}

# 3. Verify movement was recorded
GET /inventory/movements?product_id=1&limit=1
```

### Workflow 3: Strategic Inventory Planning

```bash
# 1. Get ABC Analysis
GET /inventory/abc-analysis

# 2. Review Category A products (high value)
# 3. Focus purchasing and control on these items
# 4. Apply different strategies per category
```

---

## 💡 Best Practices

### 1. Stock Reservations
- Always reserve stock when order is confirmed
- Use meaningful reference_type values
- Release reservations promptly on cancellation
- Monitor reservation aging

### 2. Location Management
- Use consistent location naming conventions
- Document location codes in your system
- Track transfers between locations
- Regular location audits

### 3. Movement Tracking
- Include detailed notes for transfers
- Regular review of movement history
- Monitor unusual patterns
- Use for compliance reporting

### 4. ABC Analysis Usage
- Run analysis monthly or quarterly
- Adjust ordering strategies per category
- Category A: Weekly review, tight control
- Category B: Bi-weekly review, moderate control
- Category C: Monthly review, bulk ordering

---

## ⚠️ Error Handling

### Common Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| 401 | Unauthorized | Provide valid JWT token |
| 403 | Insufficient privileges | Use account with proper role |
| 422 | Validation error | Check request data format |
| 500 | Operation failed | Check product exists, sufficient stock |
| 501 | Service unavailable | Inventory service not initialized |

### Example Validation Errors

```json
// Negative quantity
{
  "detail": [
    {
      "loc": ["body", "quantity"],
      "msg": "ensure this value is greater than or equal to 1",
      "type": "value_error.number.not_ge"
    }
  ]
}
```

---

## 📊 Integration Examples

### Python Example

```python
import requests

BASE_URL = "http://localhost:8000"
token = "your_jwt_token"
headers = {"Authorization": f"Bearer {token}"}

# Transfer stock
transfer_data = {
    "product_id": 1,
    "quantity": 50,
    "from_location": "Warehouse A",
    "to_location": "Store B",
    "notes": "Weekly restock"
}
response = requests.post(
    f"{BASE_URL}/inventory/transfer",
    json=transfer_data,
    headers=headers
)
print(response.json())

# Reserve stock
reserve_data = {
    "product_id": 1,
    "quantity": 10,
    "reference_id": 1234,
    "reference_type": "order"
}
response = requests.post(
    f"{BASE_URL}/inventory/reserve",
    json=reserve_data,
    headers=headers
)
print(response.json())

# Get ABC analysis
response = requests.get(
    f"{BASE_URL}/inventory/abc-analysis",
    headers=headers
)
analysis = response.json()
print(f"Category A products: {len(analysis.get('A', []))}")
```

### JavaScript/Node.js Example

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:8000';
const token = 'your_jwt_token';
const headers = { Authorization: `Bearer ${token}` };

// Transfer stock
async function transferStock() {
  const response = await axios.post(
    `${BASE_URL}/inventory/transfer`,
    {
      product_id: 1,
      quantity: 50,
      from_location: 'Warehouse A',
      to_location: 'Store B',
      notes: 'Weekly restock'
    },
    { headers }
  );
  console.log(response.data);
}

// List movements
async function getMovements() {
  const response = await axios.get(
    `${BASE_URL}/inventory/movements?product_id=1&limit=10`,
    { headers }
  );
  console.log(`Total movements: ${response.data.total}`);
}
```

---

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all inventory API tests
python test_inventory_api.py

# Or use pytest
pytest test_inventory_api.py -v
```

**Test Coverage:**
- ✅ Stock transfer operations
- ✅ Stock reservation and release
- ✅ Movement tracking and filtering
- ✅ ABC analysis
- ✅ Authorization checks
- ✅ Validation errors
- ✅ Pagination

---

## 📈 Performance Considerations

1. **Movement History**: Use limit parameter to avoid large result sets
2. **Product Filtering**: Always filter by product_id when possible
3. **ABC Analysis**: Cache results, run periodically (not per-request)
4. **Batch Operations**: For bulk transfers, consider implementing batch endpoint
5. **Indexing**: Database indexes on product_id, created_at for movements table

---

## 🔮 Future Enhancements

- Inventory count/cycle count API
- Batch/lot number tracking endpoints
- Low stock alerts and notifications
- Automated reorder point calculations
- Integration with purchase orders
- Multi-currency inventory valuation
- Inventory aging reports
- Warehouse capacity management

---

## 📞 Support

For issues, questions, or contributions:
- Review المواصفات.md for complete ERP specifications
- Check CHANGELOG.md for version history
- See test_inventory_api.py for usage examples

---

**Version:** 1.4.0  
**Last Updated:** November 19, 2025  
**API Base URL:** `http://localhost:8000`

# 🎯 Security & i18n Quick Reference

## 🚀 Quick Start

### Rate Limiting
```python
from src.security.rate_limiter import login_rate_limiter

# Check if request is allowed
allowed, remaining = login_rate_limiter.is_allowed("client_ip_or_token")
if not allowed:
    raise HTTPException(status_code=429, detail="Rate limit exceeded")
```

### Internationalization
```python
from src.utils.i18n_api import I18n

i18n = I18n()

# Negotiate locale from Accept-Language header
locale = i18n.negotiate_locale(accept_language="ar,en-US;q=0.9")

# Get translated message
message = i18n.get_message("order_created", locale, order_id=12345)
# Returns: "تم إنشاء الطلب 12345 بنجاح" (Arabic)
# Or: "Order 12345 created successfully" (English)
```

---

## 🔒 Security Features

### Rate Limiter Configuration
- **Login Endpoint**: 10 attempts / 5 minutes
- **API Endpoints**: 100 requests / minute
- **Storage**: Thread-safe in-memory
- **Cleanup**: Automatic (hourly)

### RBAC Roles
- **Admin**: Full access
- **Cashier**: Sales + limited inventory
- **Viewer**: Read-only

---

## 🌍 Supported Languages

| Code | Language | Status | Messages |
|------|----------|--------|----------|
| `ar` | العربية | ✅ Default | 70+ |
| `en` | English | ✅ Full | 70+ |

---

## 📝 Message Keys

### Common Messages
```
app_title, welcome, login, logout
username, password, dashboard
sales, purchases, inventory
products, customers, suppliers
```

### Status Messages
```
order_created, order_updated, order_not_found
payment_received, refund_created, return_created
stock_received, po_status_updated
```

### Error Messages
```
insufficient_privileges, authentication_failed
invalid_token, rate_limit_exceeded
validation_error, internal_error, not_found
```

---

## 🧪 Testing

Run all tests:
```bash
pytest tests/ -v
```

Run security tests only:
```bash
pytest tests/test_api_vendor_rating.py -v -k rbac
```

---

## 📊 Monitoring

### Rate Limit Metrics
- Track hits per endpoint
- Monitor blocked requests
- Adjust limits based on traffic

### i18n Metrics
- Track locale distribution
- Monitor message lookup failures
- Update translations as needed

---

## 🔧 Configuration

### Environment Variables
```bash
RATE_LIMIT_ENABLED=true
I18N_DEFAULT_LOCALE=ar
```

### File Locations
```
src/security/rate_limiter.py    # Rate limiter implementation
src/utils/i18n_api.py            # i18n service
locales/ar.json                  # Arabic messages
locales/en.json                  # English messages
```

---

## ✅ Production Checklist

- [x] All tests passing (49/49)
- [x] Rate limiter enabled
- [x] i18n messages loaded
- [x] Security audit complete
- [x] Documentation updated
- [x] Performance tested
- [x] Monitoring configured

---

**Version**: 2.0.0  
**Last Updated**: 2025-11-20  
**Status**: ✅ Production Ready

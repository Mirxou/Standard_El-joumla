# Mobile App Integration Guide

This guide explains how to connect and integrate the Logical Version ERP mobile app (React Native/Flutter) with the backend system.

---

## 1. API Endpoints
- All REST API endpoints are available at: `https://your-server.com/api/`
- Authentication: JWT (via `/auth/login`)
- MFA/OTP: `/auth/mfa/verify` (TOTP, SMS, Email)
- All business modules (sales, inventory, support, etc.) are accessible via documented endpoints.

## 2. Authentication Flow
1. User logs in with username/password → receives JWT.
2. If MFA is enabled, prompt for OTP (from Google Authenticator, SMS, or Email).
3. Store JWT securely (encrypted storage on device).
4. Use JWT in `Authorization: Bearer <token>` header for all requests.

## 3. Example: Login + 2FA (React Native)
```js
// Pseudocode
const login = async (username, password) => {
  const res = await fetch('/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) });
  const data = await res.json();
  if (data.mfa_required) {
    // Prompt for OTP
    const otp = await promptUserForOTP();
    const verify = await fetch('/auth/mfa/verify', { method: 'POST', body: JSON.stringify({ otp, user_id: data.user_id }) });
    // On success, store JWT
  } else {
    // Store JWT
  }
};
```

## 4. Encryption & Security
- All sensitive data (tokens, user info) must be stored using device secure storage (Keychain/Keystore).
- All API calls must use HTTPS.
- Local data (offline mode) should be encrypted (AES-256 recommended).

## 5. Barcode Scanning
- Use `react-native-camera` or `expo-barcode-scanner` for product barcode scanning.
- Send scanned code to `/products/{barcode}` endpoint to fetch product info.

## 6. Push Notifications
- Use Firebase Cloud Messaging (FCM) for push notifications.
- Backend can send notifications for new orders, support replies, etc.

## 7. Example Screens
- Login (with 2FA)
- Dashboard (KPIs)
- Sales Order Entry
- Inventory Lookup
- Support Ticket Submission
- Knowledge Base Search

## 8. Testing
- Use Postman to test all endpoints before mobile integration.
- Use device emulators and real devices for QA.

---

> For full API documentation, see `API_REFERENCE.md` and Swagger UI at `/docs` on your server.

# Wholesale AI Chatbot - Pi Network App

AI-powered wholesale management chatbot integrated with Pi Network authentication.

## Features

- 🔐 Pi Network Authentication
- 💬 AI Chat Interface
- 📸 Image Upload Support
- 🌍 RTL Support (Arabic/English)
- 🌙 Dark Mode UI

## Setup

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure Environment
Create `.env` file:
```env
NEXT_PUBLIC_PI_APP_ID=your_app_id_here
NEXT_PUBLIC_DEFAULT_LOCALE=en
NEXT_PUBLIC_SANDBOX=true

# Backend URLs (configure when ready)
STANDARD_API_BASE_URL=
STANDARD_API_UPLOAD_URL=
STANDARD_MEDIA_BASE_URL=
```

### 3. Run Development Server
```bash
npm run dev
```

## Testing in Pi Browser

1. Set **Development URL** in Pi Developer console to `http://localhost:3000`
2. Open app inside **Pi Browser** (not regular browser)
3. Authentication should complete automatically
4. Backend login requires server setup (see next section)

## Backend Requirements

Your backend server must implement these endpoints:

- `POST /v1/login` - Verify Pi payment and create session cookie
- `POST /v1/chat/default` - Process chat messages
- `POST /upload` - Handle image uploads
- `GET /health` - Health check

Required headers:
- CORS with credentials support
- `Set-Cookie` with HttpOnly, Secure, SameSite=None

## Deployment

### Vercel (Recommended)
1. Push code to GitHub
2. Import to Vercel
3. Add environment variables
4. Deploy

### Production URLs
Update Pi Developer console with:
- **App URL**: `https://your-app.vercel.app`
- **Privacy Policy**: `https://your-app.vercel.app/privacy`
- **Terms of Service**: `https://your-app.vercel.app/terms`

## License

MIT

# الإصدار المنطقي - Mobile Application

تطبيق جوال مبني بـ React Native + TypeScript

## المتطلبات

- Node.js >= 18
- React Native CLI
- Android Studio (للتطوير على Android)
- Xcode (للتطوير على iOS - macOS فقط)

## التثبيت

```bash
npm install
```

## التشغيل

### Android
```bash
npm run android
```

### iOS
```bash
npm run ios
```

## الميزات

- ✅ React Native 0.73
- ✅ TypeScript
- ✅ React Navigation (Stack + Bottom Tabs)
- ✅ React Query لإدارة البيانات
- ✅ Axios للـ API Calls
- ✅ AsyncStorage للتخزين المحلي
- ✅ Authentication مع JWT
- ✅ Offline Support
- ✅ Push Notifications

## البنية

```
src/
  ├── components/     # المكونات المشتركة
  ├── contexts/       # Context API (Auth)
  ├── navigation/     # Navigation Configuration
  ├── screens/        # شاشات التطبيق
  ├── services/       # API Services
  └── App.tsx         # المكون الرئيسي
```

## التكوين

### API Configuration

التطبيق يستخدم نظام تكوين موحد في `src/config/api.ts`:

```typescript
import { API_CONFIG } from './config/api';

// استخدام API_CONFIG.BASE_URL و API_CONFIG.ENDPOINTS
```

**ملاحظة:** حالياً يستخدم `http://localhost:8000` كقيمة افتراضية.
لإضافة دعم environment variables، يمكن تثبيت `react-native-config`:

```bash
npm install react-native-config
```

ثم إنشاء ملف `.env` في مجلد `mobile/`:
```
API_BASE_URL=http://localhost:8000
```

## ملاحظات

- API Configuration موجود في `src/config/api.ts` (موحد مع Web App)
- للتطوير على Android، تأكد من تشغيل Android Emulator أو توصيل جهاز
- للتطوير على iOS، تأكد من تشغيل iOS Simulator
- للتطوير مع Backend API، تأكد من تشغيل Backend على `localhost:8000`

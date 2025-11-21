# Standard El-Joumla - Pi Network Chatbot

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Next.js](https://img.shields.io/badge/Next.js-15.2.4-black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue)

## 🚀 Quick Deploy to Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/Mirxou/Standard_El-joumla)

## 📋 الوصف

تطبيق محادثة ذكي مخصص لشبكة Pi Network لإدارة المبيعات بالجملة مع تتبع المخزون في الوقت الفعلي.

## ✨ المميزات

- 🔐 مصادقة Pi Network SDK
- 💬 واجهة محادثة تفاعلية
- 📊 إدارة المخزون
- 🌓 دعم الوضع الليلي/النهاري
- 📱 تصميم متجاوب لجميع الشاشات
- 🌍 دعم اللغتين العربية والإنجليزية

## 🛠️ التقنيات المستخدمة

- **Framework**: Next.js 15.2.4 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Radix UI
- **Icons**: Lucide React
- **Authentication**: Pi Network SDK

## 📦 التثبيت المحلي

```bash
# استنساخ المشروع
git clone https://github.com/Mirxou/Standard_El-joumla.git
cd Standard_El-joumla

# تثبيت الحزم
npm install

# تشغيل في وضع التطوير
npm run dev
```

افتح [http://localhost:3000](http://localhost:3000) في المتصفح.

## 🌐 النشر على Vercel

### الطريقة الأولى: عبر Dashboard

1. اذهب إلى [Vercel Dashboard](https://vercel.com/new)
2. اختر "Import Git Repository"
3. حدد `Mirxou/Standard_El-joumla`
4. اضغط "Deploy"

### الطريقة الثانية: عبر CLI

```bash
# تثبيت Vercel CLI
npm i -g vercel

# النشر
vercel
```

## 🔗 ربط التطبيق بـ Pi Network

بعد نشر التطبيق على Vercel:

1. انسخ رابط التطبيق (مثال: `https://your-app.vercel.app`)
2. اذهب إلى **Pi Developer Portal** في Pi Browser
3. افتح تطبيقك
4. غيّر **Hosting Type** من "Hosted by Pi" إلى **"Self-Hosted"**
5. الصق الرابط في:
   - **Development URL**: `https://your-app.vercel.app`
   - **Production URL**: `https://your-app.vercel.app`
6. احفظ التغييرات

## 📝 متغيرات البيئة (Environment Variables)

أضف هذه المتغيرات في Vercel Dashboard → Settings → Environment Variables:

```env
# Pi Network SDK
NEXT_PUBLIC_PI_APP_ID=your-pi-app-id
NEXT_PUBLIC_PI_API_KEY=your-pi-api-key
PI_API_SECRET=your-pi-api-secret

# App Config
NEXT_PUBLIC_APP_URL=https://your-app.vercel.app
```

## 🔒 الخصوصية والشروط

- [سياسة الخصوصية](/privacy)
- [شروط الاستخدام](/terms)

## 📄 الترخيص

MIT License - انظر ملف [LICENSE](LICENSE) للتفاصيل.

## 👨‍💻 المطور

تم تطويره بواسطة **Mirxou**

- GitHub: [@Mirxou](https://github.com/Mirxou)
- Repository: [Standard_El-joumla](https://github.com/Mirxou/Standard_El-joumla)

## 🆘 الدعم

إذا واجهت أي مشكلة، يرجى فتح [Issue](https://github.com/Mirxou/Standard_El-joumla/issues) على GitHub.

---

**⚠️ ملاحظة مهمة:** هذا التطبيق يتطلب استضافة خارجية (Self-Hosted) ولا يدعم خيار "Hosted by Pi" بسبب متطلبات Server-side.

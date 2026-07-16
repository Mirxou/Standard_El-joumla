# دليل المطور

## البدء

### المتطلبات
- Node.js 18+
- npm أو yarn

### التثبيت
```bash
npm install
```

### التشغيل
```bash
npm run dev
```

## البنية

```
web/
├── app/              # Next.js app directory
├── components/       # React components
├── lib/             # Utilities and helpers
│   ├── api/         # API client
│   ├── actions/     # Server actions
│   └── utils/       # Utility functions
├── __tests__/       # Tests
└── docs/            # Documentation
```

## Best Practices

### 1. استخدام API Client
دائماً استخدم `apiClient` من `@/lib/api/client`:

```typescript
import { apiClient } from '@/lib/api/client'
import { API_CONFIG } from '@/lib/config/api'

const data = await apiClient.get(API_CONFIG.ENDPOINTS.PRODUCTS)
```

### 2. Error Handling
استخدم try-catch مع toast notifications:

```typescript
try {
  await apiClient.post('/endpoint', data)
  toast.success('تم بنجاح')
} catch (error: any) {
  toast.error(error.message || 'حدث خطأ')
}
```

### 3. Type Safety
استخدم TypeScript types:

```typescript
import type { Product, Sale } from '@/lib/types'
```

### 4. Component Structure
```tsx
"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"

export default function MyComponent() {
  const [data, setData] = useState([])
  
  useEffect(() => {
    loadData()
  }, [])
  
  return <Card>...</Card>
}
```

## Testing

### Unit Tests
```bash
npm test
```

### E2E Tests
```bash
npm run test:e2e
```

## Code Style

- استخدام ESLint
- Prettier للـ formatting
- TypeScript strict mode


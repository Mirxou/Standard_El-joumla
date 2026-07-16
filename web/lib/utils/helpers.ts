/**
 * دوال مساعدة للتطبيق
 */

/**
 * تنسيق العملة السعودية
 */
export const formatCurrency = (amount: number, locale = 'ar-SA'): string => {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: 'SAR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
};

/**
 * تنسيق التاريخ بالعربية
 */
export const formatDateArabic = (date: string | Date, format: 'short' | 'long' = 'short'): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  const options: Intl.DateTimeFormatOptions = format === 'short'
    ? { year: 'numeric', month: '2-digit', day: '2-digit' }
    : { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' };
  
  return dateObj.toLocaleDateString('ar-SA', options);
};

/**
 * تنسيق الوقت بالعربية
 */
export const formatTimeArabic = (date: string | Date): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  return dateObj.toLocaleTimeString('ar-SA', { 
    hour: '2-digit', 
    minute: '2-digit',
    second: '2-digit'
  });
};

/**
 * التحقق من صحة البريد الإلكتروني
 */
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * التحقق من صحة الهاتف السعودي
 */
export const isValidPhoneSA = (phone: string): boolean => {
  const phoneRegex = /^(\+966|0)?[5][0-9]{8}$/;
  return phoneRegex.test(phone.replace(/\s/g, ''));
};

/**
 * حساب الفرق بين تاريخين بالأيام
 */
export const getDaysDifference = (date1: Date, date2: Date): number => {
  const oneDay = 24 * 60 * 60 * 1000;
  return Math.round(Math.abs((date1.getTime() - date2.getTime()) / oneDay));
};

/**
 * اختصار النص الطويل
 */
export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

/**
 * تحويل النص إلى رقم آمن
 */
export const safeParseNumber = (value: any, defaultValue = 0): number => {
  const parsed = Number(value);
  return isNaN(parsed) ? defaultValue : parsed;
};

/**
 * حساب النسبة المئوية
 */
export const calculatePercentage = (part: number, total: number): number => {
  if (total === 0) return 0;
  return (part / total) * 100;
};

/**
 * حساب الربح
 */
export const calculateProfit = (sellingPrice: number, costPrice: number): number => {
  return sellingPrice - costPrice;
};

/**
 * حساب نسبة الربح
 */
export const calculateProfitMargin = (profit: number, sellingPrice: number): number => {
  if (sellingPrice === 0) return 0;
  return (profit / sellingPrice) * 100;
};

/**
 * معالجة الأخطاء والحصول على رسالة آمنة
 */
export const getErrorMessage = (error: unknown): string => {
  if (error instanceof Error) {
    return error.message;
  }
  if (typeof error === 'string') {
    return error;
  }
  return 'حدث خطأ غير متوقع';
};

/**
 * تأخير غير متزامن
 */
export const delay = (ms: number): Promise<void> => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

/**
 * ترجمة الحالة إلى العربية
 */
export const translateStatus = (status: string): string => {
  const translations: Record<string, string> = {
    'active': 'نشط',
    'inactive': 'غير نشط',
    'pending': 'معلق',
    'completed': 'مكتمل',
    'cancelled': 'ملغي',
    'paid': 'مدفوع',
    'draft': 'مسودة',
    'archived': 'مؤرشف',
  };
  
  return translations[status.toLowerCase()] || status;
};

import {
  formatCurrency,
  formatDateArabic,
  formatTimeArabic,
  isValidEmail,
  isValidPhoneSA,
  getDaysDifference,
  truncateText,
  safeParseNumber,
  calculatePercentage,
  calculateProfit,
  calculateProfitMargin,
  getErrorMessage,
  delay,
  translateStatus,
} from '@/lib/utils/helpers'

describe('Helper Functions', () => {
  describe('formatCurrency', () => {
    it('should format currency correctly in Arabic', () => {
      const result = formatCurrency(1000)
      expect(result).toContain('١٬٠٠٠٫٠٠')
      expect(result).toContain('ر.س')
    })

    it('should format currency in English if specified', () => {
      const result = formatCurrency(1000, 'en-US')
      expect(result).toContain('SAR')
      expect(result).toContain('1,000.00')
    })

    it('should handle zero', () => {
      expect(formatCurrency(0)).toContain('٠٫٠٠')
    })

    it('should handle negative values', () => {
      const result = formatCurrency(-500)
      expect(result).toContain('٥٠٠٫٠٠')
      // Note: Arabic negative might be different depending on environment, we just check content
    })
  })

  describe('formatDateArabic', () => {
    const testDate = new Date('2025-01-15')

    it('should format date in short format (default)', () => {
      const result = formatDateArabic(testDate)
      expect(result).toContain('١٥‏/٠١‏/٢٠٢٥')
    })

    it('should format date in long format', () => {
      const result = formatDateArabic(testDate, 'long')
      expect(result).toContain('يناير')
      expect(result).toContain('الأربعاء')
      expect(result).toContain('٢٠٢٥')
    })

    it('should handle string dates', () => {
      const result = formatDateArabic('2025-01-15')
      expect(result).toContain('١٥‏/٠١‏/٢٠٢٥')
    })
  })

  describe('formatTimeArabic', () => {
    it('should format time correctly', () => {
      const date = new Date('2025-01-15T10:30:00')
      const result = formatTimeArabic(date)
      expect(result).toContain('١٠:٣٠:٠٠')
    })

    it('should handle string dates', () => {
      const result = formatTimeArabic('2025-01-15T10:30:00')
      expect(result).toContain('١٠:٣٠:٠٠')
    })
  })

  describe('isValidEmail', () => {
    it('should validate correct email', () => {
      expect(isValidEmail('test@example.com')).toBe(true)
    })

    it('should reject invalid emails', () => {
      expect(isValidEmail('invalid')).toBe(false)
      expect(isValidEmail('test@')).toBe(false)
      expect(isValidEmail('test@domain')).toBe(false)
      expect(isValidEmail('test@domain.')).toBe(false)
    })
  })

  describe('isValidPhoneSA', () => {
    it('should validate Saudi phone numbers', () => {
      expect(isValidPhoneSA('0501234567')).toBe(true)
      expect(isValidPhoneSA('+966501234567')).toBe(true)
      expect(isValidPhoneSA('501234567')).toBe(true)
    })

    it('should handle spaces in phone numbers', () => {
      expect(isValidPhoneSA('050 123 4567')).toBe(true)
    })

    it('should reject invalid numbers', () => {
      expect(isValidPhoneSA('123456789')).toBe(false) // No 5
      expect(isValidPhoneSA('050123456')).toBe(false) // Too short
      expect(isValidPhoneSA('05012345678')).toBe(false) // Too long
    })
  })

  describe('getDaysDifference', () => {
    it('should calculate difference between dates', () => {
      const d1 = new Date('2025-01-01')
      const d2 = new Date('2025-01-11')
      expect(getDaysDifference(d1, d2)).toBe(10)
    })

    it('should handle same date', () => {
      const d = new Date()
      expect(getDaysDifference(d, d)).toBe(0)
    })
  })

  describe('truncateText', () => {
    it('should truncate long text', () => {
      expect(truncateText('Hello World', 5)).toBe('Hello...')
    })

    it('should not truncate short text', () => {
      expect(truncateText('Hi', 5)).toBe('Hi')
    })
  })

  describe('safeParseNumber', () => {
    it('should parse valid numbers', () => {
      expect(safeParseNumber('123')).toBe(123)
      expect(safeParseNumber(123.45)).toBe(123.45)
    })

    it('should return default value for invalid input', () => {
      expect(safeParseNumber('abc')).toBe(0)
      expect(safeParseNumber(undefined, 10)).toBe(10)
      expect(safeParseNumber(null, 5)).toBe(0) // Number(null) is 0
    })
  })

  describe('calculatePercentage', () => {
    it('should calculate percentage correctly', () => {
      expect(calculatePercentage(50, 200)).toBe(25)
    })

    it('should handle zero total', () => {
      expect(calculatePercentage(50, 0)).toBe(0)
    })
  })

  describe('calculateProfit & calculateProfitMargin', () => {
    it('should calculate profit correctly', () => {
      expect(calculateProfit(150, 100)).toBe(50)
    })

    it('should calculate margin correctly', () => {
      expect(calculateProfitMargin(50, 200)).toBe(25)
    })

    it('should handle zero selling price in margin', () => {
      expect(calculateProfitMargin(50, 0)).toBe(0)
    })
  })

  describe('getErrorMessage', () => {
    it('should extract message from Error object', () => {
      expect(getErrorMessage(new Error('Test error'))).toBe('Test error')
    })

    it('should return string if error is string', () => {
      expect(getErrorMessage('Simple error')).toBe('Simple error')
    })

    it('should return default message for unknown type', () => {
      expect(getErrorMessage({ unknown: true })).toBe('حدث خطأ غير متوقع')
    })
  })

  describe('delay', () => {
    it('should resolve after specified time', async () => {
      const start = Date.now()
      await delay(100)
      const end = Date.now()
      expect(end - start).toBeGreaterThanOrEqual(100)
    })
  })

  describe('translateStatus', () => {
    it('should translate statuses to Arabic', () => {
      expect(translateStatus('active')).toBe('نشط')
      expect(translateStatus('COMPLETED')).toBe('مكتمل')
      expect(translateStatus('paid')).toBe('مدفوع')
    })

    it('should return original status if no translation exists', () => {
      expect(translateStatus('unknown_status')).toBe('unknown_status')
    })
  })

  describe('Edge Cases and Additional Tests', () => {
    describe('formatCurrency edge cases', () => {
      it('should handle large numbers', () => {
        const result = formatCurrency(999999999.99)
        expect(result).toContain('ر.س')
      })

      it('should handle very small numbers', () => {
        const result = formatCurrency(0.01)
        expect(result).toContain('ر.س')
      })

      it('should handle decimal precision', () => {
        const result = formatCurrency(123.456)
        expect(result).toContain('ر.س')
      })
    })

    describe('formatDateArabic edge cases', () => {
      it('should handle invalid date strings gracefully', () => {
        const result = formatDateArabic('invalid-date')
        expect(result).toBeTruthy()
      })

      it('should handle Date objects', () => {
        const date = new Date('2025-12-25')
        const result = formatDateArabic(date)
        expect(result).toContain('٢٥')
      })
    })

    describe('isValidEmail edge cases', () => {
      it('should handle empty strings', () => {
        expect(isValidEmail('')).toBe(false)
      })

      it('should handle spaces', () => {
        expect(isValidEmail('test @example.com')).toBe(false)
      })

      it('should handle multiple @ signs', () => {
        expect(isValidEmail('test@@example.com')).toBe(false)
      })

      it('should accept valid complex emails', () => {
        expect(isValidEmail('test.user+tag@example.co.uk')).toBe(true)
      })
    })

    describe('isValidPhoneSA edge cases', () => {
      it('should handle empty strings', () => {
        expect(isValidPhoneSA('')).toBe(false)
      })

      it('should handle non-numeric characters', () => {
        expect(isValidPhoneSA('050123abc')).toBe(false)
      })

      it('should handle international format with country code', () => {
        expect(isValidPhoneSA('+966501234567')).toBe(true)
      })
    })

    describe('getDaysDifference edge cases', () => {
      it('should handle dates in different months', () => {
        const d1 = new Date('2025-01-01')
        const d2 = new Date('2025-02-01')
        expect(getDaysDifference(d1, d2)).toBe(31)
      })

      it('should handle dates in different years', () => {
        const d1 = new Date('2024-12-31')
        const d2 = new Date('2025-01-01')
        expect(getDaysDifference(d1, d2)).toBe(1)
      })

      it('should handle reversed dates', () => {
        const d1 = new Date('2025-01-11')
        const d2 = new Date('2025-01-01')
        expect(getDaysDifference(d1, d2)).toBe(10)
      })
    })

    describe('truncateText edge cases', () => {
      it('should handle empty strings', () => {
        expect(truncateText('', 5)).toBe('')
      })

      it('should handle zero maxLength', () => {
        expect(truncateText('Hello', 0)).toBe('...')
      })

      it('should handle exact length match', () => {
        expect(truncateText('Hello', 5)).toBe('Hello')
      })
    })

    describe('safeParseNumber edge cases', () => {
      it('should handle empty strings', () => {
        expect(safeParseNumber('')).toBe(0)
      })

      it('should handle boolean values', () => {
        expect(safeParseNumber(true)).toBe(1)
        expect(safeParseNumber(false)).toBe(0)
      })

      it('should handle arrays', () => {
        expect(safeParseNumber([1, 2, 3])).toBe(0)
      })

      it('should handle objects', () => {
        expect(safeParseNumber({})).toBe(0)
      })

      it('should use custom default value', () => {
        expect(safeParseNumber('invalid', 999)).toBe(999)
      })
    })

    describe('calculatePercentage edge cases', () => {
      it('should handle negative values', () => {
        expect(calculatePercentage(-50, 200)).toBe(-25)
      })

      it('should handle part greater than total', () => {
        expect(calculatePercentage(300, 200)).toBe(150)
      })

      it('should handle very small numbers', () => {
        expect(calculatePercentage(0.1, 100)).toBe(0.1)
      })
    })

    describe('calculateProfit edge cases', () => {
      it('should handle negative profit (loss)', () => {
        expect(calculateProfit(100, 150)).toBe(-50)
      })

      it('should handle zero cost price', () => {
        expect(calculateProfit(100, 0)).toBe(100)
      })

      it('should handle zero selling price', () => {
        expect(calculateProfit(0, 100)).toBe(-100)
      })
    })

    describe('calculateProfitMargin edge cases', () => {
      it('should handle negative profit', () => {
        expect(calculateProfitMargin(-50, 200)).toBe(-25)
      })

      it('should handle very large margins', () => {
        expect(calculateProfitMargin(1000, 100)).toBe(1000)
      })
    })

    describe('getErrorMessage edge cases', () => {
      it('should handle null', () => {
        expect(getErrorMessage(null)).toBe('حدث خطأ غير متوقع')
      })

      it('should handle undefined', () => {
        expect(getErrorMessage(undefined)).toBe('حدث خطأ غير متوقع')
      })

      it('should handle Error with custom message', () => {
        const error = new Error('Custom error message')
        expect(getErrorMessage(error)).toBe('Custom error message')
      })

      it('should handle Error objects without message', () => {
        const error = new Error()
        expect(getErrorMessage(error)).toBe('')
      })
    })

    describe('delay edge cases', () => {
      it('should handle zero delay', async () => {
        const start = Date.now()
        await delay(0)
        const end = Date.now()
        expect(end - start).toBeLessThan(10)
      })
    })
  })
})

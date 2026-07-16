# Test Suite Guide

## Quick Start

### Run All Tests
```bash
npm test
```

### Run Tests in Watch Mode
```bash
npm run test:watch
```

### Generate Coverage Report
```bash
npm run test:coverage
```

### Run Tests in CI Mode
```bash
npm run test:ci
```

---

## Test Structure

```
__tests__/
├── api/
│   └── routes.test.ts              # API endpoint tests
├── components/
│   └── rendering.test.tsx          # Component rendering tests
├── integration/
│   └── comprehensive.test.ts       # End-to-end integration tests
└── lib/
    ├── auth/
    │   └── index.test.ts           # Authentication tests
    ├── config/
    │   └── api.test.ts             # API configuration tests
    ├── hooks/
    │   ├── useAPI.test.ts          # Custom hook tests
    │   └── useAPI.corrected.test.ts # Enhanced hook tests
    ├── types/
    │   ├── index.test.ts           # Type definition tests
    │   └── types.corrected.test.ts # Enhanced type tests
    ├── utils/
    │   └── helpers.test.ts         # Utility function tests
    └── validation/
        └── index.test.ts           # Validation logic tests
```

---

## Test Files

### 1. API Tests (`api/routes.test.ts`) - 25 tests ✅
Tests for API route handlers, validation, and error handling.

**Key Tests:**
- Health check endpoints
- Stock optimization calculations
- ABC analysis reporting
- Error handling and validation
- Response format compliance

**Run single file:**
```bash
npm test -- __tests__/api/routes.test.ts
```

---

### 2. Component Tests (`components/rendering.test.tsx`) - 6 tests ✅
Tests for React component rendering and DOM queries.

**Key Tests:**
- Component rendering without errors
- Props handling
- DOM element selection
- ARIA attributes

**Run single file:**
```bash
npm test -- __tests__/components/rendering.test.tsx
```

---

### 3. Integration Tests (`integration/comprehensive.test.ts`) - 19 tests ✅
End-to-end testing of multiple components working together.

**Key Tests:**
- Complete CRUD operations
- Batch operations
- Pagination logic
- Data transformation
- Business calculations
- Error scenarios

**Run single file:**
```bash
npm test -- __tests__/integration/comprehensive.test.ts
```

---

### 4. Auth Tests (`lib/auth/index.test.ts`) - 22 tests ✅
Authentication and authorization logic.

**Key Tests:**
- Token storage and retrieval
- Token validation
- User authentication
- Authorization checks
- Session management
- Password handling

**Run single file:**
```bash
npm test -- __tests__/lib/auth/index.test.ts
```

---

### 5. Config Tests (`lib/config/api.test.ts`) - 14 tests ✅
API configuration and settings.

**Key Tests:**
- Configuration defaults
- Timeout settings
- Headers configuration
- Retry logic
- Base URL handling
- Error configuration

**Run single file:**
```bash
npm test -- __tests__/lib/config/api.test.ts
```

---

### 6. Hook Tests (`lib/hooks/useAPI.test.ts`) - 10 tests ✅
Custom React hooks for API operations.

**Key Tests:**
- Hook initialization
- Loading state
- Error handling
- Refetch functionality
- Mutation operations
- Reset functionality

**Run single file:**
```bash
npm test -- __tests__/lib/hooks/useAPI.test.ts
```

---

### 7. Type Tests (`lib/types/index.test.ts`) - 14 tests ✅
TypeScript type definitions validation.

**Key Tests:**
- User type structure
- Company type structure
- Product type structure
- Invoice type structure
- Sale type structure
- Type safety

**Run single file:**
```bash
npm test -- __tests__/lib/types/index.test.ts
```

---

### 8. Utils Tests (`lib/utils/helpers.test.ts`) - 12 tests ✅
Utility function testing.

**Key Tests:**
- Currency formatting
- Date formatting (Arabic)
- Time formatting (Arabic)
- Email validation
- Phone number validation (Saudi)
- Profit calculations
- Percentage calculations
- Text truncation

**Run single file:**
```bash
npm test -- __tests__/lib/utils/helpers.test.ts
```

---

### 9. Validation Tests (`lib/validation/index.test.ts`) - 18 tests ✅
Input validation logic.

**Key Tests:**
- String validation
- Number validation
- Date validation
- Array validation
- Object validation
- Complex validation rules
- Custom validators
- Error messages

**Run single file:**
```bash
npm test -- __tests__/lib/validation/index.test.ts
```

---

## Coverage Report

### Current Coverage
```
Statements:  15.26%
Branches:    9.25%
Functions:   22.03%
Lines:       13.86%
```

### View HTML Report
After running `npm run test:coverage`, open:
```
coverage/lcov-report/index.html
```

### Coverage by File
```
lib/config/api.ts         - 81.25% ✅ EXCELLENT
lib/hooks/useAPI.ts       - 56%    ✅ GOOD
lib/utils/helpers.ts      - 13.82% 🟡 NEEDS WORK
lib/api/client.ts         - 0%     ❌ UNTESTED
lib/actions/*             - 0%     ❌ UNTESTED
lib/ai/*                  - 0%     ❌ UNTESTED
components/*              - 0%     ❌ UNTESTED (except rendering)
```

---

## Writing New Tests

### Test Template

```typescript
import { test, expect } from '@jest/globals'

describe('Feature Name', () => {
  describe('Subfeature', () => {
    it('should do something', () => {
      // Arrange
      const input = 'test'
      
      // Act
      const result = myFunction(input)
      
      // Assert
      expect(result).toBe('expected')
    })
  })
})
```

### Testing Utilities

**For Components:**
```typescript
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

render(<MyComponent />)
screen.getByText('text')
userEvent.click(button)
```

**For Hooks:**
```typescript
import { renderHook, waitFor, act } from '@testing-library/react'

const { result } = renderHook(() => useMyHook())
await waitFor(() => expect(result.current.ready).toBe(true))
act(() => result.current.doSomething())
```

**For Async:**
```typescript
it('should handle async', async () => {
  const result = await asyncFunction()
  expect(result).toBeDefined()
})
```

---

## Common Issues & Solutions

### Issue: "localStorage is not defined"
**Solution:** localStorage mock is configured in jest.setup.js

### Issue: "Cannot find module '@/...'"
**Solution:** Path aliases are configured in jest.config.js

### Issue: "act() warning"
**Solution:** Wrap state updates in act():
```typescript
act(() => {
  component.setState({ ... })
})
```

### Issue: "Headers API error"
**Solution:** Some tests use jsdom which has issues with Headers API. These are noted in jest.config.js and can be fixed with node test environment for API tests.

---

## Best Practices

✅ **DO:**
- Write clear, descriptive test names
- Test one thing per test
- Use arrange-act-assert pattern
- Mock external dependencies
- Test error scenarios
- Use meaningful assertions
- Keep tests fast and isolated

❌ **DON'T:**
- Write overly complex tests
- Test implementation details
- Make tests dependent on each other
- Use hardcoded values in assertions
- Skip error tests
- Test third-party libraries
- Make tests slow (>100ms each)

---

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run Tests
  run: npm run test:ci

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage/coverage-final.json
```

---

## Coverage Goals

| Target | Current | Status |
|--------|---------|--------|
| Statements | 15.26% | 🔴 Low |
| Branches | 9.25% | 🔴 Low |
| Functions | 22.03% | 🟡 Fair |
| Lines | 13.86% | 🔴 Low |

### Next Steps
1. Complete Phase 1: Helper functions (+10%)
2. Complete Phase 2: API layer (+12%)
3. Complete Phase 3: Components (+10%)
4. Complete Phase 4: Actions & AI (+8%)
5. **Target:** 95% overall coverage

See [COVERAGE_95_ROADMAP.md](COVERAGE_95_ROADMAP.md) for detailed plan.

---

## Resources

- [Jest Documentation](https://jestjs.io/)
- [Testing Library Docs](https://testing-library.com/)
- [Next.js Testing Guide](https://nextjs.org/docs/testing)
- [TypeScript Jest](https://jest.io/docs/getting-started#using-typescript)

---

## Need Help?

1. Check existing tests for patterns
2. Read test comments for explanations
3. Review error messages carefully
4. Check jest.setup.js for available mocks
5. Run tests in watch mode to debug

---

**Last Updated:** January 2025
**Status:** ✅ All 156 tests passing
**Next Milestone:** 95% coverage (12-14 hours estimated)

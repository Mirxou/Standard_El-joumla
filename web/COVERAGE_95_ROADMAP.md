# 95% Coverage Roadmap

## Current Status
- **Tests:** 156 passing ✅
- **Coverage:** 15.26% statements
- **Target:** 95% coverage

## Coverage Gaps

### Fully Untested Files (0%)

#### API Layer
- `lib/api/client.ts` - API HTTP client (Headers API conflicts, needs mocking)
- Total lines: ~260

#### Components
- `components/hydration.tsx` - 31 lines
- `components/inventory-helpers.tsx` - 174 lines
- `components/pdf-generator.ts` - 291 lines
- Total: ~496 lines

#### Actions & Services
- `lib/actions/*` - All action creators
- `lib/ai/*` - AI/ML functions
- `app/api/*` - API routes
- `lib/store/*` - State management

### Partially Tested Files (< 50%)

- `lib/hooks/useAPI.ts` - 56% (improve to 90%+)
- `lib/utils/helpers.ts` - 13.82% (improve to 80%+)

## Phase-by-Phase Plan

### Phase 1: Fix Existing Coverage (2 hours)
**Goal:** Improve partially tested files to 80%+

1. **Enhance lib/hooks/useAPI.ts** (45 min)
   - Add 15+ tests for edge cases
   - Test error scenarios
   - Test abort/cleanup
   - Test retry logic
   - Target: 90%

2. **Enhance lib/utils/helpers.ts** (45 min)
   - Add 20+ tests for all utilities
   - Test Arabic formatting edge cases
   - Test validation patterns
   - Test edge cases (nulls, empty strings, large numbers)
   - Target: 85%

**Expected gain:** 5-8% coverage

### Phase 2: API Layer Tests (3 hours)
**Goal:** Test API client and routes

1. **lib/api/client.ts** (90 min)
   - Fix Headers mock for jsdom
   - Test all HTTP methods (GET, POST, PUT, DELETE)
   - Test error handling
   - Test retry logic
   - Test timeout
   - Add 40+ tests
   - Target: 85%

2. **app/api/** routes (90 min)
   - Test all route handlers
   - Test parameter validation
   - Test error responses
   - Test authentication/authorization
   - Add 50+ tests
   - Target: 90%

**Expected gain:** 8-12% coverage

### Phase 3: Component Tests (2.5 hours)
**Goal:** Test React components

1. **components/hydration.tsx** (30 min)
   - Test render without errors
   - Test with different props
   - Test loading/error states
   - Target: 90%

2. **components/inventory-helpers.tsx** (60 min)
   - Test all helpers
   - Test data transformations
   - Test edge cases
   - Target: 85%

3. **components/pdf-generator.ts** (90 min)
   - Test PDF generation
   - Test template rendering
   - Test data formatting
   - Target: 80%

**Expected gain:** 8-10% coverage

### Phase 4: AI/ML & Actions (2 hours)
**Goal:** Test remaining critical functions

1. **lib/ai/** (60 min)
   - Test anomaly detection
   - Test forecasting
   - Test data processing
   - Add 25+ tests

2. **lib/actions/** (60 min)
   - Test all action creators
   - Test state mutations
   - Test side effects
   - Add 30+ tests

**Expected gain:** 5-7% coverage

## Implementation Order

**Week 1:**
- [ ] Phase 1.1: useAPI tests (45 min)
- [ ] Phase 1.2: helpers tests (45 min)
- [ ] Phase 2.1: client.ts tests (90 min)
- [ ] Phase 2.2: api routes tests (90 min)

**Week 2:**
- [ ] Phase 3.1: hydration component (30 min)
- [ ] Phase 3.2: inventory-helpers (60 min)
- [ ] Phase 3.3: pdf-generator (90 min)
- [ ] Phase 4: AI & Actions (120 min)

## Test File Structure

```
__tests__/
├── lib/
│   ├── api/
│   │   ├── client.test.ts (new - 40 tests)
│   │   └── handlers.test.ts (new - 50 tests)
│   ├── hooks/
│   │   ├── useAPI.test.ts (update +15 tests)
│   │   └── useAPI.corrected.test.ts (keep)
│   ├── utils/
│   │   └── helpers.test.ts (update +20 tests)
│   ├── actions/
│   │   └── index.test.ts (new - 30 tests)
│   └── ai/
│       └── index.test.ts (new - 25 tests)
├── components/
│   ├── hydration.test.tsx (new - 8 tests)
│   ├── inventory-helpers.test.ts (new - 20 tests)
│   └── pdf-generator.test.ts (new - 15 tests)
└── app/
    └── api/
        └── routes.test.ts (new - 50 tests)
```

## Coverage Target Breakdown

| Layer | Current | Target | Gap | Tests Needed |
|-------|---------|--------|-----|--------------|
| Hooks | 56% | 90% | +34% | 15 |
| Utils | 13.82% | 85% | +71% | 20 |
| API | 0% | 85% | +85% | 90 |
| Components | 0% | 80% | +80% | 43 |
| Actions | 0% | 90% | +90% | 30 |
| AI | 0% | 90% | +90% | 25 |
| Config | 81.25% | 95% | +13.75% | 5 |
| Auth | 100% | 100% | 0% | 0 |
| Validation | 100% | 100% | 0% | 0 |
| **TOTAL** | **15.26%** | **95%** | **+79.74%** | **228** |

## Success Criteria

✅ All 156 existing tests passing
✅ 228+ new tests added
✅ Overall coverage ≥ 95%
✅ All critical paths tested
✅ Error scenarios covered
✅ Edge cases handled
✅ No regressions

## Timeline
- **Start:** NOW
- **Phase 1:** 2 hours → 20-25% coverage
- **Phase 2:** 3 hours → 30-37% coverage
- **Phase 3:** 2.5 hours → 38-47% coverage
- **Phase 4:** 2 hours → 43-54% coverage
- **Buffer:** 3-4 hours for final adjustments and fixes
- **Total:** ~12-14 hours to reach 95% coverage

## Notes

- Headers API issue with jsdom needs workaround (use node test environment for API tests)
- PDF generation testing may need snapshot tests
- AI functions may benefit from property-based testing
- Consider using faker.js for generating test data
- Use @testing-library/user-event for component interaction tests

## Resources

- Jest Documentation: https://jestjs.io/
- Testing Library: https://testing-library.com/
- Next.js Testing: https://nextjs.org/docs/testing
- Coverage Tools: https://istanbul.js.org/

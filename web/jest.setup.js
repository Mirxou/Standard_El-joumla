import '@testing-library/jest-dom'

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      push: jest.fn(),
      replace: jest.fn(),
      back: jest.fn(),
      forward: jest.fn(),
      refresh: jest.fn(),
      prefetch: jest.fn(),
    }
  },
  usePathname() {
    return '/'
  },
  useSearchParams() {
    return new URLSearchParams()
  },
  useParams() {
    return {}
  },
}))

// Mock next/headers
jest.mock('next/headers', () => ({
  cookies: jest.fn(() => ({
    get: jest.fn(),
    set: jest.fn(),
    delete: jest.fn(),
  })),
  headers: jest.fn(() => ({
    get: jest.fn(),
  })),
}))

// Mock localStorage with real implementation
const localStorageStore = {}

const localStorageMock = {
  getItem: (key) => localStorageStore[key] || null,
  setItem: (key, value) => {
    localStorageStore[key] = String(value)
  },
  removeItem: (key) => {
    delete localStorageStore[key]
  },
  clear: () => {
    Object.keys(localStorageStore).forEach(key => delete localStorageStore[key])
  },
  key: (index) => {
    const keys = Object.keys(localStorageStore)
    return keys[index] || null
  },
  get length() {
    return Object.keys(localStorageStore).length
  },
}

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true,
})

// Also mock axios if needed
jest.mock('axios', () => ({
  create: jest.fn(() => ({
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    request: jest.fn(),
  })),
  default: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  },
}))

// Mock axios
jest.mock('axios', () => ({
  create: jest.fn(() => ({
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    request: jest.fn(),
  })),
  default: {
    create: jest.fn(() => ({
      get: jest.fn(),
      post: jest.fn(),
      put: jest.fn(),
      delete: jest.fn(),
      request: jest.fn(),
    })),
  },
}))


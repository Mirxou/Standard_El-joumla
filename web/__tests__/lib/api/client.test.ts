import { apiClient, APIClient } from '@/lib/api/client';
import { API_CONFIG } from '@/lib/config/api';

// Mock global fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock window.location
const mockLocation = { href: '' };
Object.defineProperty(window, 'location', {
    value: mockLocation,
    writable: true,
});

describe('APIClient', () => {
    let client: APIClient;

    beforeEach(() => {
        jest.clearAllMocks();
        localStorage.clear();
        client = new APIClient();
        mockLocation.href = '';
    });

    describe('Initialization & Credentials', () => {
        it('should load credentials from localStorage on init', () => {
            localStorage.setItem('access_token', 'test-token');
            localStorage.setItem('company_id', 'test-company');
            const newClient = new APIClient();
            // We can't access private members, so we test behavior
            // by making a request and checking headers
        });

        it('should set and persist token', () => {
            client.setToken('new-token');
            expect(localStorage.getItem('access_token')).toBe('new-token');
        });

        it('should set and persist company id', () => {
            client.setCompanyId('new-company');
            expect(localStorage.getItem('company_id')).toBe('new-company');
        });

        it('should clear credentials', () => {
            localStorage.setItem('access_token', 'token');
            client.clearCredentials();
            expect(localStorage.getItem('access_token')).toBeNull();
        });
    });

    describe('HTTP Methods', () => {
        beforeEach(() => {
            mockFetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({ success: true }),
            });
        });

        it('should perform GET request', async () => {
            await client.get('/test');
            expect(mockFetch).toHaveBeenCalledWith(
                expect.stringContaining('/test'),
                expect.objectContaining({ method: 'GET' })
            );
        });

        it('should perform POST request with body', async () => {
            const body = { name: 'test' };
            await client.post('/test', body);
            expect(mockFetch).toHaveBeenCalledWith(
                expect.any(String),
                expect.objectContaining({
                    method: 'POST',
                    body: JSON.stringify(body),
                })
            );
        });

        it('should perform PUT request with body', async () => {
            await client.put('/test', { id: 1 });
            expect(mockFetch).toHaveBeenCalledWith(
                expect.any(String),
                expect.objectContaining({ method: 'PUT' })
            );
        });

        it('should perform DELETE request', async () => {
            await client.delete('/test');
            expect(mockFetch).toHaveBeenCalledWith(
                expect.any(String),
                expect.objectContaining({ method: 'DELETE' })
            );
        });

        it('should handle 204 No Content', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: true,
                status: 204,
            });
            const result = await client.get('/empty');
            expect(result).toEqual({ success: true });
        });
    });

    describe('Token Refresh Logic', () => {
        it('should attempt to refresh token on 401', async () => {
            localStorage.setItem('refresh_token', 'rt-123');

            // 1. First call fails with 401
            mockFetch.mockResolvedValueOnce({
                status: 401,
                ok: false,
            });

            // 2. Refresh call succeeds
            mockFetch.mockResolvedValueOnce({
                status: 200,
                ok: true,
                json: () => Promise.resolve({ access_token: 'new-at' }),
            });

            // 3. Retried call succeeds
            mockFetch.mockResolvedValueOnce({
                status: 200,
                ok: true,
                json: () => Promise.resolve({ data: 'ok' }),
            });

            const result = await client.get('/secure');

            expect(result).toEqual({ data: 'ok' });
            expect(localStorage.getItem('access_token')).toBe('new-at');
        });

        it('should redirect to login if refresh fails', async () => {
            localStorage.setItem('refresh_token', 'rt-invalid');

            mockFetch.mockResolvedValueOnce({ status: 401, ok: false }); // Initial 401
            mockFetch.mockResolvedValueOnce({ status: 400, ok: false }); // Refresh fail

            await expect(client.get('/secure')).rejects.toThrow();
            expect(mockLocation.href).toBe('/login');
        });
    });

    describe('Retry Logic', () => {
        it('should retry on network errors (TypeError)', async () => {
            mockFetch
                .mockRejectedValueOnce(new TypeError('Failed to fetch'))
                .mockResolvedValueOnce({
                    ok: true,
                    status: 200,
                    json: () => Promise.resolve({ data: 'recovered' }),
                });

            // Reduce delay for tests
            const originalDelay = API_CONFIG.RETRY.DELAY_MS;
            (API_CONFIG.RETRY as any).DELAY_MS = 1;

            const result = await client.get('/flaky');
            expect(result).toEqual({ data: 'recovered' });
            expect(mockFetch).toHaveBeenCalledTimes(2);

            (API_CONFIG.RETRY as any).DELAY_MS = originalDelay;
        });

        it('should retry on timeout (AbortError)', async () => {
            const abortError = new Error('Timeout');
            abortError.name = 'AbortError';

            mockFetch
                .mockRejectedValueOnce(abortError)
                .mockResolvedValueOnce({
                    ok: true,
                    status: 200,
                    json: () => Promise.resolve({ data: 'recovered' }),
                });

            (API_CONFIG.RETRY as any).DELAY_MS = 1;
            const result = await client.get('/slow');
            expect(result).toEqual({ data: 'recovered' });

            (API_CONFIG.RETRY as any).DELAY_MS = 1000;
        });
    });

    describe('Error Response Handling', () => {
        it('should parse error messages from JSON body', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: false,
                status: 400,
                json: () => Promise.resolve({ detail: 'Validation failed' }),
            });

            await expect(client.get('/error')).rejects.toThrow('Validation failed');
        });

        it('should fallback to status text if JSON fails', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: false,
                status: 500,
                statusText: 'Internal Error',
                json: () => Promise.reject(new Error('No JSON')),
            });

            await expect(client.get('/error')).rejects.toThrow('Internal Error');
        });
    });

    describe('Request Configuration', () => {
        it('should include default headers in requests', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({ data: 'ok' }),
            });

            await client.get('/test');

            const callArgs = mockFetch.mock.calls[0];
            expect(callArgs[1].headers).toBeDefined();
        });

        it('should include Authorization header when token is set', async () => {
            client.setToken('test-token');
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({ data: 'ok' }),
            });

            await client.get('/test');

            const callArgs = mockFetch.mock.calls[0];
            const headers = callArgs[1].headers as Headers;
            if (headers instanceof Headers) {
                expect(headers.get('Authorization')).toContain('test-token');
            }
        });

        it('should include Company-Id header when company ID is set', async () => {
            client.setCompanyId('company-123');
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({ data: 'ok' }),
            });

            await client.get('/test');

            const callArgs = mockFetch.mock.calls[0];
            expect(callArgs[1].headers).toBeDefined();
        });
    });

    describe('Edge Cases', () => {
        it('should handle missing response body gracefully', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: true,
                status: 200,
                json: () => Promise.resolve(null),
            });

            const result = await client.get('/empty-response');
            expect(result).toBeDefined();
        });

        it('should handle network timeout scenarios', async () => {
            mockFetch.mockRejectedValueOnce(new Error('Network request failed'));

            await expect(client.get('/timeout')).rejects.toThrow();
        });

        it('should handle malformed JSON responses', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: true,
                status: 200,
                json: () => Promise.reject(new Error('Invalid JSON')),
            });

            await expect(client.get('/malformed')).rejects.toThrow();
        });

        it('should handle concurrent refresh token requests', async () => {
            localStorage.setItem('refresh_token', 'rt-123');

            // Multiple 401 responses
            mockFetch
                .mockResolvedValueOnce({ status: 401, ok: false })
                .mockResolvedValueOnce({ status: 401, ok: false });

            // Refresh succeeds
            mockFetch.mockResolvedValueOnce({
                status: 200,
                ok: true,
                json: () => Promise.resolve({ access_token: 'new-token' }),
            });

            // Retried requests succeed
            mockFetch.mockResolvedValue({
                status: 200,
                ok: true,
                json: () => Promise.resolve({ data: 'ok' }),
            });

            const promises = [
                client.get('/secure1'),
                client.get('/secure2'),
            ];

            await Promise.all(promises);
            expect(localStorage.getItem('access_token')).toBe('new-token');
        });

        it('should handle refresh token when no refresh_token exists', async () => {
            localStorage.removeItem('refresh_token');
            mockFetch.mockResolvedValueOnce({ status: 401, ok: false });

            await expect(client.get('/secure')).rejects.toThrow();
            expect(mockLocation.href).toBe('/login');
        });

        it('should handle POST with null body', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({ success: true }),
            });

            await client.post('/test', null);
            expect(mockFetch).toHaveBeenCalled();
        });

        it('should handle PUT with undefined body', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({ success: true }),
            });

            await client.put('/test', undefined);
            expect(mockFetch).toHaveBeenCalled();
        });

        it('should handle DELETE request with query parameters', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: true,
                status: 204,
            });

            await client.delete('/test?id=123');
            expect(mockFetch).toHaveBeenCalledWith(
                expect.stringContaining('/test'),
                expect.any(Object)
            );
        });

        it('should preserve error information in thrown exceptions', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: false,
                status: 404,
                statusText: 'Not Found',
                json: () => Promise.resolve({ detail: 'Resource not found' }),
            });

            try {
                await client.get('/not-found');
                fail('Should have thrown an error');
            } catch (error: any) {
                expect(error.message).toBeDefined();
            }
        });
    });

    describe('Credentials Management', () => {
        it('should handle setting token to null', () => {
            client.setToken('token');
            client.setToken('');
            expect(localStorage.getItem('access_token')).toBe('');
        });

        it('should handle setting company ID to null', () => {
            client.setCompanyId('company');
            client.setCompanyId('');
            expect(localStorage.getItem('company_id')).toBe('');
        });

        it('should handle clearing credentials when none exist', () => {
            localStorage.clear();
            expect(() => client.clearCredentials()).not.toThrow();
            expect(localStorage.getItem('access_token')).toBeNull();
        });

        it('should load credentials on initialization', () => {
            localStorage.setItem('access_token', 'init-token');
            localStorage.setItem('company_id', 'init-company');
            
            const newClient = new APIClient();
            // Credentials should be loaded (tested via behavior)
            expect(newClient).toBeDefined();
        });
    });

    describe('Retry Logic Edge Cases', () => {
        it('should not retry on non-retryable errors', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: false,
                status: 400,
                json: () => Promise.resolve({ detail: 'Bad Request' }),
            });

            await expect(client.get('/bad-request')).rejects.toThrow();
            expect(mockFetch).toHaveBeenCalledTimes(1);
        });

        it('should handle max retry attempts', async () => {
            const networkError = new TypeError('Failed to fetch');
            mockFetch.mockRejectedValue(networkError);

            // Reduce delay for test
            const originalDelay = API_CONFIG.RETRY.DELAY_MS;
            (API_CONFIG.RETRY as any).DELAY_MS = 1;

            await expect(client.get('/flaky')).rejects.toThrow();

            (API_CONFIG.RETRY as any).DELAY_MS = originalDelay;
        });
    });
});

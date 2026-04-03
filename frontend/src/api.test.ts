import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import { requestOtp, getProjects, ApiError } from './api';

describe('api.ts', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  it('apiFetch sets correct headers and credentials', async () => {
    const mockResponse = {
      ok: true,
      status: 200,
      text: () => Promise.resolve(JSON.stringify({ message: 'Success' })),
    };
    (fetch as Mock).mockResolvedValue(mockResponse);

    await requestOtp('test@tul.cz');

    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/auth/otp/request'),
      expect.objectContaining({
        method: 'POST',
        credentials: 'include',
        headers: expect.any(Headers),
      })
    );
    
    const headers = (vi.mocked(fetch).mock.calls[0][1]?.headers as Headers);
    expect(headers.get('Content-Type')).toBe('application/json');
  });

  it('throws ApiError on non-2xx response', async () => {
    const mockResponse = {
      ok: false,
      status: 401,
      text: () => Promise.resolve(JSON.stringify({ detail: 'Unauthorized' })),
    };
    (fetch as Mock).mockResolvedValue(mockResponse);

    await expect(getProjects()).rejects.toThrow(ApiError);
  });

  it('getProjects builds query string correctly', async () => {
    const mockResponse = {
      ok: true,
      status: 200,
      text: () => Promise.resolve('[]'),
    };
    (fetch as Mock).mockResolvedValue(mockResponse);

    await getProjects({ q: 'test', year: 2023 });

    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/projects?q=test&year=2023'),
      expect.anything()
    );
  });
});

import { afterEach, describe, expect, it, vi } from 'vitest';
import { api } from '../services/api';

afterEach(() => { vi.unstubAllGlobals(); });

describe('upload API client', () => {
  it('posts one multipart file to the canonical endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ is_duplicate: false }) });
    vi.stubGlobal('fetch', fetchMock);
    const file = new File(['%PDF-1.7'], 'paper.pdf', { type: 'application/pdf' });
    await api.uploadDocument(file);
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/v1\/documents$/);
    expect(options.method).toBe('POST');
    expect(options.body.get('file')).toBe(file);
    expect(options.headers['Content-Type']).toBeUndefined();
  });

  it('surfaces the server failure', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 503, json: async () => ({ detail: 'Document storage temporarily unavailable' }) }));
    await expect(api.uploadDocument(new File(['pdf'], 'paper.pdf', { type: 'application/pdf' }))).rejects.toMatchObject({ status: 503, message: 'Document storage temporarily unavailable' });
  });

  it('rejects invalid, empty and oversized files before sending', async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
    await expect(api.uploadDocument(new File(['x'], 'wrong.txt', { type: 'application/pdf' }))).rejects.toMatchObject({ status: 400 });
    await expect(api.uploadDocument(new File([], 'empty.pdf', { type: 'application/pdf' }))).rejects.toMatchObject({ status: 400 });
    const large = new File(['x'], 'large.pdf', { type: 'application/pdf' });
    Object.defineProperty(large, 'size', { value: 26 * 1024 * 1024 });
    await expect(api.uploadDocument(large)).rejects.toMatchObject({ status: 413 });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('accepts a PDF with no browser MIME and preserves duplicate responses', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ is_duplicate: true }) }));
    expect(await api.uploadDocument(new File(['pdf'], 'paper.pdf'))).toMatchObject({ is_duplicate: true });
  });
});


it('deletes the canonical document and accepts the empty 204 response without parsing JSON', async () => {
  const json = vi.fn().mockRejectedValue(new Error('204 has no body'));
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 204, json });
  vi.stubGlobal('fetch', fetchMock);
  await expect(api.deleteDocument('507f1f77bcf86cd799439011')).resolves.toBeUndefined();
  expect(fetchMock).toHaveBeenCalledWith(expect.stringMatching(/\/documents\/507f1f77bcf86cd799439011$/), expect.objectContaining({ method: 'DELETE' }));
  expect(json).not.toHaveBeenCalled();
  await expect(api.deleteDocument('invalid')).rejects.toThrow();
  expect(fetchMock).toHaveBeenCalledTimes(1);
});

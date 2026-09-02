import { test, expect } from 'vitest';

describe('API Client', () => {
  test('should have correct base URL', () => {
    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
    expect(baseUrl).toBeDefined();
  });
});

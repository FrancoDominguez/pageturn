const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

async function apiFetch<T>(
  path: string,
  options?: RequestInit & { params?: Record<string, string | undefined> }
): Promise<T> {
  const { params, ...fetchOptions } = options || {};

  let url = `${API_BASE}${path}`;
  if (params) {
    const searchParams = new URLSearchParams(
      Object.entries(params).filter((entry): entry is [string, string] => entry[1] != null)
    );
    const qs = searchParams.toString();
    if (qs) url += `?${qs}`;
  }

  // Get Clerk token
  const token = await window.Clerk?.session?.getToken();

  const response = await fetch(url, {
    ...fetchOptions,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...fetchOptions?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new ApiError(response.status, error.detail || 'Unknown error');
  }

  return response.json();
}

export { apiFetch, ApiError };

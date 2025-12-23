// frontend/src/lib/api.ts
import { z } from 'zod';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Base options without body, as body is handled differently by methods
type BaseApiOptions = {
  headers?: Record<string, string>;
  params?: Record<string, string | number>;
};

// Options for methods that can have a body
type BodyApiOptions = BaseApiOptions & {
  body?: any;
};

/**
 * Canonical API Error
 *
 * Extracts error information from AEQ error envelope:
 * {
 *   "error": {
 *     "code": "AEQ_JOURNAL_IMBALANCE",
 *     "message": "Journal entry is not balanced...",
 *     "details": {...},
 *     "request_id": "...",
 *     "correlation_id": "..."
 *   }
 * }
 */
class ApiError extends Error {
  status: number;
  code: string;
  details: any;
  requestId?: string;
  correlationId?: string;

  constructor(message: string, status: number, errorData: any) {
    // If errorData has canonical error envelope, extract it
    if (errorData && typeof errorData === 'object' && errorData.error) {
      const error = errorData.error;
      super(error.message || message);
      this.code = error.code || `HTTP_${status}`;
      this.details = error.details || {};
      this.requestId = error.request_id;
      this.correlationId = error.correlation_id;
    } else {
      // Fallback for non-canonical errors
      super(message);
      this.code = `HTTP_${status}`;
      this.details = errorData || {};
    }

    this.name = 'ApiError';
    this.status = status;
  }

  /**
   * Get a user-friendly error message
   */
  getUserMessage(): string {
    return this.message || 'An unexpected error occurred';
  }

  /**
   * Get detailed error message with request IDs (for debugging)
   */
  getDetailedMessage(): string {
    let msg = this.message;
    if (this.requestId) {
      msg += `\n\nRequest ID: ${this.requestId}`;
    }
    if (this.correlationId) {
      msg += `\nCorrelation ID: ${this.correlationId}`;
    }
    return msg;
  }
}

async function baseRequest<T>(
  endpoint: string,
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH',
  options: BodyApiOptions = {}
): Promise<T> {
  const { params } = options;
  // Support both "body" and legacy "data" keys (some DELETE calls passed data)
  const resolvedBody = options.body ?? (options as any).data;
  // Separate headers to avoid mutation
  const headers = { ...options.headers };

  // Auto-inject token
  const token = localStorage.getItem('aequitas_token');
  if (token && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  let url = `${API_URL}${endpoint}`;

  if (params) {
    const queryParams = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      queryParams.append(key, String(value));
    }
    url += `?${queryParams.toString()}`;
  }

  const config: RequestInit = {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
  };

  if (resolvedBody) {
    if (resolvedBody instanceof FormData) {
      delete (config.headers as Record<string, string>)['Content-Type'];
      config.body = resolvedBody;
    } else {
      config.body = JSON.stringify(resolvedBody);
    }
  }

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      let errorDetails;
      try {
        errorDetails = await response.json();
      } catch (e) {
        errorDetails = { message: response.statusText };
      }
      throw new ApiError(
        `API request failed with status ${response.status}`,
        response.status,
        errorDetails
      );
    }

    if (response.status === 204) {
      return null as T;
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new Error(error instanceof Error ? error.message : 'An unknown network error occurred');
  }
}

export const api = {
  get: <T>(endpoint: string, options?: BaseApiOptions) => baseRequest<T>(endpoint, 'GET', options),
  post: <T>(endpoint: string, body: any, options?: BaseApiOptions) => baseRequest<T>(endpoint, 'POST', { ...options, body }),
  put: <T>(endpoint: string, body: any, options?: BaseApiOptions) => baseRequest<T>(endpoint, 'PUT', { ...options, body }),
  delete: <T>(endpoint: string, options?: BodyApiOptions) => baseRequest<T>(endpoint, 'DELETE', options),
  patch: <T>(endpoint: string, body: any, options?: BaseApiOptions) => baseRequest<T>(endpoint, 'PATCH', { ...options, body }),
};

export { ApiError };

// Example usage with Zod schema validation
export async function fetchAndValidate<T>(
  endpoint: string,
  schema: z.ZodType<T>,
  options: BaseApiOptions = {}
): Promise<T> {
  const data = await api.get<unknown>(endpoint, options);
  const validationResult = schema.safeParse(data);
  if (!validationResult.success) {
    console.error("API response validation failed:", validationResult.error);
    throw new Error("Invalid data structure received from the server.");
  }
  return validationResult.data;
}

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

class ApiError extends Error {
  status: number;
  details: any;

  constructor(message: string, status: number, details: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

async function baseRequest<T>(
  endpoint: string,
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH',
  options: BodyApiOptions = {}
): Promise<T> {
  const { headers = {}, params, body } = options;

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

  if (body) {
    if (body instanceof FormData) {
      delete (config.headers as Record<string, string>)['Content-Type'];
      config.body = body;
    } else {
      config.body = JSON.stringify(body);
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
  post: <T>(endpoint:string, body: any, options?: BaseApiOptions) => baseRequest<T>(endpoint, 'POST', { ...options, body }),
  put: <T>(endpoint: string, body: any, options?: BaseApiOptions) => baseRequest<T>(endpoint, 'PUT', { ...options, body }),
  delete: <T>(endpoint: string, options?: BaseApiOptions) => baseRequest<T>(endpoint, 'DELETE', options),
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

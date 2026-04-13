export type ApiQuery = Record<string, string | number | boolean | undefined | null>

export class ApiError extends Error {
  readonly status: number
  readonly body: unknown

  constructor(message: string, status: number, body: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.body = body
  }
}

function buildQuery(query?: ApiQuery): string {
  if (!query) return ''

  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === null) continue
    params.set(key, String(value))
  }

  const qs = params.toString()
  return qs ? `?${qs}` : ''
}

type RequestMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

export class ApiClient {
  /**
   * Generic request method that accepts HTTP method as parameter
   */
  static async request<T>(
    method: RequestMethod,
    path: string,
    options?: {
      query?: ApiQuery
      body?: unknown
      init?: RequestInit
    }
  ): Promise<T> {
    const { query, body, init } = options ?? {}

    const url = method === 'GET' ? `${path}${buildQuery(query)}` : path

    const headers: HeadersInit = {
      Accept: 'application/json',
      ...(init?.headers ?? {}),
    }

    if (body && method !== 'GET') {
      headers['Content-Type'] = 'application/json'
    }

    const res = await fetch(url, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
      ...init,
    })

    const contentType = res.headers.get('content-type') ?? ''
    const isJson = contentType.includes('application/json')
    const responseBody = isJson
      ? await res.json().catch(() => null)
      : await res.text().catch(() => null)

    if (!res.ok) {
      const message =
        typeof responseBody === 'object' && responseBody && 'error' in responseBody
          ? String((responseBody as { error?: unknown }).error)
          : `Request failed (${res.status})`

      throw new ApiError(message, res.status, responseBody)
    }

    return responseBody as T
  }

  /**
   * Convenience method for GET requests
   */
  static async getJson<T>(path: string, query?: ApiQuery, init?: RequestInit): Promise<T> {
    return this.request<T>('GET', path, { query, init })
  }

  /**
   * Convenience method for POST requests
   */
  static async postJson<T>(path: string, data: unknown, init?: RequestInit): Promise<T> {
    return this.request<T>('POST', path, { body: data, init })
  }
}

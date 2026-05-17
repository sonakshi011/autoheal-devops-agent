const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchFromBackend<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  // Auth-ready design: inject authorization token seamlessly if present
  const headers = new Headers(options?.headers);
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("autoheal_auth_token");
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    const body = await response.json();

    if (!response.ok || body.success === false) {
      throw new Error(body.error || `API Request failed with status ${response.status}`);
    }

    return body.data as T;
  } catch (error: any) {
    console.error(`API Fetch Error [${url}]:`, error);
    throw error;
  }
}

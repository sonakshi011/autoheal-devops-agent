import { APIResponse } from "@/types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchFromBackend<T>(endpoint: string, options?: RequestInit): Promise<APIResponse<T>> {
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

    return {
      success: body.success ?? response.ok,
      data: body.data,
      error: body.error,
      timestamp: body.timestamp || new Date().toISOString(),
    } as APIResponse<T>;
  } catch (error: any) {
    console.error(`API Fetch Error [${url}]:`, error);
    return {
      success: false,
      error: error.message || "Failed to establish connection to AutoHeal core backend.",
      timestamp: new Date().toISOString(),
    } as APIResponse<T>;
  }
}

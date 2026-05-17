export interface APISuccessResponse<T> {
  success: true;
  data: T;
  timestamp: string;
}

export interface APIErrorResponse {
  success: false;
  error: string;
  timestamp: string;
}

export type APIResponse<T> = APISuccessResponse<T> | APIErrorResponse;

export interface ApiResponseType<T = any> {

  code: number;
  message: string;
  data?: T;
}

// include `status` boolean to match the GraphQL `BaseResponse.status` field
export interface ApiResponseTypeWithStatus<T = any> extends ApiResponseType<T> {
  status: boolean;
}

/**
 * Small helper to standardize API responses across resolvers/services.
 * Use `ApiResponse.success(data, message?)` for 200 responses and
 * `ApiResponse.error(message, code?, data?)` for error responses.
 */
export class ApiResponse {
  static success<T = any>(data?: any, message = "Success"): ApiResponseTypeWithStatus<T> {
    return {
      status: true,
      code: 200,
      message,
      data,
    };
  }

  static error<T = any>(message = "Internal Server Error", code = 500, data?: T): ApiResponseTypeWithStatus<T> {
    return {
      status: false,
      code,
      message,
      data,
    };
  }
}

export default ApiResponse;

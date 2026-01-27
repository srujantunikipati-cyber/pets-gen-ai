
export const ErrorResponse = {
  INTERNAL_SERVER_ERROR: "Internal server error",
} ;

export const responseMessage = {
  sendPasswordResetEmail: "Password reset email sent successfully",
    refreshToken: "Token refreshed successfully",
    failedToSendEmail: "Failed to send email",
    failRefreshToken: "Failed to refresh token",
    OtpSendSuccess: "OTP sent successfully",
    UserLoginSuccess: "User logged in successfully",
    UserSignupSuccess: "User signed up successfully",
} ;

export const HttpStatusCodes = {
  OK: 200,                       // Success
  CREATED: 201,                  // Created
  ACCEPTED: 202,                 // Accepted
  NO_CONTENT: 204,               // No Content
  BAD_REQUEST: 400,              // Bad Request
  UNAUTHORIZED: 401, 
  FORCECHANGE_PASSWORD:428,            // Unauthorized
  FORBIDDEN: 403,                // Forbidden
  NOT_FOUND: 404,                // Not Found
  METHOD_NOT_ALLOWED: 405,       // Method Not Allowed
  CONFLICT: 409,                 // Conflict
  UNPROCESSABLE_ENTITY: 422,     // Unprocessable Entity
  INTERNAL_SERVER_ERROR: 500,    // Internal Server Error
  NOT_IMPLEMENTED: 501,          // Not Implemented
  BAD_GATEWAY: 502,              // Bad Gateway
  SERVICE_UNAVAILABLE: 503,      // Service Unavailable
  GATEWAY_TIMEOUT: 504,  
        // Gateway Timeout
};

export const LoginType={
  manualy:1,
  google:2,
  manualy_google:3,
}
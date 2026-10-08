import type { components } from "./schema.js";

export * from "./schema.js";

// Convenient aliases for commonly used schemas
export type UserDto = components["schemas"]["UserOut"];
export type TokenResponse = components["schemas"]["TokenResponse"];
export type HealthReport = components["schemas"]["HealthReport"];

// Request types
export type RegisterRequest = components["schemas"]["RegisterRequest"];
export type LoginRequest = components["schemas"]["LoginRequest"];
export type RefreshRequest = components["schemas"]["RefreshRequest"];

// Error types
export type ValidationError = components["schemas"]["ValidationError"];
export type HTTPValidationError = components["schemas"]["HTTPValidationError"];

// Enum types
export type UserRole = components["schemas"]["UserRole"];

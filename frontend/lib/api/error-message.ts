import { ApiError } from "./client";

export function errorMessage(error: unknown) {
  if (error instanceof ApiError) {
    if (typeof error.details === "string") return error.details;
    if (Array.isArray(error.details)) return error.details.join(" ");
    if (error.details && typeof error.details === "object") {
      return Object.values(error.details as Record<string, unknown>).flat().join(" ");
    }
    return error.message;
  }
  return error instanceof Error ? error.message : "Une erreur est survenue.";
}

import { api } from "./client";

export type AuthResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: { id: string; email: string; full_name?: string; role: "merchant" | "underwriter" | "admin" };
};

export function login(email: string, password: string) {
  return api<AuthResponse>("/auth/login", {
    method: "POST",
    auth: false,
    body: JSON.stringify({ email, password }),
  });
}

export function register(email: string, password: string, fullName: string, role: string) {
  return api("/auth/register", {
    method: "POST",
    auth: false,
    body: JSON.stringify({ email, password, full_name: fullName, role }),
  });
}


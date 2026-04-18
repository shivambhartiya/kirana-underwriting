const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

type RequestOptions = RequestInit & {
  auth?: boolean;
};

export async function api<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers(options.headers || {});
  headers.set("Content-Type", "application/json");
  if (options.auth !== false) {
    const token = localStorage.getItem("access_token");
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }
  const response = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!response.ok) {
    if (response.status === 401) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function uploadBinary(url: string, file: File): Promise<void> {
  const response = await fetch(url, {
    method: "PUT",
    headers: { "Content-Type": file.type || "image/jpeg" },
    body: file,
  });
  if (!response.ok) {
    throw new Error("Upload failed");
  }
}


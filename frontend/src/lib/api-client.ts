const API_BASE_URL = import.meta.env.VITE_APP_API_URL || "/api";

export const getHeaders = () => {
  const token = localStorage.getItem("safina_token");
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
};

export const apiFetch = async (endpoint: string, options: RequestInit = {}) => {
  const url = endpoint.startsWith("http") ? endpoint : `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      ...getHeaders(),
      ...options.headers,
    },
  });

  if (response.status === 401) {
    localStorage.removeItem("safina_token");
    localStorage.removeItem("safina_role");
    localStorage.removeItem("safina_user");
    localStorage.removeItem("safina_projectId");
    window.location.href = "/";
    return response;
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || response.statusText || "API Request failed");
  }

  return response;
};

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
    window.location.href = "/";
    throw new Error("Unauthorized");
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    let errorMessage = "API Request failed";
    if (typeof errorData.detail === "string") {
        errorMessage = errorData.detail;
    } else if (Array.isArray(errorData.detail)) {
        errorMessage = errorData.detail.map((e: any) => e.msg).join(", ");
    } else if (errorData.message) {
        errorMessage = errorData.message;
    } else if (response.statusText) {
        errorMessage = response.statusText;
    }
    throw new Error(errorMessage);
  }

  return response;
};

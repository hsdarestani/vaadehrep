import axios from "axios";

const AUTH_FREE_PATHS = ["/accounts/login-otps/", "/accounts/verify-login/"];

const shouldAttachAuth = (url?: string) => {
  if (!url) return false;
  return !AUTH_FREE_PATHS.some((openPath) => url.includes(openPath));
};

export const api = axios.create({
  baseURL: "/api",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("vaadeh_access");
  if (token && shouldAttachAuth(config.url)) {
    config.headers = {
      ...config.headers,
      Authorization: `Bearer ${token}`,
    };
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const code = error.response?.data?.code;
    if (code === "token_not_valid" || error.response?.status === 401) {
      localStorage.removeItem("vaadeh_access");
      localStorage.removeItem("vaadeh_refresh");
      localStorage.removeItem("vaadeh_user");
    }
    return Promise.reject(error);
  },
);

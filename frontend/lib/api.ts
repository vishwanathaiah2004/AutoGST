import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

// Attach token to every request
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 globally
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// ─── Auth ────────────────────────────────────────────────────────────────────
export const authApi = {
  login: (email: string, password: string) =>
    api.post("/auth/login", { email, password }),
  register: (data: any) => api.post("/auth/register", data),
  me: () => api.get("/auth/me"),
};

// ─── Transactions ─────────────────────────────────────────────────────────────
export const transactionsApi = {
  list: (params?: any) => api.get("/transactions", { params }),
  get: (id: number) => api.get(`/transactions/${id}`),
  create: (data: any) => api.post("/transactions", data),
  update: (id: number, data: any) => api.put(`/transactions/${id}`, data),
  delete: (id: number) => api.delete(`/transactions/${id}`),
};

// ─── Dashboard ───────────────────────────────────────────────────────────────
export const dashboardApi = {
  stats: () => api.get("/dashboard"),
};

// ─── GST ─────────────────────────────────────────────────────────────────────
export const gstApi = {
  calculate: (data: any) => api.post("/gst/calculate", data),
  rates: () => api.get("/gst/rates"),
  hsnRate: (code: string) => api.get(`/gst/hsn-rate/${code}`),
};

// ─── Reports ─────────────────────────────────────────────────────────────────
export const reportsApi = {
  gstr: (params: any) => api.get("/reports/gstr", { params }),
  pdfUrl: (params: any) => {
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : "";
    const q = new URLSearchParams(params).toString();
    return `${API_URL}/reports/gstr/pdf?${q}`;
  },
  excelUrl: (params: any) => {
    const q = new URLSearchParams(params).toString();
    return `${API_URL}/reports/gstr/excel?${q}`;
  },
};

// ─── Upload ──────────────────────────────────────────────────────────────────
export const uploadApi = {
  upload: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post("/upload", form, { headers: { "Content-Type": "multipart/form-data" } });
  },
  list: () => api.get("/upload"),
  get: (id: number) => api.get(`/upload/${id}`),
};

// ─── Tax ─────────────────────────────────────────────────────────────────────
export const taxApi = {
  calculate: (data: any, save = false) =>
    api.post(`/tax/calculate?save=${save}`, data),
  slabs: (regime: string) => api.get(`/tax/slabs?regime=${regime}`),
  history: () => api.get("/tax/history"),
};

// ─── Alerts ──────────────────────────────────────────────────────────────────
export const alertsApi = {
  list: (unreadOnly = false) => api.get(`/alerts?unread_only=${unreadOnly}`),
  markRead: (id: number) => api.put(`/alerts/${id}/read`),
  markAllRead: () => api.put("/alerts/read-all"),
};

export default api;

// ─── AI Assistant ─────────────────────────────────────────────────────────────
export const aiApi = {
  chat: (message: string, history: { role: string; content: string }[]) =>
    api.post("/ai/chat", { message, history }),
  suggestions: () => api.get("/ai/suggestions"),
};

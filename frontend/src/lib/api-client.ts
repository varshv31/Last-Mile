import type {
  AddressInput,
  AdminOrderFilters,
  AgentProfileResponse,
  AreaResponse,
  AssignmentResponse,
  AvailabilityStatus,
  CODSurchargeResponse,
  FailureReason,
  OrderCreateInput,
  OrderResponse,
  OrderStatus,
  OrderType,
  PackageInput,
  PaymentType,
  RateCardResponse,
  RateQuote,
  RescheduleResponse,
  SurchargeType,
  TokenPair,
  TrackingTimelineResponse,
  UserResponse,
  UserRole,
  ZoneResponse,
  ZoneType,
} from "./api-types";

const getBaseUrl = () => {
  const envUrl = import.meta.env["VITE_API_BASE_URL"] as string | undefined;
  if (envUrl) return envUrl;
  let hostname = typeof window !== "undefined" ? window.location.hostname : "127.0.0.1";
  if (hostname === "localhost") hostname = "127.0.0.1";
  return `http://${hostname}:8000`;
};

export const API_BASE_URL = getBaseUrl().replace(/\/$/, "");

const PREFIX = "/api/v1";
const STORAGE_KEY = "lmd.auth.tokens";

export class ApiError extends Error {
  status: number;
  detail: unknown;
  constructor(status: number, message: string, detail?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

/* ------------------------------ token storage ----------------------------- */

export interface StoredTokens {
  access_token: string;
  refresh_token: string;
}

export function getTokens(): StoredTokens | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as StoredTokens) : null;
  } catch {
    return null;
  }
}

export function setTokens(tokens: StoredTokens | null) {
  if (typeof window === "undefined") return;
  if (tokens) window.localStorage.setItem(STORAGE_KEY, JSON.stringify(tokens));
  else window.localStorage.removeItem(STORAGE_KEY);
}

/* -------------------------------- core fetch ------------------------------ */

function messageFromDetail(detail: unknown, fallback: string): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const parts = detail
      .map((d) => {
        const item = d as { loc?: unknown[]; msg?: string };
        const field = Array.isArray(item.loc) ? item.loc.slice(1).join(".") : "";
        return field ? `${field}: ${item.msg ?? "invalid"}` : (item.msg ?? "invalid");
      })
      .filter(Boolean);
    if (parts.length) return parts.join(" • ");
  }
  return fallback;
}

let refreshInFlight: Promise<StoredTokens | null> | null = null;

async function refreshTokens(): Promise<StoredTokens | null> {
  const current = getTokens();
  if (!current?.refresh_token) return null;
  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      try {
        const res = await fetch(`${API_BASE_URL}${PREFIX}/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: current.refresh_token }),
        });
        if (!res.ok) {
          setTokens(null);
          return null;
        }
        const data = (await res.json()) as TokenPair;
        const next = { access_token: data.access_token, refresh_token: data.refresh_token };
        setTokens(next);
        return next;
      } catch {
        return null;
      } finally {
        setTimeout(() => {
          refreshInFlight = null;
        }, 0);
      }
    })();
  }
  return refreshInFlight;
}

interface RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "DELETE" | undefined;
  body?: unknown | undefined;
  query?: Record<string, string | number | boolean | undefined | null> | undefined;
  auth?: boolean | undefined;
  signal?: AbortSignal | undefined;
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, query, auth = true, signal } = options;

  const url = new URL(`${API_BASE_URL}${PREFIX}${path}`);
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, String(value));
      }
    }
  }

  const send = async (token?: string) => {
    const headers: Record<string, string> = {};
    if (body !== undefined) headers["Content-Type"] = "application/json";
    if (token) headers["Authorization"] = `Bearer ${token}`;
    return fetch(url.toString(), {
      method,
      headers,
      body: body === undefined ? null : JSON.stringify(body),
      ...(signal ? { signal } : {}),
    });
  };

  let response: Response;
  try {
    response = await send(auth ? getTokens()?.access_token : undefined);
  } catch (err) {
    if (err instanceof Error && err.name === "AbortError") {
      throw err;
    }
    throw new ApiError(
      0,
      `Cannot reach the API at ${API_BASE_URL}. Make sure the backend is running.`,
    );
  }

  if (response.status === 401 && auth) {
    const refreshed = await refreshTokens();
    if (refreshed) {
      response = await send(refreshed.access_token);
    } else {
      setTokens(null);
      if (typeof window !== "undefined") {
        window.dispatchEvent(new CustomEvent("lmd:unauthenticated"));
      }
    }
  }

  if (response.status === 204) return undefined as T;

  const text = await response.text();
  let payload: unknown = null;
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = text;
    }
  }

  if (!response.ok) {
    const detail = (payload as { detail?: unknown } | null)?.detail ?? payload;
    throw new ApiError(
      response.status,
      messageFromDetail(detail, `Request failed (${response.status})`),
      detail,
    );
  }

  return payload as T;
}

/* --------------------------------- Auth ---------------------------------- */

export const authApi = {
  register: (body: {
    name: string;
    email: string;
    phone?: string | undefined;
    password: string;
    role?: UserRole | undefined;
  }) => apiRequest<UserResponse>("/auth/register", { method: "POST", body, auth: false }),
  login: (body: { email: string; password: string }) =>
    apiRequest<TokenPair>("/auth/login", { method: "POST", body, auth: false }),
  me: () => apiRequest<UserResponse>("/auth/me"),
};

/* ------------------------------ Customer API ------------------------------ */

export interface CalculatePayload {
  pickup_address: AddressInput;
  drop_address: AddressInput;
  package: PackageInput;
  order_type: OrderType;
  payment_type: PaymentType;
}

export const customerApi = {
  calculate: (body: CalculatePayload, signal?: AbortSignal) =>
    apiRequest<RateQuote>("/orders/calculate", { method: "POST", body, ...(signal ? { signal } : {}) }),
  createOrder: (body: OrderCreateInput) =>
    apiRequest<OrderResponse>("/orders", { method: "POST", body }),
  listOrders: (query: { limit?: number | undefined; offset?: number | undefined } = {}) =>
    apiRequest<OrderResponse[]>("/orders", { query }),
  getOrder: (orderId: string) => apiRequest<OrderResponse>(`/orders/${orderId}`),
  getTracking: (orderId: string) =>
    apiRequest<TrackingTimelineResponse>(`/orders/${orderId}/tracking`),
  reschedule: (orderId: string, newDeliveryDate: string) =>
    apiRequest<RescheduleResponse>(`/orders/${orderId}/reschedule`, {
      method: "POST",
      body: { new_delivery_date: newDeliveryDate },
    }),
};

/* -------------------------------- Agent API ------------------------------- */

export const agentApi = {
  profile: () => apiRequest<AgentProfileResponse>("/agent/profile"),
  listOrders: (query: { limit?: number | undefined; offset?: number | undefined } = {}) =>
    apiRequest<OrderResponse[]>("/agent/orders", { query }),
  getOrder: (orderId: string) => apiRequest<OrderResponse>(`/agent/orders/${orderId}`),
  updateLocation: (body: { latitude: number; longitude: number; zone_id?: string | undefined }) =>
    apiRequest<AgentProfileResponse>("/agent/location", { method: "PATCH", body }),
  updateAvailability: (availability_status: AvailabilityStatus) =>
    apiRequest<AgentProfileResponse>("/agent/availability", {
      method: "PATCH",
      body: { availability_status },
    }),
  updateOrderStatus: (orderId: string, body: { status: OrderStatus; remarks?: string | undefined }) =>
    apiRequest<OrderResponse>(`/agent/orders/${orderId}/status`, { method: "PATCH", body }),
  failOrder: (orderId: string, body: { reason: FailureReason; remarks?: string | undefined }) =>
    apiRequest<OrderResponse>(`/agent/orders/${orderId}/fail`, { method: "POST", body }),
};

/* -------------------------------- Admin API ------------------------------- */

export const adminApi = {
  // Zones
  listZones: (query: { limit?: number | undefined; offset?: number | undefined } = {}) =>
    apiRequest<ZoneResponse[]>("/admin/zones", { query }),
  createZone: (body: { name: string; code: string; description?: string | undefined; is_active?: boolean | undefined }) =>
    apiRequest<ZoneResponse>("/admin/zones", { method: "POST", body }),
  updateZone: (
    id: string,
    body: { name?: string | undefined; description?: string | null | undefined; is_active?: boolean | undefined },
  ) => apiRequest<ZoneResponse>(`/admin/zones/${id}`, { method: "PATCH", body }),
  deleteZone: (id: string) => apiRequest<void>(`/admin/zones/${id}`, { method: "DELETE" }),

  // Areas
  listAreas: (query: { limit?: number | undefined; offset?: number | undefined } = {}) =>
    apiRequest<AreaResponse[]>("/admin/areas", { query }),
  createArea: (body: {
    name: string;
    postal_code: string;
    zone_id: string;
    is_active?: boolean | undefined;
  }) => apiRequest<AreaResponse>("/admin/areas", { method: "POST", body }),
  updateArea: (id: string, body: { name?: string | undefined; zone_id?: string | undefined; is_active?: boolean | undefined }) =>
    apiRequest<AreaResponse>(`/admin/areas/${id}`, { method: "PATCH", body }),
  deleteArea: (id: string) => apiRequest<void>(`/admin/areas/${id}`, { method: "DELETE" }),

  // Rate cards
  listRates: (query: { limit?: number | undefined; offset?: number | undefined } = {}) =>
    apiRequest<RateCardResponse[]>("/admin/rates", { query }),
  createRate: (body: {
    order_type: OrderType;
    zone_type: ZoneType;
    min_weight: number;
    max_weight: number;
    price: number;
    is_active?: boolean | undefined;
    effective_from?: string | null | undefined;
    effective_to?: string | null | undefined;
  }) => apiRequest<RateCardResponse>("/admin/rates", { method: "POST", body }),
  updateRate: (
    id: string,
    body: {
      price?: number | undefined;
      is_active?: boolean | undefined;
      effective_from?: string | null | undefined;
      effective_to?: string | null | undefined;
    },
  ) => apiRequest<RateCardResponse>(`/admin/rates/${id}`, { method: "PATCH", body }),
  deleteRate: (id: string) => apiRequest<void>(`/admin/rates/${id}`, { method: "DELETE" }),

  // COD surcharges
  listCodSurcharges: () => apiRequest<CODSurchargeResponse[]>("/admin/cod-surcharges"),
  createCodSurcharge: (body: {
    order_type: OrderType;
    surcharge_type: SurchargeType;
    value: number;
    is_active?: boolean | undefined;
  }) => apiRequest<CODSurchargeResponse>("/admin/cod-surcharges", { method: "POST", body }),
  updateCodSurcharge: (
    id: string,
    body: { surcharge_type?: SurchargeType | undefined; value?: number | undefined; is_active?: boolean | undefined },
  ) => apiRequest<CODSurchargeResponse>(`/admin/cod-surcharges/${id}`, { method: "PATCH", body }),
  deleteCodSurcharge: (id: string) =>
    apiRequest<void>(`/admin/cod-surcharges/${id}`, { method: "DELETE" }),

  // Orders
  createOrder: (body: OrderCreateInput) =>
    apiRequest<OrderResponse>("/admin/orders", { method: "POST", body }),
  listOrders: (filters: AdminOrderFilters = {}) =>
    apiRequest<OrderResponse[]>("/admin/orders", {
      query: filters as Record<string, string | number | undefined>,
    }),
  getOrder: (orderId: string) => apiRequest<OrderResponse>(`/admin/orders/${orderId}`),
  overrideStatus: (orderId: string, body: { status: OrderStatus; reason: string }) =>
    apiRequest<OrderResponse>(`/admin/orders/${orderId}/status`, { method: "PATCH", body }),
  assignAgent: (orderId: string, agentId: string) =>
    apiRequest<AssignmentResponse>(`/admin/orders/${orderId}/assign-agent`, {
      method: "POST",
      body: { agent_id: agentId },
    }),
  autoAssign: (orderId: string) =>
    apiRequest<AssignmentResponse>(`/admin/orders/${orderId}/auto-assign`, { method: "POST" }),
};

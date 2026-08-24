// Types mirror API_DOCUMENTATION.md exactly. No invented fields.

export type UserRole = "CUSTOMER" | "AGENT" | "ADMIN";
export type OrderStatus =
  | "CREATED"
  | "PICKED_UP"
  | "IN_TRANSIT"
  | "OUT_FOR_DELIVERY"
  | "DELIVERED"
  | "FAILED"
  | "CANCELLED";
export type OrderType = "B2B" | "B2C";
export type PaymentType = "PREPAID" | "COD";
export type ZoneType = "INTRA_ZONE" | "INTER_ZONE";
export type AvailabilityStatus = "AVAILABLE" | "BUSY" | "OFFLINE";
export type AssignmentType = "MANUAL" | "AUTO";
export type SurchargeType = "FIXED" | "PERCENTAGE";
export type FailureReason =
  | "CUSTOMER_NOT_AVAILABLE"
  | "WRONG_ADDRESS"
  | "CUSTOMER_REJECTED"
  | "ACCESS_ISSUE"
  | "OTHER";

export const ORDER_STATUSES: OrderStatus[] = [
  "CREATED",
  "PICKED_UP",
  "IN_TRANSIT",
  "OUT_FOR_DELIVERY",
  "DELIVERED",
  "FAILED",
  "CANCELLED",
];

export const FAILURE_REASONS: FailureReason[] = [
  "CUSTOMER_NOT_AVAILABLE",
  "WRONG_ADDRESS",
  "CUSTOMER_REJECTED",
  "ACCESS_ISSUE",
  "OTHER",
];

export interface AddressInput {
  name: string;
  phone: string;
  address_line1: string;
  address_line2?: string | null | undefined;
  city: string;
  state: string;
  postal_code: string;
  country?: string | undefined;
}

export interface PackageInput {
  length_cm: number;
  breadth_cm: number;
  height_cm: number;
  actual_weight_kg: number;
}

export interface AddressResponse extends AddressInput {
  id: string;
  address_type: "PICKUP" | "DROP";
  address_line2: string | null;
  country: string;
}

export interface PackageResponse extends PackageInput {
  id: string;
}

export interface UserResponse {
  id: string;
  name: string;
  email: string;
  phone: string | null;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface OrderResponse {
  id: string;
  order_number: string;
  customer_id: string;
  pickup_zone_id: string | null;
  drop_zone_id: string | null;
  order_type: OrderType;
  payment_type: PaymentType;
  zone_type: ZoneType | null;
  actual_weight: number;
  volumetric_weight: number;
  billable_weight: number;
  base_charge: number;
  cod_charge: number;
  total_charge: number;
  status: OrderStatus;
  assigned_agent_id: string | null;
  confirmed_at: string | null;
  created_at: string;
  updated_at: string;
  addresses: AddressResponse[];
  package: PackageResponse | null;
}

export interface OrderCreateInput {
  pickup_address: AddressInput;
  drop_address: AddressInput;
  package: PackageInput;
  order_type: OrderType;
  payment_type: PaymentType;
  customer_id?: string | undefined;
}

export interface RateQuote {
  pickup_area_name: string;
  pickup_postal_code: string;
  pickup_zone_id: string;
  pickup_zone_name: string;
  drop_area_name: string;
  drop_postal_code: string;
  drop_zone_id: string;
  drop_zone_name: string;
  zone_type: ZoneType;
  actual_weight: number;
  volumetric_weight: number;
  billable_weight: number;
  rate_card_id: string;
  base_charge: number;
  cod_surcharge: number;
  total_charge: number;
  order_type: OrderType;
  payment_type: PaymentType;
}

export interface TrackingEvent {
  id: string;
  previous_status: OrderStatus | null;
  new_status: OrderStatus;
  actor_role: UserRole | null;
  actor_name: string | null;
  remarks: string | null;
  created_at: string;
}

export interface TrackingTimelineResponse {
  order_id: string;
  order_number: string;
  current_status: OrderStatus;
  timeline: TrackingEvent[];
}

export type RescheduleStatus = "PENDING" | "APPROVED" | "REJECTED";

export interface RescheduleResponse {
  order_id: string;
  reschedule_id: string;
  new_delivery_date: string;
  status: RescheduleStatus;
}

export interface AgentProfileResponse {
  id: string;
  user_id: string;
  availability_status: AvailabilityStatus;
  current_latitude: number | null;
  current_longitude: number | null;
  current_zone_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface AssignmentResponse {
  agent_user_id: string;
  agent_name: string;
  assignment_type: AssignmentType;
  distance_km: number | null;
  reason: string;
  assigned_at: string;
}

export interface ZoneResponse {
  id: string;
  name: string;
  code: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AreaResponse {
  id: string;
  name: string;
  postal_code: string;
  zone_id: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface RateCardResponse {
  id: string;
  order_type: OrderType;
  zone_type: ZoneType;
  min_weight: number;
  max_weight: number;
  price: number;
  is_active: boolean;
  effective_from: string | null;
  effective_to: string | null;
  created_at: string;
  updated_at: string;
}

export interface CODSurchargeResponse {
  id: string;
  order_type: OrderType;
  surcharge_type: SurchargeType;
  value: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AdminOrderFilters {
  status?: OrderStatus | undefined;
  pickup_zone_id?: string | undefined;
  drop_zone_id?: string | undefined;
  agent_id?: string | undefined;
  order_type?: OrderType | undefined;
  payment_type?: PaymentType | undefined;
  customer_id?: string | undefined;
  created_from?: string | undefined;
  created_to?: string | undefined;
  limit?: number | undefined;
  offset?: number | undefined;
}

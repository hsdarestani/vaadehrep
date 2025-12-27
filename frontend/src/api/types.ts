export type Vendor = {
  id: number;
  name: string;
  slug: string;
  is_active?: boolean;
  is_accepting_orders?: boolean;
  logo_url?: string;
  description?: string;
  lat?: number;
  lng?: number;
  area?: string;
};

export type Category = {
  id: number;
  vendor: number;
  name: string;
  description?: string;
  sort_order?: number;
};

export type Product = {
  id: number;
  vendor: number;
  category: number | null;
  name_fa: string;
  name_en?: string;
  short_description?: string;
  description?: string;
  base_price?: number;
  sort_order?: number;
  is_active?: boolean;
  is_available?: boolean;
  is_available_today?: boolean;
};

export type Address = {
  id: number;
  title: string;
  city?: string;
  full_text?: string;
  is_default?: boolean;
  latitude?: number;
  longitude?: number;
};

export type Order = {
  id: string;
  status: string;
  placed_at: string;
  short_code: string;
  payment_url?: string | null;
  total_amount?: number;
  delivery_type?: string | null;
  delivery_is_cash_on_delivery?: boolean;
  payment_status?: string;
  items?: OrderItem[];
  delivery?: OrderDelivery;
};

export type OrderItem = {
  id: string;
  product: number;
  product_title_snapshot: string;
  quantity: number;
  unit_price_snapshot: number;
  modifiers?: unknown;
  line_subtotal?: number;
};

export type OrderDelivery = {
  id: string;
  delivery_type?: string;
  is_cash_on_delivery?: boolean;
  courier_name?: string;
  courier_phone?: string;
  tracking_code?: string;
  tracking_url?: string;
  external_delivery_quote_amount?: number;
  external_delivery_final_amount?: number;
  external_provider?: string;
  external_payload?: unknown;
  created_at?: string;
};

export type UserProfile = {
  id: number | string;
  phone: string;
};

export type ActiveOrderSummary = {
  id: string;
  short_code: string;
  status: string;
};

export type VerifyLoginResponse = {
  ok: boolean;
  access: string;
  refresh: string;
  user: UserProfile;
};

export type SessionResponse = {
  authenticated: boolean;
  user?: UserProfile;
  active_order?: ActiveOrderSummary | null;
};

export type ServiceabilityResponse = {
  is_serviceable: boolean;
  delivery_type: "IN_ZONE" | "OUT_OF_ZONE_SNAPP" | null;
  delivery_fee_amount: number;
  delivery_label?: string;
  delivery_is_postpaid?: boolean;
  vendor?: Vendor | null;
  menu_products: Product[];
  distance_meters?: number | null;
  reason?: string;
  suggested_product_ids?: number[];
  active_order?: ActiveOrderSummary | null;
  nearest_location?: {
    title?: string;
    lat: number;
    lng: number;
    service_radius_m?: number | null;
  };
};

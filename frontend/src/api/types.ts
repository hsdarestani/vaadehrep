export type Vendor = {
  id: number;
  name: string;
  slug: string;
  is_active?: boolean;
  is_accepting_orders?: boolean;
  logo_url?: string;
  description?: string;
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
};

export type Order = {
  id: string;
  status: string;
  placed_at: string;
  total_amount?: number;
};

export type UserProfile = {
  id: number | string;
  phone: string;
};

export type VerifyLoginResponse = {
  ok: boolean;
  access: string;
  refresh: string;
  user: UserProfile;
};

export interface User {
  id: int;
  full_name: string;
  email: string;
  role: 'user' | 'admin';
  phone?: string;
  department?: string;
  is_active: boolean;
  created_at: string;
}

export type int = number;

export interface Category {
  id: number;
  name: string;
  slug: string;
  description?: string;
  icon?: string;
  is_active: boolean;
  subcategories: Subcategory[];
}

export interface Subcategory {
  id: number;
  category_id: number;
  name: string;
  slug: string;
  is_active: boolean;
}

export interface CampusLocation {
  id: number;
  name: string;
  building_or_area: string;
  description?: string;
  is_active: boolean;
}

export interface ItemImage {
  id: number;
  image_path: string;
  original_filename: string;
  is_primary: boolean;
  uploaded_at: string;
}

export interface FoundItemCard {
  id: number;
  reference_code: string;
  title: string;
  description: string;
  category: { id: number; name: string; slug: string };
  subcategory?: { id: number; name: string; slug: string };
  location: { id: number; name: string; building_or_area: string };
  found_at: string;
  quantity: number;
  condition?: string;
  status: 'available' | 'returned' | 'removed';
  created_at: string;
  primary_image?: string;
}

export interface FoundItemDetail {
  id: number;
  reference_code: string;
  title: string;
  description: string;
  category: { id: number; name: string; slug: string };
  subcategory?: { id: number; name: string; slug: string };
  location: { id: number; name: string; building_or_area: string };
  reporter: { id: number; full_name: string; department?: string };
  found_at: string;
  quantity: number;
  condition?: string;
  status: 'available' | 'returned' | 'removed';
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  images: ItemImage[];
  contact_count?: number;
  is_owner?: boolean;
}

export interface MyFoundItem extends Omit<FoundItemDetail, 'images' | 'is_owner' | 'reporter'> {
  primary_image?: string;
  contact_count: number;
}

export interface PaginatedItems {
  items: FoundItemCard[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ContactRequest {
  id: number;
  item_id: number;
  item: {
    id: number;
    reference_code: string;
    title: string;
    status: string;
    primary_image?: string;
  };
  sender: {
    id: number;
    full_name: string;
    department?: string;
  };
  recipient: {
    id: number;
    full_name: string;
    department?: string;
  };
  message: string;
  status: 'new' | 'read' | 'closed';
  created_at: string;
  updated_at: string;
}

export interface NotificationItem {
  id: number;
  type: string;
  title: string;
  message: string;
  related_item_id?: number;
  related_contact_request_id?: number;
  is_read: boolean;
  created_at: string;
}

export interface DatabaseOverview {
  total_users: number;
  total_items: number;
  available_items: number;
  returned_items: number;
  removed_items: number;
  total_contact_requests: number;
  categories_count: number;
  locations_count: number;
  total_images: number;
  total_notifications: number;
  total_status_history: number;
}

export interface TableColumnMeta {
  name: string;
  type: string;
  nullable: boolean;
  is_primary: boolean;
  default?: string;
}

export interface TableMeta {
  name: string;
  type: string;
  row_count: number;
  columns: TableColumnMeta[];
}

export interface TableRowsData {
  table_name: string;
  total_rows: number;
  page: number;
  page_size: number;
  total_pages: number;
  columns: string[];
  rows: Record<string, unknown>[];
}

export interface SqlQueryMeta {
  id: string;
  title: string;
  category: string;
  concept: string;
  description: string;
  sql_text: string;
  params: Record<string, number>;
}

export interface SqlQueryResult {
  query_id: string;
  title: string;
  concept: string;
  sql_executed: string;
  execution_time_ms: number;
  row_count: number;
  columns: string[];
  rows: Record<string, unknown>[];
}

export interface DatabaseRelationship {
  from_table: string;
  from_column: string;
  constraint_name: string;
  to_table: string;
  to_column: string;
}

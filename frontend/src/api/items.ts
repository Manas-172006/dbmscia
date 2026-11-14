import { api } from './client';
import type { FoundItemDetail, MyFoundItem, PaginatedItems } from '../types';

export interface FoundItemUpdatePayload {
  title?: string;
  description?: string;
  category_id?: number;
  subcategory_id?: number | null;
  location_id?: number;
  found_at?: string;
  quantity?: number;
  condition?: string;
}

export interface SearchFilters {
  location_id?: number | string;
  category_id?: number | string;
  subcategory_id?: number | string;
  q?: string;
  quantity?: number | string;
  date_from?: string;
  date_to?: string;
  sort?: string;
  page?: number;
  page_size?: number;
}

export const itemsApi = {
  search: (filters: SearchFilters) =>
    api.get<PaginatedItems>('/items', filters),

  getByReference: (refCode: string) =>
    api.get<FoundItemDetail>(`/items/${refCode}`),

  create: (formData: FormData) =>
    api.postForm<FoundItemDetail>('/items', formData),

  update: (id: number, data: FoundItemUpdatePayload) =>
    api.patch<FoundItemDetail>(`/items/${id}`, data),

  updateStatus: (id: number, status: 'available' | 'returned' | 'removed', note?: string) =>
    api.patch<FoundItemDetail>(`/items/${id}/status`, { status, note }),

  delete: (id: number) =>
    api.delete<{ message: string; status: string }>(`/items/${id}`),

  getMyItems: () =>
    api.get<MyFoundItem[]>('/me/items'),
};

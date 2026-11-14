import { api } from './client';
import type { Category, CampusLocation } from '../types';

export const categoriesApi = {
  getAll: () => api.get<Category[]>('/categories'),
};

export const locationsApi = {
  getAll: () => api.get<CampusLocation[]>('/locations'),
};

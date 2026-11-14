import { api } from './client';
import type { User } from '../types';

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export const authApi = {
  register: (data: { full_name: string; email: string; password: string; department?: string; phone?: string }) =>
    api.post<TokenResponse>('/auth/register', data),

  login: (data: { email: string; password: string }) =>
    api.post<TokenResponse>('/auth/login', data),

  getMe: () =>
    api.get<User>('/auth/me'),
};

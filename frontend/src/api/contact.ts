import { api } from './client';
import type { ContactRequest, NotificationItem } from '../types';

export const contactApi = {
  sendContactRequest: (itemId: number, message: string) =>
    api.post<ContactRequest>(`/items/${itemId}/contact`, { message }),

  getSentRequests: () =>
    api.get<ContactRequest[]>('/me/contact-requests/sent'),

  getReceivedRequests: () =>
    api.get<ContactRequest[]>('/me/contact-requests/received'),

  updateRequestStatus: (requestId: number, status: 'new' | 'read' | 'closed') =>
    api.patch<ContactRequest>(`/contact-requests/${requestId}/status`, { status }),

  getNotifications: () =>
    api.get<NotificationItem[]>('/me/notifications'),

  markNotificationRead: (id: number) =>
    api.patch<NotificationItem>(`/me/notifications/${id}/read`),

  markAllNotificationsRead: () =>
    api.patch<{ message: string }>('/me/notifications/read-all'),
};

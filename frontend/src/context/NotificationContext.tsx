import React, { createContext, useContext, useEffect, useState } from 'react';
import { contactApi } from '../api/contact';
import type { NotificationItem } from '../types';
import { useAuth } from './AuthContext';

interface NotificationContextType {
  notifications: NotificationItem[];
  unreadCount: number;
  markAsRead: (id: number) => Promise<void>;
  markAllAsRead: () => Promise<void>;
}

interface NotificationState {
  userId: number;
  notifications: NotificationItem[];
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const [notificationState, setNotificationState] = useState<NotificationState | null>(null);
  const notifications = user && notificationState && user.id === notificationState.userId
    ? notificationState.notifications
    : [];

  useEffect(() => {
    if (!user) return;
    let active = true;
    const pollNotifications = () => {
      contactApi.getNotifications()
        .then((data) => {
          if (active) setNotificationState({ userId: user.id, notifications: data });
        })
        .catch((error: Error) => {
          console.error('Failed to load notifications', error);
        });
    };
    pollNotifications();
    const interval = window.setInterval(pollNotifications, 20000);
    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, [user]);

  const markAsRead = async (id: number) => {
    if (!user) return;
    await contactApi.markNotificationRead(id);
    setNotificationState((current) => current?.userId === user.id
      ? {
        ...current,
        notifications: current.notifications.map((notification) =>
          notification.id === id ? { ...notification, is_read: true } : notification
        ),
      }
      : current);
  };

  const markAllAsRead = async () => {
    if (!user) return;
    await contactApi.markAllNotificationsRead();
    setNotificationState((current) => current?.userId === user.id
      ? {
        ...current,
        notifications: current.notifications.map((notification) => ({ ...notification, is_read: true })),
      }
      : current);
  };

  const unreadCount = notifications.filter((notification) => !notification.is_read).length;

  return (
    <NotificationContext.Provider
      value={{
        notifications,
        unreadCount,
        markAsRead,
        markAllAsRead,
      }}
    >
      {children}
    </NotificationContext.Provider>
  );
};

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};

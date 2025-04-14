import type { PaginatedResponse, UserNotification } from "#imports";
import { groupBy } from "lodash-es";

export type NotificationGroup = {
  isGroup: true;
  key: string;
  label: string;
  notifications: UserNotification[];
} | {
  isGroup: false;
  key: string;
  notification: UserNotification;
};

export const useNotificationStore = defineStore('notifications', {
  state: () => ({
    notifications: [] as UserNotification[],
    isLoading: false,
    enabled: true,
  }),
  actions: {
    async fetchNotifications() {
      try {
        this.isLoading = true;
        const res = await $fetch<PaginatedResponse<UserNotification>>('/api/v1/pentestusers/self/notifications/?read=false&order=-group', { method: 'GET' });
        this.notifications = res.results;
      return this.notifications;
      } finally {
        this.isLoading = false;
      }
    },
    async markAsRead(notification: UserNotification) {
      if (!notification.read) {
        try {
          notification.read = true;
          await $fetch(`/api/v1/pentestusers/self/notifications/${notification.id}/`, {
            method: 'PATCH',
            body: {
              read: true
            }
          });
        } catch (error) {
          notification.read = false;
          throw error;
        }
      }
    },
    async markAllAsRead() {
      await $fetch('/api/v1/pentestusers/self/notifications/readall/', {
        method: 'POST',
        body: {},
      });
      this.notifications.forEach(n => n.read = true);
    }
  },
  getters: {
    unreadNotifications(): UserNotification[] {
      return this.notifications.filter(n => !n.read);
    },
    unreadNotificationCount(): number {
      return this.unreadNotifications.length;
    },
    groupedNotifications(): NotificationGroup[] {
      return Object.entries(groupBy(this.unreadNotifications, n => n.content.project_id || n.id))
        .map(([k, g]) => {
          const isGrouped = g.length !== 1 || (k !== g[0]!.id || g[0]!.content.project_name);
          return {
            isGroup: isGrouped,
            key: k,
            ...(isGrouped ? {
              label: `${g[0]!.content.project_name}`,
              notifications: g
            } : {
              notification: g[0]!
            })
          } as NotificationGroup
        });
    },
  },
  persist: {
    storage: sessionStorage,
    pick: ['enabled'],
  }
})

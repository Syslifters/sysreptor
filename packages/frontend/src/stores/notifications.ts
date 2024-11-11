import type { PaginatedResponse, UserNotification } from "#imports";

export const useNotificationStore = defineStore('notifications', {
  state: () => ({
    notifications: [] as UserNotification[],
  }),
  actions: {
    async fetchNotifications() {
      const res = await $fetch<PaginatedResponse<UserNotification>>('/api/v1/pentestusers/self/notifications/', { method: 'GET' });
      this.notifications = res.results;
      return this.notifications;
    },
    async markAsRead(notification: UserNotification) {
      if (!notification.read) {
        await $fetch(`/api/v1/pentestusers/self/notifications/${notification.id}/`, {
          method: 'PATCH',
          body: {
            read: true
          }
        });
        notification.read = true;
      }
    },
  },
  getters: {
    unreadNotificationCount(): number {
      return this.notifications.filter(n => !n.read).length;
    },
  },
})

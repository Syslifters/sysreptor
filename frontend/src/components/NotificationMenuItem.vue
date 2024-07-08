<template>
  <s-btn-icon>
    <v-badge v-if="notificationStore.unreadNotificationCount > 0" :content="notificationStore.unreadNotificationCount" color="primary-bg">
      <v-icon icon="mdi-bell" />
    </v-badge>
    <v-icon v-else icon="mdi-bell" />

    <s-tooltip activator="parent" location="bottom" text="Notifications" />

    <v-menu activator="parent" :close-on-content-click="false" location="bottom" max-width="500px" class="menu-max-height">
      <v-list>
        <v-list-item
          v-for="notification in notificationStore.notifications"
          :key="notification.id"
          :title="notification.content.title"
          :subtitle="notification.content.text"
          :href="notification.content.link_url as any"
          target="_blank"
          @click="markAsRead(notification)"
          link
          lines="two"
        >
          <template #append>
            <s-btn-icon v-if="!notification.read" @click.stop.prevent="markAsRead(notification)" icon="mdi-checkbox-blank-outline" />
            <s-btn-icon v-else disabled icon="mdi-checkbox-marked-outline" />
          </template>
        </v-list-item>
        <v-list-item
          v-if="notificationStore.notifications.length === 0"
          title="No notifications"
        />
      </v-list>
    </v-menu>
  </s-btn-icon>
</template>

<script setup lang="ts">
const notificationStore = useNotificationStore();
useLazyAsyncData(async () => {
  await notificationStore.fetchNotifications();
});

async function markAsRead(notification: UserNotification) {
  try {
    await notificationStore.markAsRead(notification);
  } catch (error: any) {
    requestErrorToast({ error });
  }
}
</script>

<style lang="scss" scoped>
.menu-max-height {
  max-height: 90vh;
}
</style>

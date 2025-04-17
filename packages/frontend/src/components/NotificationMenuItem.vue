<template>
  <s-btn-icon>
    <v-badge 
      :model-value="notificationStore.enabled && notificationStore.unreadNotificationCount > 0"
      :content="notificationStore.unreadNotificationCount"
      color="primary-bg"
    >
      <v-icon :icon="notificationStore.enabled ? 'mdi-bell' : 'mdi-bell-off'" />
    </v-badge>

    <s-tooltip activator="parent" location="bottom" text="Notifications" />

    <v-menu 
      @update:model-value="onOpenMenu"
      activator="parent" 
      :close-on-content-click="false" 
      location="bottom" 
      max-width="500px" 
      class="menu-max-height"
    >
      <v-list
        :opened="openGroups"
        @click:open="onOpenGroup"
        density="compact"
        class="h-100 d-flex flex-column"
      >
        <div>
          <v-list-item>
            <template #prepend>
              <s-btn-icon
                v-if="notificationStore.enabled"
                @click="notificationStore.enabled = false"
                icon="mdi-bell"
                v-tooltip="'Mute notifications (temporarily for session)'"
                density="compact"
              />
              <s-btn-icon
                v-else
                @click="notificationStore.enabled = true"
                icon="mdi-bell-off"
                v-tooltip="'Unmute notifications'"
                density="compact"
              />
            </template>
            <template #default>
              <v-list-item-title class="text-h6">
                <nuxt-link to="/users/self/notifications/" class="title-link">Notifications</nuxt-link>
              </v-list-item-title>
            </template>
            <template #append v-if="notificationStore.unreadNotificationCount > 0">
              <s-btn-icon
                @click="markAllAsRead"
                icon="mdi-checkbox-blank-outline"
                density="compact"
                v-tooltip="'Mark all notifications as read'"
              />
            </template>
          </v-list-item>
          <v-divider />
        </div>

        <div class="flex-grow-1 overflow-y-auto">
          <v-list-item
            v-if="notificationStore.groupedNotifications.length === 0"
            title="No new notifications"
          />

          <template v-for="group in notificationStore.groupedNotifications" :key="group.key">
            <v-list-item 
              v-if="!group.isGroup"
              :value="group.notification.id"
              :title="group.notification.content.title"
              :subtitle="group.notification.content.text"
              :href="group.notification.content.link_url || undefined"
              target="_blank"
              @click="markAsRead(group.notification)"
              link
              lines="two"
            >
              <template #append>
                <s-btn-icon @click.stop.prevent="markAsRead(group.notification)" icon="mdi-checkbox-blank-outline" density="compact" />
              </template>
            </v-list-item>
            <v-list-group v-else :value="group.key">
              <template #activator="{ props: listGroupProps}">
                <v-list-item
                  :title="group.label"
                  prepend-icon="mdi-file-document"
                  v-bind="listGroupProps"
                />
              </template>
              <v-list-item
                v-for="notification in group.notifications"
                :key="notification.id"
                :value="notification.id"
                :href="notification.content.link_url || undefined"
                target="_blank"
                @click="markAsRead(notification)"
                link
                :lines="false"
                class="pt-0 pb-0"
              >
                <v-list-item-title class="text-body-2">{{ notification.content.title }}</v-list-item-title>
                <template #append>
                  <s-btn-icon @click.stop.prevent="markAsRead(notification)" icon="mdi-checkbox-blank-outline" density="compact" />
                </template>
              </v-list-item>
            </v-list-group>
          </template>
        </div>
        
      </v-list>
    </v-menu>
  </s-btn-icon>
</template>

<script setup lang="ts">
import { renderDOMHead } from '@unhead/vue/client'

const notificationStore = useNotificationStore();

const closedGroups = ref<string[]>([]);
const openGroups = computed(() => notificationStore.groupedNotifications.filter(g => !closedGroups.value.includes(g.key)).map(g => g.key));

// Regularly refresh notifications
const intervalControls = useIntervalFn(async () => notificationStore.fetchNotifications(), 5 * 60 * 1000, { immediateCallback: true });
watch(() => notificationStore.enabled, (enabled) => {
  if (enabled) {
    intervalControls.resume();
  } else {
    intervalControls.pause();
  }
}, { immediate: true });

async function onOpenMenu(value: boolean) {
  if (value) {
    await notificationStore.fetchNotifications();
  }
}


async function markAsRead(notification: UserNotification) {
  try {
    await notificationStore.markAsRead(notification, true);
  } catch (error: any) {
    requestErrorToast({ error });
  }
}

async function markAllAsRead() {
  try {
    await notificationStore.markAllAsRead();
  } catch (error: any) {
    requestErrorToast({ error });
  }
}

function onOpenGroup(event: {id: unknown, value: unknown}) {
  const groupKey = event.id as string;
  if (event.value) {
    closedGroups.value = closedGroups.value.filter(g => g !== groupKey);
  } else {
    closedGroups.value.push(groupKey);
  }
}


const nuxtApp = useNuxtApp();
const head = nuxtApp.vueApp._context.provides.usehead
watch([() => notificationStore.unreadNotificationCount, () => notificationStore.enabled], () => {
  // Nuxt does not reactively update the page title when unreadNotificationCount changes
  // So we manually update it here
  renderDOMHead(head);
});

</script>

<style lang="scss" scoped>
.menu-max-height {
  max-height: 90vh;
}

.v-list-item:deep(.v-list-item__prepend .v-list-item__spacer) {
  width: 0.5em;
}
.v-list-group {
  --prepend-width: 0.5em !important;
}

.title-link {
  text-decoration: none;
  color: inherit;

  &:hover {
    color: rgba(var(--v-theme-primary));
  }
}
</style>

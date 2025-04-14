<template>
  <list-view url="/api/v1/pentestusers/self/notifications/?order=-created">
    <template #title>Notifications</template>
    <template #searchbar><div /></template>
    <template #item="{item}: {item: UserNotification}">
      <v-list-item
        :value="item.id"
        :title="item.content.title"
        :subtitle="item.content.text"
        :href="item.content.link_url || undefined"
        target="_blank"
        @click="markAsRead(item, true)"
        link
        lines="two"
      >
        <template #default>
          <chip-created :value="item.created" />
          <v-chip v-if="item.content.project_name" size="small">
            <v-icon size="small" start icon="mdi-file-document" />
            {{ item.content.project_name }}
          </v-chip>
        </template>
        <template #append>
          <s-btn-icon 
            @click.stop.prevent="markAsRead(item, !item.read)" 
            :icon="item.read ? 'mdi-checkbox-outline' : 'mdi-checkbox-blank-outline'"
          />
        </template>
      </v-list-item>
    </template>
  </list-view>
</template>

<script setup lang="ts">
definePageMeta({
  title: 'Notifications',
})

const notificationStore = useNotificationStore();
async function markAsRead(notification: UserNotification, read: boolean) {
  try {
    await notificationStore.markAsRead(notification, read);
  } catch (error: any) {
    requestErrorToast({ error });
  }
}
</script>

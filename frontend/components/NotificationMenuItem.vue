<template>
  <v-menu :close-on-content-click="false" max-width="500px" bottom offset-y>
    <template #activator="{attrs: menuAttrs, on: menuOn}">
      <s-btn v-bind="menuAttrs" v-on="menuOn" icon dark>
        <v-badge v-if="unreadNotificationCount > 0" color="primary" :content="unreadNotificationCount" overlap>
          <v-icon>mdi-bell-outline</v-icon>
        </v-badge>
        <v-icon v-else>mdi-bell-outline</v-icon>
      </s-btn>
    </template>
    <template #default>
      <v-list>
        <v-list-item 
          v-for="notification in notifications" 
          :key="notification.id" 
          :href="notification.content.link_url" 
          target="_blank" 
          @click="markAsRead(notification)" 
          link 
          two-line
        >
          <v-list-item-content>
            <v-list-item-title>{{ notification.content.title }}</v-list-item-title>
            <div class="text-caption">{{ notification.content.text }}</div>
          </v-list-item-content>
          <v-list-item-action>
            <s-btn v-if="!notification.read" @click.stop.prevent="markAsRead(notification)" icon>
              <v-icon>mdi-checkbox-blank-outline</v-icon>
            </s-btn>
            <s-btn v-else disabled icon>
              <v-icon>mdi-checkbox-marked-outline</v-icon>
            </s-btn>
          </v-list-item-action>
        </v-list-item>
        <v-list-item v-if="notifications.length === 0">
          <v-list-item-title>No notifications</v-list-item-title>
        </v-list-item>
      </v-list>
    </template>
  </v-menu>
</template>

<script>
export default {
  data() {
    return {
      notifications: [],
      originalTitleTemplate: this.$root.$options.head.titleTemplate,
    };
  },
  async fetch() {
    this.notifications = (await this.$axios.$get('/pentestusers/self/notifications/')).results;
  },
  computed: {
    unreadNotificationCount() {
      return this.notifications.filter(n => !n.read).length;
    },
  },
  watch: {
    unreadNotificationCount: {
      immediate: true,
      handler(val) {
        // Update notification count in title
        this.$root.$options.head.titleTemplate = title => this.originalTitleTemplate(title) + (val > 0 ? ` (${val})` : '');
        this.$meta().refresh();
      }
    },
  },
  beforeDestroy() {
    // Remove notification count from title, because we can no longer update it.
    // This prevents a wrong notification count in title after the user has logged out.
    this.$root.$options.head.titleTemplate = this.originalTitleTemplate;
    this.$meta().refresh();
  },
  methods: {
    async markAsRead(notification) {
      if (!notification.read) {
        try {
          await this.$axios.$patch(`/pentestusers/self/notifications/${notification.id}/`, {
            read: true
          });
          notification.read = true;
        } catch (error) {
          this.$toast.global.requestError({ error });
        }
      }
    },
  }
}
</script>

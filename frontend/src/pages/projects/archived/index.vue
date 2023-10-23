<template>
  <full-height-page>
    <template #header>
      <s-sub-menu>
        <v-tab to="/projects/" exact text="Active Projects" />
        <v-tab to="/projects/finished/" text="Finished Projects" />
        <v-tab to="/projects/archived/" text="Archived Projects" />
      </s-sub-menu>
    </template>

    <list-view url="/api/v1/archivedprojects/">
      <template #title>Archived Projects</template>
      <template #item="{item}: { item: ArchivedProject}">
        <v-list-item :to="`/projects/archived/${item.id}/`" lines="two">
          <v-list-item-title> {{ item.name }}</v-list-item-title>

          <v-list-item-subtitle>
            <chip-created :value="item.created" />
            <chip-auto-delete :value="item.auto_delete_date" />

            <v-chip size="small" class="ma-1">
              <v-icon v-if="item.key_parts.some(p => !p.user.is_active) && item.key_parts.filter(p => p.user.is_active).length < item.threshold * 2" size="small" start color="warning" icon="mdi-alert" />
              {{ item.threshold }} / {{ item.key_parts.length }}

              <s-tooltip activator="parent">
                {{ item.threshold }} of {{ item.key_parts.length }} users are required to restore this project
              </s-tooltip>
            </v-chip>

            <v-chip
              v-for="keypart in item.key_parts" :key="keypart.id"
              class="ma-1" size="small"
            >
              <v-icon v-if="keypart.is_decrypted" size="small" start color="success" icon="mdi-lock-open-variant" />
              <v-icon v-else size="small" start color="red" icon="mdi-lock" />
              {{ keypart.user.username }}

              <s-tooltip activator="parent">
                <span v-if="keypart.is_decrypted">{{ keypart.user.username }} already restored their part</span>
                <span v-else>{{ keypart.user.username }}'s part is still encrypted</span>
              </s-tooltip>
            </v-chip>

            <chip-tag v-for="tag in item.tags" :key="tag" :value="tag" class="mt-2" />
          </v-list-item-subtitle>
        </v-list-item>
      </template>
    </list-view>
  </full-height-page>
</template>

<script setup lang="ts">
definePageMeta({
  title: 'Projects',
})
</script>

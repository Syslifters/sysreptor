<template>
  <template v-if="token.is_project_restricted">
    <v-chip size="small" class="ml-3">{{ token.read_only ? 'Read only' : 'Read/write' }}</v-chip>
    <v-chip v-for="project in token.projects" :key="project" size="small" class="ml-1">
      {{ token.project_details.find(p => p.id === project)?.name || 'Unavailable project' }}
    </v-chip>
    <v-chip v-if="token.projects.length === 0" size="small" class="ml-1">Restricted — no projects remaining</v-chip>
  </template>
</template>

<script setup lang="ts">
defineProps<{ token: ApiToken }>();
</script>

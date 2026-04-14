<template>
  <s-select
    :model-value="currentItem.value"
    :items="props.items"
    item-title="title"
    item-value="value"
    density="compact"
    rounded="xl"
    menu-icon=""
    class="navigation-dropdown"
  >
    <template #selection="{ item }">
      <div class="d-flex align-center ga-2">
        <v-icon v-if="item.icon" size="small" :icon="item.icon" />
        <span class="navigation-dropdown-title">
          {{ item.title }}
        </span>
      </div>
    </template>
    <template #item="{ item }">
      <v-list-item
        :value="item.value"
        :to="item.to"
        :prepend-icon="item.icon"
        :disabled="item.disabled"
        :active="item.value === currentItem.value"
        density="compact"
      >
        <template #prepend v-if="item.icon">
          <v-icon size="small" :icon="item.icon" />
        </template>
        <template #title>
          <pro-info v-if="item.proInfo">{{ item.title }}</pro-info>
          <span v-else>{{ item.title }}</span>
        </template>
      </v-list-item>
    </template>

    <template #prepend-inner v-if="prevItem">
      <s-btn-icon
        :to="prevItem.to"
        density="compact"
      >
        <v-icon icon="mdi-chevron-left" />
        <s-tooltip activator="parent" location="top">
          <v-icon v-if="prevItem.icon" start :icon="prevItem.icon" />
          <span>{{ prevItem.title }}</span>
        </s-tooltip>
      </s-btn-icon>
    </template>
    <template #append-inner v-if="nextItem">
      <s-btn-icon
        :to="nextItem.to"
        density="compact"
      >
        <v-icon icon="mdi-chevron-right" />
        <s-tooltip activator="parent" location="top">
          <v-icon v-if="nextItem.icon" start :icon="nextItem.icon" />
          <span>{{ nextItem.title }}</span>
        </s-tooltip>
      </s-btn-icon>
    </template>
  </s-select>
</template>

<script setup lang="ts">
import type { RouteLocationRaw } from '#vue-router';

const props = defineProps<{
  value: string;
  items: {
    value: string;
    to: RouteLocationRaw;
    title: string;
    icon?: string;
    disabled?: boolean;
    proInfo?: boolean;
  }[];
}>();

const currentItem = computed(() => props.items.find(item => item.value === props.value) ?? props.items.at(0)!);
const currentIndex = computed(() => props.items.findIndex(item => item.value === currentItem.value.value));
const prevItem = computed(() => props.items.at(currentIndex.value - 1));
const nextItem = computed(() => props.items.at((currentIndex.value + 1) % props.items.length));
</script>

<style lang="scss" scoped>
.navigation-dropdown {
  min-width: 11em
}

.navigation-dropdown:deep() {
  .v-select__selection {
    display: flex;
    flex-direction: column;
    justify-content: center;
    width: 100%;
  }

  .v-field {
    padding-left: 0.5em;
    padding-right: 0.5em;
  }

  .v-field__append-inner {
    flex-direction: row-reverse;
  }

  .v-btn .v-icon {
    opacity: var(--v-medium-emphasis-opacity);
  }
}

:deep(.v-field) {
  padding-left: 0.5em;
  padding-right: 0.5em;
}

</style>

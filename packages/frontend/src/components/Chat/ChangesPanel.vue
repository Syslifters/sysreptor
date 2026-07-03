<template>
  <v-expansion-panels
    v-if="props.changedPages.length"
    :model-value="expanded"
    flat
    class="changes-panel"
    @update:model-value="expanded = !!$event"
  >
    <v-expansion-panel :value="true">
      <v-expansion-panel-title class="text-body-medium text-medium-emphasis">
        <v-icon icon="mdi-file-edit-outline" size="small" start />
        {{ summaryText }}
      </v-expansion-panel-title>
      <v-expansion-panel-text>
        <v-list density="compact" class="bg-transparent py-0">
          <v-list-item
            v-for="page in props.changedPages"
            :key="page.filePath"
            :to="getChangedPagePath(props.project.id, page)"
            class="px-2 py-1 min-h-0"
          >
            <template #prepend>
              <v-icon
                :icon="page.type === 'note' ? 'mdi-note-text-outline' : 'mdi-file-document-outline'"
                size="x-small"
              />
            </template>
            <v-list-item-title class="text-body-medium text-truncate">  
              {{ page.title }}
              <span v-if="page.isCreated" class="text-disabled ml-1">(new)</span>
            </v-list-item-title>
            <template #append>
              <div class="d-flex align-center ga-3">
                <s-btn-icon
                  @click.prevent.stop="emit('revert', page)"
                  icon="mdi-undo"
                  :disabled="props.readonly"
                  size="x-small"
                  density="compact"
                  v-tooltip.top="page.isCreated ? 'Delete' : 'Revert changes'"
                />
                <s-btn-icon
                  @click.prevent.stop="emit('accept', page.filePath)"
                  icon="mdi-check"
                  :disabled="props.readonly"
                  size="x-small"
                  density="compact"
                  v-tooltip.top="'Accept changes'"
                />
              </div>
            </template>
          </v-list-item>
        </v-list>
      </v-expansion-panel-text>
    </v-expansion-panel>
  </v-expansion-panels>
</template>

<script setup lang="ts">
import { getChangedPagePath, type AgentChangedPage } from '@/utils/agent';

const props = defineProps<{
  project: PentestProject;
  changedPages: AgentChangedPage[];
  readonly?: boolean;
}>();

const emit = defineEmits<{
  revert: [page: AgentChangedPage];
  accept: [filePath: string];
}>();

const expanded = ref(false);

const summaryText = computed(() => {
  const count = props.changedPages.length;
  return count === 1 ? 'Changed 1 page' : `Changed ${count} pages`;
});
</script>

<style lang="scss" scoped>
.changes-panel {
  border-bottom: thin solid rgba(var(--v-border-color), var(--v-border-opacity));
  background: rgba(var(--v-theme-on-surface), 0.03);
}

.changes-panel:deep() {
  .v-expansion-panel {
    background-color: transparent;
  }

  .v-expansion-panel-title {
    min-height: 0;
    padding: 0.5rem 0.75rem;
  }

  .v-expansion-panel-text__wrapper {
    padding-top: 0;
    padding-bottom: 0.25rem;
    padding-left: 0;
    padding-right: 0;
  }

  .v-list-item {
    min-height: 0;
    padding-left: 1em;
    padding-right: 1em;
  }

  .v-list-item__prepend {
    .v-list-item__spacer {
      width: 0.5rem;
    }
  }
  .v-list-item__append {
    margin-inline-start: 0.5rem;
  }
  .v-list-item-title {
    color: rgb(var(--v-theme-primary));
  }
}
</style>

<template>
  <v-list density="compact" class="pb-0 h-100 d-flex flex-column">
    <v-list-subheader>
      <span>{{ props.title || 'Notes' }}</span>
      <s-btn-icon
        @click="createNoteBtnRef?.click()"
        :disabled="!canCreate"
        size="small"
        variant="flat"
        color="secondary"
        density="compact"
        class="ml-2"
      >
        <v-icon icon="mdi-plus" />
        <s-tooltip activator="parent" location="top">Add Note (Ctrl+J)</s-tooltip>
      </s-btn-icon>
      <v-spacer />
      <s-btn-icon v-if="props.exportUrl || props.performImport" size="small" density="compact">
        <v-icon icon="mdi-dots-vertical" />
        <v-menu activator="parent" :close-on-content-click="false" location="bottom right" class="context-menu">
          <v-list>
            <btn-import 
              v-if="props.performImport"
              :import="performImport"
              :disabled="props.readonly"
              button-variant="list-item"
            />
            <btn-export
              v-if="props.exportUrl"
              button-text="Export All"
              :export-url="props.exportUrl"
              :name="props.exportName"
              :disabled="props.readonly"
            />
          </v-list>
        </v-menu>
      </s-btn-icon>
    </v-list-subheader>

    <div class="flex-grow-1 overflow-y-auto">
      <slot name="default" />
    </div>

    <div>
      <v-divider />
      <v-list-item>
        <btn-confirm
          ref="createNoteBtnRef"
          :action="createNote"
          :disabled="!canCreate"
          :confirm="false"
          button-text="Add"
          button-icon="mdi-plus"
          tooltip-text="Add Note (Ctrl+J)"
          keyboard-shortcut="ctrl+j"
          size="small"
          block
        />
      </v-list-item>
    </div>
  </v-list>
</template>

<script setup lang="ts">
const props = defineProps<{
  title?: string;
  readonly?: boolean;
  createNote?: () => Promise<void>;
  exportUrl?: string;
  exportName?: string;
  performImport?: (file: File) => Promise<void>;
}>();

const createNoteBtnRef = ref();
const canCreate = computed(() => !props.readonly && !!props.createNote);
</script>

<style lang="scss" scoped>
@use "@/assets/vuetify" as vuetify;

:deep(.v-list-subheader) {
  padding-left: 0.5em !important;

  .v-list-subheader__text {
    display: flex;
    flex-direction: row;
    width: 100%;
  }
}

:deep(.v-list-item__prepend > .v-progress-circular ~ .v-list-item__spacer) {
  width: vuetify.$list-item-icon-margin-start;
}
</style>

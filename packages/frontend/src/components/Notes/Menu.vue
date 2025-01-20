<template>
  <file-drop-area 
    @drop="importBtnRef?.performImport($event)"
    :disabled="props.readonly || !props.performImport" 
    class="h-100"
  >
    <v-list density="compact" class="pb-0 pt-0 h-100 d-flex flex-column">
      <v-list-subheader v-if="!isInSearchMode">
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
        <s-btn-icon
          v-if="search !== undefined"
          @click="showSearch"
          icon="mdi-magnify"
          size="small"
          density="compact"
          class="ml-2"
        />
        <s-btn-icon v-if="props.exportUrl || props.performImport" size="small" density="compact">
          <v-icon icon="mdi-dots-vertical" />
          <v-menu activator="parent" eager :close-on-content-click="false" location="bottom right" class="context-menu">
            <v-list>
              <btn-import 
                v-if="props.performImport"
                ref="importBtnRef"
                :import="props.performImport"
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
      <v-list-subheader v-else class="mt-0">
        <s-text-field 
          v-model="search"
          placeholder="Search..."
          density="compact"
          variant="underlined"
          prepend-inner-icon="mdi-magnify"
          append-inner-icon="$clear"
          @click:append-inner="hideSearch"
          autofocus
        >
          <template #prepend-inner-icon>
            <v-icon icon="mdi-magnify" size="small" />
          </template>
          <template #append-inner-icon>
            <v-icon icon="mdi-close" size="small" />
          </template>
        </s-text-field>
      </v-list-subheader>

      <div class="flex-grow-1 overflow-y-auto">
        <slot 
          v-if="isInSearchMode && (search?.length || 0) >= 3"
          name="search"
          :search="search!"
        />
        <slot 
          v-else 
          name="default" 
        />
      </div>

      <div>
        <v-divider />
        <v-list-item>
          <btn-confirm
            ref="createNoteBtnRef"
            :action="props.createNote!"
            :disabled="!canCreate"
            :confirm="false"
            data-testid="create-note"
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
  </file-drop-area>
</template>

<script setup lang="ts">
const search = defineModel<string|null>('search');
const props = defineProps<{
  title?: string;
  readonly?: boolean;
  createNote?: () => Promise<void>;
  exportUrl?: string;
  exportName?: string;
  performImport?: (file: File) => Promise<void>;
}>();

const importBtnRef = ref();

const createNoteBtnRef = ref();
const canCreate = computed(() => !props.readonly && !!props.createNote);
const isInSearchMode = computed(() => search.value !== null);

function showSearch() {
  search.value = '';
}
function hideSearch() {
  search.value = null;
}

useKeyboardShortcut('ctrl+shift+f', () => showSearch());
</script>

<style lang="scss" scoped>
@use "@base/assets/vuetify" as vuetify;

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

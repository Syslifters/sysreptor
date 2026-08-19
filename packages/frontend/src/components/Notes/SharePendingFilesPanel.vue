<template>
  <div>
    <div v-if="loading" class="d-flex justify-center pa-8">
      <v-progress-circular indeterminate size="50" />
    </div>

    <template v-else-if="pendingItems.length > 0">
      <div class="d-flex align-center justify-space-between mb-2">
        <s-btn-icon
          @click="windowRef?.group?.prev()"
          :disabled="pendingItems.length <= 1"
          icon="mdi-chevron-left"
          density="comfortable"
        />
        <span class="text-body-medium">{{ currentIndex + 1 }} / {{ pendingItems.length }}</span>
        <s-btn-icon
          @click="windowRef?.group?.next()"
          :disabled="pendingItems.length <= 1"
          icon="mdi-chevron-right"
          density="comfortable"
        />
      </div>

      <v-window
        ref="windowRef"
        v-model="currentFileId"
        :show-arrows="pendingItems.length > 1"
        :continuous="true"
        class="pending-files-window"
      >
        <v-window-item
          v-for="item in pendingItems"
          :key="item.fileId"
          :value="item.fileId"
        >
          <s-card density="compact">
            <div v-if="item.file && fileApiBaseUrls && isImageFile(item.file)" class="preview-container bg-surface-container">
              <v-img
                :src="filePreviewUrl(item.file, fileApiBaseUrls)"
                :alt="item.file.name"
                max-height="360"
                contain
                class="bg-surface-container h-100 w-100"
              />
            </div>
            <div v-else-if="item.file" class="preview-container bg-surface-container d-flex flex-column align-center justify-center pa-8">
              <v-icon icon="mdi-file-outline" size="72" class="mb-2" />
              <span class="text-body-large text-center">{{ item.file.name }}</span>
            </div>
            <div v-else class="preview-container bg-surface-container d-flex align-center justify-center pa-8">
              <v-chip color="warning" prepend-icon="mdi-alert-outline">
                File unavailable ({{ item.fileId.slice(0, 8) }}…)
              </v-chip>
            </div>

            <v-card-text v-if="item.file">
              <div class="d-flex align-center flex-wrap ga-2">
                <span class="text-body-large font-weight-medium">{{ item.file.name }}</span>
                <chip-created :value="item.file.created" />
              </div>
            </v-card-text>

            <v-card-actions class="flex-wrap">
              <template v-if="item.file && fileApiBaseUrls">
                <s-btn-icon
                  icon="mdi-download"
                  :href="filePreviewUrl(item.file, fileApiBaseUrls)"
                  download
                  density="comfortable"
                  variant="text"
                  v-tooltip="'Download'"
                />
                <s-btn-icon
                  v-if="isImageFile(item.file)"
                  icon="mdi-open-in-new"
                  :href="filePreviewUrl(item.file, fileApiBaseUrls)"
                  target="_blank"
                  density="comfortable"
                  variant="text"
                  v-tooltip="'Open in new tab'"
                />
              </template>
              <v-spacer />
              <btn-confirm
                :action="() => approveFiles([item.fileId])"
                :disabled="props.readonly || props.approving"
                :loading="props.approving"
                :confirm="false"
                button-text="Approve"
                button-icon="mdi-check"
                button-color="primary-bg"
              />
              <btn-confirm
                v-if="pendingItems.length > 1"
                :action="approveAll"
                :disabled="props.readonly || props.approving"
                :loading="props.approving"
                :confirm="true"
                :dialog-title="'Approve all shared files?'"
                :dialog-text="`Visitors will be able to see and download all ${pendingItems.length} shared files on this share link.`"
                :button-text="`Approve all (${pendingItems.length})`"
                button-icon="mdi-check-all"
                button-color="primary-bg"
              />
            </v-card-actions>
          </s-card>
        </v-window-item>
      </v-window>
      <p class="text-body-medium text-medium-emphasis mb-4">
        Visitors cannot see or download these files until you approve them.
      </p>
    </template>
  </div>
</template>

<script setup lang="ts">
import {
  fetchUploadedFileById,
  filePreviewUrl,
  isImageFile,
  type FileApiBaseUrls,
} from '~/utils/files';

type PendingItem = {
  fileId: string;
  file: UploadedFileInfo | null;
};

const props = defineProps<{
  shareInfo: ShareInfo;
  fileApiBaseUrls: FileApiBaseUrls | null;
  readonly?: boolean;
  approving?: boolean;
}>();

const emit = defineEmits<{
  approve: [fileIds: string[]];
}>();

const windowRef = useTemplateRef('windowRef');
const loading = ref(false);
const pendingItems = ref<PendingItem[]>([]);
const currentFileId = ref<string | null>(null);

const currentIndex = computed(() => {
  if (!currentFileId.value) {
    return 0;
  }
  const idx = pendingItems.value.findIndex(item => item.fileId === currentFileId.value);
  return idx >= 0 ? idx : 0;
});

function isTypingTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) {
    return false;
  }
  return target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName);
}

function handleWindowKeydown(event: KeyboardEvent) {
  if (pendingItems.value.length <= 1 || isTypingTarget(event.target)) {
    return;
  }

  if (event.key === 'ArrowLeft') {
    event.preventDefault();
    windowRef.value?.group?.prev();
  } else if (event.key === 'ArrowRight') {
    event.preventDefault();
    windowRef.value?.group?.next();
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleWindowKeydown);
});

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleWindowKeydown);
});

async function loadPendingItems() {
  const fileIds = props.shareInfo.pending_file_ids ?? [];
  if (fileIds.length === 0) {
    pendingItems.value = [];
    currentFileId.value = null;
    return;
  }

  if (!props.fileApiBaseUrls) {
    pendingItems.value = fileIds.map(fileId => ({ fileId, file: null }));
    currentFileId.value = fileIds[0] ?? null;
    return;
  }

  loading.value = true;
  try {
    const items = await Promise.all(fileIds.map(async (fileId): Promise<PendingItem> => {
      try {
        const file = await fetchUploadedFileById(
          props.fileApiBaseUrls!.imagesBase,
          props.fileApiBaseUrls!.filesBase,
          fileId,
        );
        return { fileId, file };
      } catch {
        return { fileId, file: null };
      }
    }));
    pendingItems.value = items;
    if (!items.some(item => item.fileId === currentFileId.value)) {
      currentFileId.value = items[0]?.fileId ?? null;
    }
  } finally {
    loading.value = false;
  }
}

watch(() => props.shareInfo.pending_file_ids, () => {
  loadPendingItems();
}, { immediate: true, deep: true });

function approveFiles(fileIds: string[]) {
  if (fileIds.length === 0) {
    return;
  }
  emit('approve', fileIds);
}

function approveAll() {
  approveFiles(props.shareInfo.pending_file_ids ?? []);
}
</script>

<style lang="scss" scoped>
.preview-container {
  min-height: 22.5rem;
  height: 22.5rem;
}

:deep(.pending-files-window) {
  .v-window__controls {
    padding: 0;
  }
}
</style>

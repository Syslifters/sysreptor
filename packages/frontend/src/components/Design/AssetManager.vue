<template>
  <file-drop-area multiple :disabled="props.disabled" @drop="performFileUpload" class="h-100">
    <!-- Upload files with drag-and-drop here -->
    <v-row class="ma-0">
      <v-col :cols="12" :md="3">
        <s-card>
          <v-card-actions>
            <s-btn-secondary
              :disabled="props.disabled || uploadInProgress"
              :loading="uploadInProgress"
              @click="($refs.fileInput as unknown as HTMLInputElement).click()"
              block
              prepend-icon="mdi-upload"
              text="Upload"
            >
              <template #loader>
                <s-saving-loader-spinner />
                Uploading
              </template>
            </s-btn-secondary>
            <input
              ref="fileInput"
              type="file"
              multiple
              @change="performFileUpload(($event.target as HTMLInputElement)?.files)"
              :disabled="disabled || uploadInProgress"
              class="d-none"
            />
          </v-card-actions>
          <v-card-text class="text--small text-center pt-0">
            Attach files via drag and drop
          </v-card-text>
        </s-card>
      </v-col>

      <v-col v-for="asset in assets.data.value" :key="asset.id" :cols="12" :md="3">
        <s-card density="compact">
          <v-img v-if="isImage(asset)" alt="" :src="absoluteAssetUrl(asset)" aspect-ratio="2" />
          <v-card-title>{{ asset.name }}</v-card-title>
          <v-card-text class="text--small pb-0">
            {{ assetUrl(asset) }}
            <s-btn-icon @click="copyToClipboard(assetUrl(asset))" size="small" density="compact">
              <v-icon size="small" icon="mdi-content-copy" />
              <s-tooltip activator="parent" text="Copy path to clipboard" />
            </s-btn-icon>
          </v-card-text>
          <v-card-actions>
            <s-btn-icon :href="absoluteAssetUrl(asset)" download density="comfortable">
              <v-icon icon="mdi-download" />
              <s-tooltip activator="parent" text="Download asset" />
            </s-btn-icon>
            <s-btn-icon :href="absoluteAssetUrl(asset)" target="_blank" density="comfortable">
              <v-icon icon="mdi-open-in-new" />
              <s-tooltip activator="parent" text="Show image in new tab" />
            </s-btn-icon>
            <v-spacer />
            <btn-delete
              :delete="() => performDelete(asset)"
              :disabled="disabled"
              button-variant="icon"
              density="comfortable"
            />
          </v-card-actions>
        </s-card>
      </v-col>

      <v-col v-if="assets.hasNextPage.value" :cols="12" :md="3">
        <v-card>
          <v-card-text>
            <page-loader :items="assets" />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </file-drop-area>
</template>

<script setup lang="ts">
import { last } from 'lodash-es';
import { uploadFileHelper, absoluteApiUrl } from "#imports";
import { urlJoin, uuidv4 } from "@base/utils/helpers";

const props = defineProps<{
  projectType: ProjectType;
  disabled?: boolean;
}>();

const assets = useSearchableCursorPaginationFetcher<UploadedFileInfo>({
  baseURL: `/api/v1/projecttypes/${props.projectType.id}/assets/`
})

const uploadInProgress = ref(false);
const fileInput = ref();
async function uploadSingleFile(file: File) {
  try {
    const asset = await uploadFileHelper<UploadedFileInfo>(`/api/v1/projecttypes/${props.projectType.id}/assets/`, file);
    assets.data.value.unshift(asset);
  } catch (error) {
    requestErrorToast({ error, message: 'Failed to upload ' + file.name });
  }
}
async function performFileUpload(files?: File[]|FileList|null) {
  if (uploadInProgress.value || props.disabled || !files) {
    return;
  }

  try {
    uploadInProgress.value = true;

    // upload all files
    await Promise.all(Array.from(files).map(uploadSingleFile));
  } finally {
    // clear file input
    fileInput.value = null;
    uploadInProgress.value = false;
  }
}

const cacheBuster = ref(uuidv4());
function isImage(asset: UploadedFileInfo) {
  // Detect file type by extension
  // Used for displaying image previews
  return ['jpg', 'jpeg', 'png', 'gif', 'svg'].includes(last(asset.name.split('.')) || '')
}
function assetUrl(asset: UploadedFileInfo) {
  return `/assets/name/${asset.name}`;
}
function absoluteAssetUrl(asset: UploadedFileInfo) {
  return absoluteApiUrl(urlJoin(`/api/v1/projecttypes/${props.projectType.id}/`, assetUrl(asset)) + `?c=${cacheBuster.value}`);
}

async function performDelete(asset: UploadedFileInfo) {
  await $fetch(`/api/v1/projecttypes/${props.projectType.id}/assets/${asset.id}/`, {
    method: 'DELETE'
  });
  assets.data.value = assets.data.value.filter(a => a.id !== asset.id);
}
</script>

<style lang="scss" scoped>
.text--small {
  font-size: smaller;
}
</style>

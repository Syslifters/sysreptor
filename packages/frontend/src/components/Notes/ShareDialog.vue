<template>
  <s-dialog
    v-if="isVisible"
    v-model="isVisible"
    :min-width="mdAndDown ? '90vw' : '60vw'"
    height="80vh"
  >
    <template #title>Share Note</template>
    <template #default>
      <split-menu :model-value="shareInfos.length > 0 ? 200 : 0" :class="{'split-menu-noexpand': shareInfos.length === 0}">
        <template #menu>
          <v-list
            v-model:selected="currentShareInfoSelection"
            mandatory
            density="compact"
            class="pb-0 pt-0 h-100 d-flex flex-column"
          >
            <div class="flex-grow-1 overflow-y-auto">
              <v-list-item
                v-for="shareInfo in shareInfos"
                :key="shareInfo.id"
                :value="shareInfo.id"
                :title="shareInfo.comment || undefined"
                prepend-icon="mdi-share-variant"
                lines="three"
                class="pl-2"
              >
                <template #subtitle>
                  <chip-created :value="shareInfo.created" />
                  <v-chip v-if="shareInfo.is_revoked" color="error" size="small">Revoked</v-chip>
                  <chip-expires :value="shareInfo.expire_date" />
                </template>
              </v-list-item>
            </div>
            <div>
              <v-divider class="mb-1" />
              <v-list-item>
                <s-btn-secondary
                  @click="openCreateForm"
                  :disabled="props.readonly"
                  text="Share"
                  prepend-icon="mdi-share-variant"
                  size="small"
                  block
                />
              </v-list-item>
            </div>
          </v-list>
        </template>
        <template #default>
          <v-container fluid>
            <div v-if="currentShareInfo">
              <notes-share-info-form
                v-model="currentShareInfo"
                :disabled="props.readonly"
              />
              <btn-confirm
                :action="() => updateShareInfo(currentShareInfo!)"
                :disabled="props.readonly || (isEqual(currentShareInfo, shareInfos.find(si => si.id === currentShareInfo?.id)))"
                :confirm="false"
                button-text="Update"
                button-icon="mdi-content-save"
                button-color="primary-bg"
                class="mt-4"
              />
            </div>
            <div v-else-if="createShareInfoForm">
              <notes-share-info-form
                v-model="createShareInfoForm.data"
                :disabled="createShareInfoForm.saveInProgress || props.readonly"
                :error="createShareInfoForm.error"
                :hidden-fields="['is_revoked']"
              />
              <btn-confirm
                :action="createShareInfo"
                :disabled="createShareInfoForm.saveInProgress || props.readonly"
                :loading="createShareInfoForm.saveInProgress"
                :confirm="false"
                button-text="Share"
                button-icon="mdi-share-variant"
                button-color="primary-bg"
                class="mt-4"
              />
            </div>
            <div v-else-if="isListLoading" class="mt-4 d-flex flex-column align-center">
              <v-progress-circular indeterminate size="50" />
            </div>
            <div v-else>
              <v-alert v-if="!apiSettings.settings!.features.sharing" color="warning">
                Note sharing is disabled in instance settings.
              </v-alert>
              <v-alert v-else color="warning">
                You do not have permission to share notes.
              </v-alert>
            </div>
          </v-container>
        </template>
      </split-menu>
    </template>
  </s-dialog>
</template>

<script setup lang="ts">
import { isEqual } from 'lodash-es';
import { addDays, formatISO9075 } from "date-fns";

const apiSettings = useApiSettings();
const { mdAndDown } = useDisplay();

const isVisible = defineModel<boolean>();
const props = defineProps<{
  note: NoteBase;
  project?: PentestProject;
  user?: User;
  readonly?: boolean;
}>();

const shareInfos = ref<ShareInfo[]>([]);
const isListLoading = ref(false);
const currentShareInfo = ref<ShareInfo|null>(null);
const currentShareInfoSelection = computed({
  get: () => {
    const current = shareInfos.value.find(si => si.id === currentShareInfo.value?.id);
    return current ? [current.id] : [];
  },
  set: (value) => {
    if (value.length > 0) {
      if (currentShareInfo.value?.id !== value[0]) {
        currentShareInfo.value = shareInfos.value.find(si => si.id === value[0]) || null;
      }
    } else {
      currentShareInfo.value = null;
    }
  }
});

whenever(isVisible, updateShareInfoList);
async function updateShareInfoList() {
  try {
    isListLoading.value = true;
    if (props.project) {
      shareInfos.value = await $fetch(`/api/v1/pentestprojects/${props.project.id}/notes/${props.note.id}/shareinfos/`, { method: 'GET' });
    } else if (props.user) {
      shareInfos.value = await $fetch(`/api/v1/pentestusers/${props.user.id}/notes/${props.note.id}/shareinfos/`, { method: 'GET' });
    }
    // Automatically select the first share info
    if (shareInfos.value.length > 0) {
      currentShareInfo.value = shareInfos.value[0]!;
    } else {
      openCreateForm();
    }
  } finally {
    isListLoading.value = false;
  }
}

async function updateShareInfo(shareInfo: ShareInfo) {
  try {
    if (props.project) {
      shareInfo = await $fetch<ShareInfo>(`/api/v1/pentestprojects/${props.project.id}/notes/${props.note.id}/shareinfos/${shareInfo.id}/`, {
        method: 'PATCH',
        body: shareInfo,
      });
    } else if (props.user) {
      shareInfo = await $fetch<ShareInfo>(`/api/v1/pentestusers/${props.user.id}/notes/${props.note.id}/shareinfos/${shareInfo.id}/`, {
        method: 'PATCH',
        body: shareInfo,
      });
    }
    shareInfos.value = shareInfos.value.map(si => si.id === shareInfo.id ? shareInfo : si);
    currentShareInfo.value = shareInfo;
  } catch (error) {
    requestErrorToast({ error });
  }
}

const createShareInfoForm = ref<null|{
  data: ShareInfo;
  error?: any|null;
  saveInProgress: boolean;
}>(null);
function openCreateForm() {
  if (props.readonly) {
    return;
  }
  createShareInfoForm.value = {
    data: {
      id: '',
      shared_by: null,
      expire_date: formatISO9075(addDays(new Date(), 14), { representation: 'date' }),
      is_revoked: false,
      password: null,
      permissions_write: false,
    } as ShareInfo,
    saveInProgress: false,
  }
  currentShareInfo.value = null;
}
async function createShareInfo() {
  if (!createShareInfoForm.value) {
    return;
  }
  try {
    createShareInfoForm.value.saveInProgress = true;
    let obj: ShareInfo;
    if (props.project) {
      obj = await $fetch<ShareInfo>(`/api/v1/pentestprojects/${props.project.id}/notes/${props.note.id}/shareinfos/`, {
        method: 'POST',
        body: createShareInfoForm.value.data,
      });
    } else if (props.user) {
      obj = await $fetch<ShareInfo>(`/api/v1/pentestusers/${props.user.id}/notes/${props.note.id}/shareinfos/`, {
        method: 'POST',
        body: createShareInfoForm.value.data,
      });
    } else {
      return;
    }
    shareInfos.value.unshift(obj);
    currentShareInfo.value = obj;
    createShareInfoForm.value = null;
  } catch (error: any) {
    createShareInfoForm.value!.error = error?.data;
  } finally {
    if (createShareInfoForm.value) {
      createShareInfoForm.value.saveInProgress = false;
    }
  }
}

</script>

<style lang="scss" scoped>
:deep(.v-list-item__prepend) {
  .v-list-item__spacer {
    width: 0.5em;
  }
}
:deep(.v-list-item-subtitle) {
  opacity: 1;
}

.split-menu-noexpand:deep(.expand-button-wrapper) {
  display: none;
}
</style>

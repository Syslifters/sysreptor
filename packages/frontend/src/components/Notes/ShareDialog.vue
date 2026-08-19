<template>
  <s-dialog
    v-if="isVisible"
    v-model="isVisible"
    :min-width="lgAndDown ? '90vw' : '60vw'"
    height="80vh"
  >
    <template #title>
      <div class="d-flex align-center ga-1">
        <s-btn-icon
          v-if="dialogView === 'pending'"
          @click="dialogView = 'main'"
          icon="mdi-arrow-left"
          density="compact"
          v-tooltip="'Back to share settings'"
        />
        <span>{{ dialogView === 'pending' ? 'Review shared files' : 'Share Note' }}</span>
      </div>
    </template>
    <template #default>
      <v-divider />

      <div v-if="dialogView === 'pending' && currentShareInfo" class="overflow-y-auto">
        <v-container fluid>
          <notes-share-pending-files-panel
            :share-info="currentShareInfo"
            :file-api-base-urls="fileApiBaseUrls"
            :readonly="props.readonly || approveInProgress"
            :approving="approveInProgress"
            @approve="onApprovePendingFiles"
          />
        </v-container>
      </div>

      <split-menu
        v-else
        :model-value="260"
      >
        <template v-if="shareInfos.length > 0" #menu>
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
                density="compact"
                class="py-2 px-3"
                :class="{ 'text-medium-emphasis': shareInfo.is_revoked || isShareExpired(shareInfo) }"
              >
                <template #prepend>
                  <v-icon
                    :icon="shareInfo.is_revoked ? 'mdi-link-variant-off' : 'mdi-link-variant'"
                    :color="shareInfo.is_revoked || isShareExpired(shareInfo) ? 'error' : undefined"
                    size="small"
                  />
                </template>

                <v-list-item-title class="text-body-medium font-weight-medium">
                  <span v-if="shareInfo.comment?.trim()" class="text-truncate d-block">{{ shareInfo.comment.trim() }}</span>
                  <span v-else class="text-medium-emphasis">{{ formatShareCreated(shareInfo.created) }}</span>
                </v-list-item-title>

                <div class="d-flex flex-column ga-1 mt-1 text-body-small w-100">
                  <div
                    v-if="shareInfo.comment?.trim() || shareInfo.shared_by || shareInfo.permissions_write"
                    class="d-flex flex-wrap align-center ga-1"
                  >
                    <span v-if="shareInfo.comment?.trim()" class="text-medium-emphasis">{{ formatShareCreated(shareInfo.created) }}</span>
                    <span v-if="shareInfo.shared_by" class="text-medium-emphasis">@{{ shareInfo.shared_by.username }}</span>
                    <v-chip v-if="shareInfo.permissions_write" size="x-small" variant="tonal" label>
                      Can edit
                    </v-chip>
                  </div>
                  <div :class="shareExpiryTextClass(shareInfo)">
                    {{ formatShareExpiry(shareInfo) }}
                  </div>
                  <v-btn
                    v-if="pendingCountFor(shareInfo.id) > 0"
                    variant="tonal"
                    color="error"
                    size="x-small"
                    block
                    class="mt-1 text-caption"
                    @click.stop="openPendingReview(shareInfo)"
                  >
                    <v-icon icon="mdi-file-eye-outline" size="x-small" start />
                    {{ pendingCountFor(shareInfo.id) }} shared {{ pendingCountFor(shareInfo.id) === 1 ? 'file' : 'files' }} to review
                    <v-spacer />
                    <v-icon icon="mdi-chevron-right" size="x-small" end />
                  </v-btn>
                </div>
              </v-list-item>
              <v-list-item>
                <v-divider />
                <s-btn-secondary
                  class="mt-4"
                  @click="openCreateForm"
                  :disabled="props.readonly"
                  text="New Share Link"
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
              <s-btn-secondary
                v-if="(currentShareInfo.pending_file_ids?.length ?? 0) > 0"
                @click="openPendingReview(currentShareInfo)"
                text="Review shared files"
                prepend-icon="mdi-file-eye-outline"
                color="error"
                variant="tonal"
                class="mb-4"
              />
              <notes-share-info-form
                v-model="currentShareInfo"
                :disabled="props.readonly"
              />
              <btn-confirm
                :action="() => performUpdateShareInfo(currentShareInfo!)"
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
                :action="performCreateShareInfo"
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
              <v-sheet
                v-if="!apiSettings.settings!.features.sharing"
                color="warning"
                variant="tonal"
                class="pa-4 rounded"
              >
                Note sharing is disabled in instance settings.
              </v-sheet>
              <v-sheet
                v-else
                color="warning"
                variant="tonal"
                class="pa-4 rounded"
              >
                You do not have permission to share notes.
              </v-sheet>
            </div>
          </v-container>
        </template>
      </split-menu>
    </template>
  </s-dialog>
</template>

<script setup lang="ts">
import { isEqual } from 'lodash-es';
import { addDays, formatISO9075, formatDistanceToNow, parseISO, endOfDay, endOfToday } from "date-fns";
import { getFileApiBaseUrls } from '~/utils/files';

const apiSettings = useApiSettings();
const { lgAndDown } = useVDisplay();
const noteShareInfoStore = useNoteShareInfoStore();

const isVisible = defineModel<boolean>();
const props = defineProps<{
  note: NoteBase;
  project?: PentestProject;
  user?: User;
  readonly?: boolean;
}>();

const shareInfoContext = computed(() => ({
  noteId: props.note.id,
  projectId: props.project?.id,
  userId: props.user?.id,
}));
const shareInfos = computed(() => noteShareInfoStore.shareInfosFor(shareInfoContext.value));
const isListLoading = computed(() => noteShareInfoStore.isLoadingFor(shareInfoContext.value));
const fileApiBaseUrls = computed(() => getFileApiBaseUrls({ project: props.project, user: props.user }));
const approveInProgress = ref(false);

function pendingCountFor(shareInfoId: string): number {
  return shareInfos.value.find(si => si.id === shareInfoId)?.pending_file_ids?.length ?? 0;
}

const dialogView = ref<'main' | 'pending'>('main');
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

watch(isVisible, (visible) => {
  if (!visible) {
    dialogView.value = 'main';
  }
});

watch(() => currentShareInfo.value?.pending_file_ids?.length, (count) => {
  if (dialogView.value === 'pending' && (count ?? 0) === 0) {
    dialogView.value = 'main';
  }
});

whenever(isVisible, updateShareInfoList);
async function updateShareInfoList() {
  try {
    await noteShareInfoStore.fetchShareInfos(shareInfoContext.value);
    if (shareInfos.value.length > 0) {
      const selectedId = currentShareInfo.value?.id;
      currentShareInfo.value = selectedId
        ? shareInfos.value.find(si => si.id === selectedId) ?? shareInfos.value[0]!
        : shareInfos.value[0]!;
    } else {
      openCreateForm();
    }
  } catch (error) {
    requestErrorToast({ error });
  }
}

function openPendingReview(shareInfo: ShareInfo) {
  currentShareInfo.value = shareInfo;
  createShareInfoForm.value = null;
  dialogView.value = 'pending';
}

function formatShareCreated(created: string) {
  return formatDistanceToNow(parseISO(created)) + ' ago';
}

function isShareExpired(shareInfo: ShareInfo) {
  return endOfDay(parseISO(shareInfo.expire_date)) < endOfToday();
}

function formatShareExpiry(shareInfo: ShareInfo) {
  if (shareInfo.is_revoked) {
    return 'Revoked';
  }
  if (isShareExpired(shareInfo)) {
    return 'Expired';
  }
  return 'Expires in ' + formatDistanceToNow(parseISO(shareInfo.expire_date));
}

function shareExpiryTextClass(shareInfo: ShareInfo) {
  return shareInfo.is_revoked || isShareExpired(shareInfo) ? 'text-error' : 'text-medium-emphasis';
}

async function performUpdateShareInfo(shareInfo: ShareInfo) {
  try {
    currentShareInfo.value = await noteShareInfoStore.updateShareInfo(shareInfoContext.value, shareInfo);
  } catch (error) {
    requestErrorToast({ error });
  }
}

async function onApprovePendingFiles(fileIds: string[]) {
  if (!currentShareInfo.value || approveInProgress.value) {
    return;
  }
  approveInProgress.value = true;
  try {
    currentShareInfo.value = await noteShareInfoStore.approvePendingFiles(
      shareInfoContext.value,
      currentShareInfo.value,
      fileIds,
    );
  } catch (error) {
    requestErrorToast({ error });
  } finally {
    approveInProgress.value = false;
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
  dialogView.value = 'main';
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
async function performCreateShareInfo() {
  if (!createShareInfoForm.value) {
    return;
  }
  try {
    createShareInfoForm.value.saveInProgress = true;
    const obj = await noteShareInfoStore.createShareInfo(shareInfoContext.value, createShareInfoForm.value.data);
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

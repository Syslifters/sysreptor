<template>
  <div class="toolbar-sticky">
    <v-toolbar density="compact" flat color="inherit">
      <v-toolbar-title><slot name="title"></slot></v-toolbar-title>

      <slot></slot>

      <s-btn-icon
        v-if="showSave"
        :loading="savingInProgress"
        :disabled="!canSave"
        @click="performSave"
      >
        <v-badge v-if="props.data !== undefined" dot :color="hasChanges? 'error' : 'success'">
          <v-icon icon="mdi-content-save" />
        </v-badge>
        <v-icon v-else icon="mdi-content-save" />
        <template #loader>
          <v-badge>
            <v-icon icon="mdi-content-save" />
            <template #badge>
              <s-saving-loader-spinner />
            </template>
          </v-badge>
        </template>

        <s-tooltip
          activator="parent"
          location="bottom"
          :text="hasChanges ? 'Save with Ctrl+S' : 'Everything saved'"
        />
      </s-btn-icon>

      <s-btn-icon v-if="(showSave && props.canAutoSave) || showDelete || slots['context-menu']">
        <v-icon icon="mdi-dots-vertical" />

        <v-menu activator="parent" :close-on-content-click="false" location="bottom left" class="context-menu">
          <v-list>
            <v-list-item
              v-if="showSave && props.canAutoSave"
              @click="autoSaveEnabled = !autoSaveEnabled"
              :disabled="!canSave"
              link
              title="Auto Save"
            >
              <template #prepend>
                <v-switch
                  v-model="autoSaveEnabled"
                  hide-details
                  color="primary"
                  class="mt-0 mr-2"
                />
              </template>
            </v-list-item>
            <slot name="context-menu" />
            <btn-delete
              v-if="showDelete"
              :delete="performDelete"
              :confirm="true"
              :confirm-input="props.deleteConfirmInput"
              :disabled="!canDelete"
              button-variant="list-item"
              color="error"
            />
          </v-list>
        </v-menu>
      </s-btn-icon>
    </v-toolbar>

    <v-alert v-if="props.errorMessage || lockError" type="warning" density="compact" class="mt-0 mb-0">
      <span v-if="props.errorMessage">
        <pro-info v-if="props.errorMessage.includes('SysReptor Professional')">{{ props.errorMessage }}</pro-info>
        <span v-else>{{ props.errorMessage }}</span>
      </span>
      <span v-else-if="!lockInfo">
        Could not lock resource for editing.
      </span>
      <span v-else-if="lockInfo.user.id !== auth.user.value!.id">
        {{ lockInfo.user.name }} is currently editing this page.
        To prevent overwriting changes, only one user has write access at a time.
        Please wait until they are finished or ask them to leave this page.
      </span>
      <span v-else-if="lockInfo.user.id === auth.user.value!.id">
        It seems like you are editing this page in another tab or browser session.
        To prevent overwriting changes, only one instance has write access at a time.
        <v-btn @click="selfLockedEditAnyway" variant="text" size="small">Edit Anyway</v-btn>
      </span>
    </v-alert>

    <v-divider />
  </div>
</template>

<script setup lang="ts" generic="T extends { id: string, lock_info?: LockInfo|null }">
import debounce from 'lodash/debounce';
import cloneDeep from 'lodash/cloneDeep';
import isEqual from 'lodash/isEqual';
import type { VForm } from "vuetify/lib/components/index.mjs";
import type { NavigationGuardNext, RouteLocationNormalized } from "vue-router";
import type { LockInfo } from '@/utils/types';
import { EditMode } from '@/utils/types';

const props = withDefaults(defineProps<{
  data?: T|null,
  form?: VForm,
  canSave?: boolean,
  canAutoSave?: boolean,
  save?:((data: T) => Promise<void>),
  canDelete?: boolean,
  delete?: ((data: T) => Promise<void>),
  deleteConfirmInput?: string,
  lockUrl?: string,
  unlockUrl?: string,
  editMode?: EditMode,
  errorMessage?: string|null,
}>(), {
  data: undefined,
  form: undefined,
  canSave: true,
  canAutoSave: false,
  save: undefined,
  canDelete: undefined,
  delete: undefined,
  deleteConfirmInput: undefined,
  lockUrl: undefined,
  unlockUrl: undefined,
  editMode: EditMode.EDIT,
  errorMessage: undefined,
});
const emit = defineEmits<{
  (e: 'update:data', value: { newValue: T | null, oldValue: T | null}): void;
  (e: 'update:editMode', value: EditMode): void;
  (e: 'update:lockedData', value: any): void;
}>();
const slots = useSlots();

const auth = useAuth();
const localSettings = useLocalSettings();

const showDelete = computed(() => props.delete !== undefined);
const canDelete = computed(() => props.canDelete || (props.canDelete === undefined && props.delete !== undefined && props.editMode === EditMode.EDIT));
const showSave = computed(() => props.save !== undefined);
const canSave = computed(() => showSave.value && props.canSave && props.editMode === EditMode.EDIT);
const hasChangesValue = ref(false);
const hasChanges = computed(() => hasChangesValue.value || props.data === undefined);
const autoSaveEnabled = computed({
  get: () => localSettings.autoSaveEnabled && props.canAutoSave,
  set: (val) => { localSettings.autoSaveEnabled = val; },
});
const autoSave = debounce(() => {
  if (props.canAutoSave && autoSaveEnabled.value) {
    performSave();
  }
}, 5000);
watch(autoSaveEnabled, (val) => {
  if (val) {
    autoSave();
  } else {
    autoSave.cancel();
  }
});

const savingInProgress = ref(false);
const deletingInProgress = ref(false);
const actionInProgress = computed(() => savingInProgress.value || deletingInProgress.value);

const previousData = ref<T | null>(null);
const isDestroying = ref(false);
const lockingInProgress = ref(false);
const lockInfo = ref<LockInfo | null>(null);
const hasLock = ref(false);
const lockError = ref<boolean>(false);
const refreshLockInterval = ref<number | null>(null);

watch(() => props.editMode, (newValue) => {
  if (newValue === EditMode.EDIT && !hasLock.value) {
    performLock();
  } else if (newValue === EditMode.READONLY) {
    performUnlock(false);
  }
});

watch(() => props.data, async (newValue) => {
  const oldValue = previousData.value as T;
  const valueChanged = !isEqual(newValue, previousData.value);
  if (!oldValue && newValue) {
    // @ts-ignore
    previousData.value = cloneDeep(newValue)
  }
  if (newValue && !hasLock.value && props.editMode === EditMode.EDIT) {
    await performLock();
  }
  if (oldValue && valueChanged) {
    hasChangesValue.value = true;
    // @ts-ignore
    previousData.value = cloneDeep(newValue);
    // @ts-ignore
    emit('update:data', { newValue, oldValue });
    if (autoSaveEnabled.value) {
      autoSave();
    }
  }
}, {
  deep: true,
  immediate: true,
});

onMounted(() => {
  window.addEventListener('beforeunload', beforeLeaveBrowser);
  window.addEventListener('keydown', keyboardShortcutListener);
  window.addEventListener('unload', onUnloadBrowser);
});
onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', beforeLeaveBrowser);
  window.removeEventListener('keydown', keyboardShortcutListener);
  window.removeEventListener('unload', onUnloadBrowser);

  if (refreshLockInterval.value) {
    clearInterval(refreshLockInterval.value);
    refreshLockInterval.value = null;
  }
});

async function performSave() {
  if (!canSave.value || !hasChanges.value || savingInProgress.value) {
    return;
  }
  if (props.form !== undefined) {
    const { valid, errors } = await props.form.validate();
    if (!valid) {
      // eslint-disable-next-line no-console
      console.log('form validation errors', errors);
      return;
    }
  }

  try {
    savingInProgress.value = true;
    await props.save!(props.data!);
    await nextTick();
    // @ts-ignore
    previousData.value = cloneDeep(props.data!);
    hasChangesValue.value = false;
  } catch (error) {
    requestErrorToast({ error });
  } finally {
    savingInProgress.value = false;
  }
}

async function performDelete() {
  if (!canDelete.value || !(hasLock.value || props.lockUrl === undefined)) {
    return;
  }

  const hasLockReset = hasLock.value;
  const hasChangesValueReset = hasChangesValue.value;
  try {
    hasLock.value = false;
    hasChangesValue.value = false;
    await props.delete!(props.data!);
  } catch (error) {
    hasLock.value = hasLockReset;
    hasChangesValue.value = hasChangesValueReset;
    throw error;
  }
}

async function selfLockedEditAnyway() {
  await performLock(true)
  if (hasLock.value) {
    emit('update:editMode', EditMode.EDIT);
  }
}

async function performLockRequest(forceLock: boolean) {
  let status = 0;
  const data = await $fetch<T>(props.lockUrl!, {
    method: 'POST',
    body: {
      refresh_lock: hasLock.value || forceLock,
    },
    onResponse({ response }) {
      status = response.status;
    },
  });
  return { data, status };
}

async function performLock(forceLock = false) {
  if (lockingInProgress.value || !props.lockUrl || (props.editMode === EditMode.READONLY && !forceLock) || isDestroying.value) {
    return;
  }

  lockingInProgress.value = true;
  if (!refreshLockInterval.value) {
    refreshLockInterval.value = window.setInterval(performLock, 30_000);
  }

  try {
    // eslint-disable-next-line no-console
    console.log('EditToolbar.performLock');
    const lockResponse = await performLockRequest(forceLock);

    const lockedData = lockResponse.data as Lockable;
    lockInfo.value = lockedData.lock_info;
    emit('update:lockedData', lockedData);

    if (lockResponse.status !== 201 && !hasLock.value && !forceLock) {
      throw new Error('Lock error: User has lock in another tab or browser session.');
    }

    hasLock.value = true;
    lockError.value = false;
  } catch (error: any) {
    // Do not release lock (in frontend) if the user previously had the lock.
    // Prevent resetting lock on network errors.
    // hasLock is only set to false in situations where the API tells us that we do not have the lock.
    // hasLock.value = false;

    if (error?.status === 403 && error?.data?.lock_info) {
      lockInfo.value = error.data.lock_info;
      lockError.value = true;
      hasLock.value = false;
      emit('update:editMode', EditMode.READONLY);
      emit('update:lockedData', error.data);
    } else if (error?.message?.includes('User has lock in another tab or browser session')) {
      // Open by current user in another tab or browser session
      lockError.value = true;
      hasLock.value = false;
      emit('update:editMode', EditMode.READONLY);
    } else {
      requestErrorToast({ error, message: 'Locking failed' });
    }
  } finally {
    lockingInProgress.value = false;
  }
}

function performUnlockRequest(browserUnload: boolean): Promise<T> | null {
  if (browserUnload) {
    // sendbeacon does not support setting headers (including Authorization header)
    // we might want to replace sendBeacon with fetch.keepalive in the future
    // however, fetch.keepalive is currently not supported by Firefox
    window.navigator.sendBeacon(
      props.unlockUrl!,
      auth.user.value!.id
    );
    return null;
  } else {
    return $fetch(props.unlockUrl!, {
      method: 'POST',
      body: {}
    });
  }
}

function performUnlock(browserUnload = false) {
  if (!props.unlockUrl || !hasLock.value) {
    return Promise.resolve();
  }

  if (refreshLockInterval.value) {
    clearInterval(refreshLockInterval.value);
    refreshLockInterval.value = null;
  }

  hasLock.value = false;
  lockInfo.value = null;
  lockError.value = false;

  try {
    // eslint-disable-next-line no-console
    console.log('EditToolbar.performUnlock', hasLock.value);

    const res = performUnlockRequest(browserUnload);
    if (!browserUnload) {
      return res!.then((unlockedData) => {
        lockInfo.value = unlockedData.lock_info || null;
        emit('update:lockedData', unlockedData);
      })
        .catch((error) => {
          if (error?.data?.lock_info !== undefined) {
            lockInfo.value = error.data.lock_info;
            emit('update:lockedData', error.data);
          }
        });
    }
  } catch (error) {
    // silently ignore error
    // eslint-disable-next-line no-console
    console.error('Unlock error', error);
  }

  return Promise.resolve();
}

function beforeLeaveBrowser(event: BeforeUnloadEvent) {
  if (!canSave.value || !hasChangesValue.value || autoSaveEnabled.value || actionInProgress.value) {
    return;
  }
  // Browser navigation event onbeforeunload: user navigates to a different site or refreshes pages
  // Message is not displayed, but should not be empty
  event.returnValue = 'Leave?';
  return 'Leave?';
}

async function beforeLeave(_to: RouteLocationNormalized, _from: RouteLocationNormalized, next: NavigationGuardNext) {
  if (!canSave.value || !hasChangesValue.value || actionInProgress.value) {
    next();
    await resetComponent()
  } else if (autoSaveEnabled.value) {
    next();
    await performSave();
    await resetComponent();
  } else {
    // vue-router navigation event: user navigates to a different SPA page
    const answer = window.confirm('Do you really want to leave? You have unsaved changes!');
    next(answer);
    if (answer) {
      await resetComponent();
    }
  }
}

function keyboardShortcutListener(event: KeyboardEvent) {
  if ((event.ctrlKey && event.key === 's') || (event.metaKey && event.key === 's')) {
    event.preventDefault();
    performSave();
  }
}

function onUnloadBrowser() {
  // Note: the unload event is not triggered in certain situations
  //       e.g. on mobile devices or on Chrome when a user navigates to a different origin
  //       https://developer.mozilla.org/en-US/docs/Web/API/Window/unload_event#usage_notes
  performUnlock(true);
}

function resetComponent() {
  isDestroying.value = true;
  hasChangesValue.value = false;
  previousData.value = null;

  lockInfo.value = null;
  lockError.value = false;

  return performUnlock(false);
}

defineExpose({
  autoSaveEnabled,
  performSave,
  beforeLeave,
  resetComponent,
})
</script>

<style lang="scss" scoped>
.toolbar-sticky {
  position: sticky;
  top: 0;
  z-index: 1;
  background-color: rgb(var(--v-theme-surface));
}

.btn-autosave :deep() {
  .v-label {
    width: max-content;
  }
}

</style>

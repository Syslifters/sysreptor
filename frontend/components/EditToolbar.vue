<template>
  <div class="toolbar-sticky">
    <v-toolbar flat dense tile>
      <v-toolbar-title><slot name="title" /></v-toolbar-title>
      <v-spacer />

      <slot></slot>

      <v-switch v-if="canSave && canAutoSave" v-model="autoSaveEnabled" label="Auto Save" class="btn-autosave align-self-center ml-2 mr-2" hide-details />

      <s-tooltip v-if="canSave" :disabled="data === null" :open-on-focus="false">
        <template #activator="{on, attrs}">
          <s-btn :loading="savingInProgress" :disabled="savingInProgress" @click="performSave" v-bind="attrs" v-on="on" color="primary" class="ml-1 mr-1">
            <template #default>
              <v-icon>mdi-content-save</v-icon>
              <v-badge v-if="data !== null" dot :color="hasChanges? 'error' : 'success'">
                <slot name="save-button-text">Save</slot>
              </v-badge>
              <slot v-else name="save-button-text">Save</slot>
            </template>

            <template #loader>
              <saving-loader-spinner />
              <slot name="save-button-text">Save</slot>
            </template>
          </s-btn>
        </template>
        <template #default>
          <span v-if="hasChanges">Save with Ctrl+S</span>
          <span v-else>Everything saved</span>
        </template>
      </s-tooltip>
    
      <btn-delete
        v-if="canDelete" 
        :delete="performDelete" 
        :confirm="true"  
        :confirm-input="deleteConfirmInput"
        icon color="error" 
      />
    </v-toolbar>

    <v-alert v-if="errorMessage || lockError" type="warning" dense class="mt-0 mb-0">
      <span v-if="errorMessage">
        {{ errorMessage }}
      </span>
      <span v-else-if="!lockInfo">
        Could not lock resource for editing.
      </span>
      <span v-else-if="lockInfo.user.id !== $auth.user.id">
        {{ lockInfo.user.name }} is currenlty editing this page. 
        To prevent overwriting changes, only one user has write access at a time.
        Please wait until they are finished or ask them to leave this page.
      </span>
      <span v-else-if="lockInfo.user.id === $auth.user.id">
        It seems like you are editing this page in another tab or browser session.
        To prevent overwriting changes, only one instance has write access at a time.
        <v-btn @click="selfLockedEditAnyway" text small>Edit Anyway</v-btn>
      </span>
    </v-alert>

    <v-divider />
  </div>
</template>

<script>
import { debounce, cloneDeep, isEqual } from 'lodash';
import { absoluteApiUrl } from '~/utils/urls';
import { EditMode } from '~/utils/other';

export default {
  props: {
    data: {
      type: Object,
      default: null,
    },
    form: {
      type: Object,
      default: null,
    },
    canAutoSave: {
      type: Boolean,
      default: false,
    },
    save: {
      type: Function,
      default: null,
    },
    delete: {
      type: Function,
      default: null,
    },
    deleteConfirmInput: {
      type: String,
      default: null,
    },
    lockUrl: {
      type: String,
      default: null,
    },
    unlockUrl: {
      type: String,
      default: null,
    },
    editMode: {
      type: String,
      default: EditMode.EDIT,
    },
    errorMessage: {
      type: String,
      default: null,
    }
  },
  events: [
    'update:editMode',
    'update:lockedData',
  ],
  data() {
    return {
      hasChangesValue: false,
      savingInProgress: false,
      deletingInProgress: false,
      lockingInProgress: false,
      previousData: null,
      wasReset: true,
      
      hasLock: false,
      lockInfo: null,
      lockError: false,
      refreshLockInterval: null,
    }
  },
  computed: {
    canDelete() {
      return this.delete !== null && this.editMode === EditMode.EDIT;
    },
    canSave() {
      return this.save !== null && this.editMode === EditMode.EDIT;
    },
    autoSaveEnabled: {
      get() {
        return this.canSave && this.canAutoSave && this.$store.state.settings.autoSaveEnabled;
      },
      set(val) {
        this.$store.commit('settings/updateAutoSaveEnabled', val);
      }
    },
    actionInProgress() {
      return this.savingInProgress || this.deletingInProgress;
    },
    hasChanges() {
      return this.hasChangesValue || this.data === null;
    }
  },
  watch: {
    data: {
      deep: true,
      immediate: true,
      handler(newValue) {
        const oldValue = this.previousData;
        const valueChanged = isEqual(newValue, this.previousData);
        if (!this.wasReset && !valueChanged) {
          this.hasChangesValue = true;
          this.previousData = cloneDeep(newValue);

          this.$emit('update:data', { newValue, oldValue });
          if (this.autoSaveEnabled) {
            this.autoSave();
          }
        } else if (this.wasReset) {
          this.previousData = cloneDeep(newValue);
          this.wasReset = false;
          if (this.editMode === EditMode.EDIT) {
            this.performLock();
          }
        }
      }
    },
    autoSaveEnabled(newValue) {
      if (newValue) {
        this.autoSave();
      } else {
        this.autoSave.cancel();
      }
    },
    editMode(newValue, oldValue) {
      if (newValue === EditMode.EDIT && !this.hasLock) {
        this.performLock();
      } else if (newValue === EditMode.READONLY) {
        this.performUnlock(false);
      }
    }
  },
  created() {
    this.autoSave = debounce(this.performSave, 5000);
  },
  mounted() {
    window.addEventListener('beforeunload', this.beforeLeaveBrowser);
    window.addEventListener('keydown', this.keyboardShortcutListener);
    window.addEventListener('unload', this.onUnloadBrowser);
  },
  beforeDestroy() {
    window.removeEventListener('beforeunload', this.beforeLeaveBrowser);
    window.removeEventListener('keydown', this.keyboardShortcutListener);
    window.removeEventListener('unload', this.onUnloadBrowser);

    if (this.refreshLockInterval) {
      clearInterval(this.refreshLockInterval);
      this.refreshLockInterval = null;
    }
  },
  methods: {
    async performSave() {
      if (!this.canSave || !this.hasChanges || this.savingInProgress) {
        return;
      }
      if (this.form !== null) {
        if (!this.form.validate()) {
          return;
        }
      }
      
      try {
        this.savingInProgress = true;
        await this.save(this.data);

        this.hasChangesValue = false;
        this.previousData = cloneDeep(this.data);
      } catch (error) {
        this.$toast.global.requestError({ error });
      } finally {
        this.savingInProgress = false;
      }
    },
    async performDelete() {
      if (!this.canDelete || !(this.hasLock || this.lockUrl === null)) {
        return;
      }

      const hasLockReset = this.hasLock;
      const hasChangesValueReset = this.hasChangesValue;
      try {
        this.hasLock = false;
        this.hasChangesValue = false;
        await this.delete(this.data);
      } catch (error) {
        this.hasLock = hasLockReset;
        this.hasChangesValue = hasChangesValueReset;
        throw error;
      }
    },
    async selfLockedEditAnyway() {
      await this.performLock(true)
      // eslint-disable-next-line no-console
      console.log('selfLockedEditAnyway', this.hasLock);
      if (this.hasLock) {
        this.$emit('update:editMode', EditMode.EDIT);
      }
    },
    async performLockRequest(forceLock) {
      return await this.$axios.post(this.lockUrl, {
        refresh_lock: this.hasLock || forceLock,
      });
    },
    async performLock(forceLock = false) {
      // eslint-disable-next-line no-console
      console.log('EditToolbar.performLock');
      if (this.lockingInProgress || !this.lockUrl || (this.editMode === EditMode.READONLY && !forceLock) || this.wasReset) {
        return;
      }

      this.lockingInProgress = true;
      if (!this.refreshLockInterval) {
        this.refreshLockInterval = setInterval(this.performLock, 30_000);
      }

      try {
        const lockResponse = await this.performLockRequest(forceLock);
        // eslint-disable-next-line no-console
        console.log('performLock lockResponse', lockResponse);

        const lockedData = lockResponse.data;
        this.lockInfo = lockedData.lock_info;
        this.$emit('update:lockedData', lockedData);

        if (lockResponse.status !== 201 && !this.hasLock && !forceLock) {
          throw new Error('Lock error: User has lock in another tab or browser session.');
        }

        this.hasLock = true;
        this.lockError = false;
      } catch (error) {
        // Do not release lock (in frontend) if the user previously had the lock.
        // Prevent resetting lock on network errors.
        // hasLock is only set to false in situations where the API tells us that we do not have the lock.
        // this.hasLock = false;

        if (error.response?.status === 403 && error.response?.data?.lock_info) {
          // eslint-disable-next-line no-console
          console.log('Lock error: Another user has the lock. Switching to readonly mode.', this.data.id, error, error.response.data);
          this.lockInfo = error.response.data.lock_info;
          this.lockError = true;
          this.hasLock = false;
          this.$emit('update:editMode', EditMode.READONLY);
          this.$emit('update:lockedData', error.response.data);
        } else if (error?.message?.includes('User has lock in another tab or browser session')) {
          // Open by current user in another tab or browser session
          // eslint-disable-next-line no-console
          console.log(error, this.data.id);
          this.lockError = true;
          this.hasLock = false;
          this.$emit('update:editMode', EditMode.READONLY);
        } else {
          this.$toast.global.requestError({ error, message: 'Locking failed' });
        }
      } finally {
        this.lockingInProgress = false;
      }
    },
    performUnlockRequest(browserUnload) {
      if (browserUnload) {
        // sendbeacon does not support setting headers (including Authorization header)
        // we might want to replace sendBeacon with fetch.keepalive in the future
        // however, fetch.keepalive is currently not supported by Firefox
        window.navigator.sendBeacon(
          absoluteApiUrl(this.unlockUrl, this.$axios),
          this.$auth.user.id
        );
      } else {
        return this.$axios.$post(this.unlockUrl, {});
      }
    },
    performUnlock(browserUnload = false) {
      // eslint-disable-next-line no-console
      console.log('EditToolbar.performUnlock', this.hasLock);
      if (!this.unlockUrl || !this.hasLock) {
        return Promise.resolve();
      }
      
      if (this.refreshLockInterval) {
        clearInterval(this.refreshLockInterval);
        this.refreshLockInterval = null;
      }
      
      this.hasLock = false;
      this.lockInfo = null;
      this.lockError = false;

      try {
        const res = this.performUnlockRequest(browserUnload);
        if (!browserUnload) {
          return res.then((unlockedData) => {
            this.lockInfo = unlockedData.lock_info;
            this.$emit('update:lockedData', unlockedData);
          })
            .catch((error) => {
              if (error?.response?.data?.lock_info !== undefined) {
                this.lockInfo = error.response.data.lock_info;
                this.$emit('update:lockedData', error.response.data);
              }
            });
        }
      } catch (error) {
        // silently ignore error
        // eslint-disable-next-line no-console
        console.error('Unlock error', error);
      }

      return Promise.resolve();
    },
    beforeLeaveBrowser(event) {
      if (!this.canSave || !this.hasChangesValue || this.autoSaveEnabled || this.actionInProgress) {
        return;
      }
      // Browser navigation event onbeforeunload: user navigates to a different site or refreshes pages
      // Message is not displayed, but should not be empty
      event.returnValue = 'Leave?';
      return 'Leave?';
    },
    async beforeLeave(to, from, next) {
      if (!this.canSave || !this.hasChangesValue || this.actionInProgress) {
        next();
        await this.resetComponent()
      } else if (this.autoSaveEnabled) {
        next();
        await this.performSave();
        await this.resetComponent();
      } else {
        // vue-router navigation event: user navigates to a different SPA page
        const answer = window.confirm('Do you really want to leave? You have unsaved changes!');
        next(answer);
        if (answer) {
          await this.resetComponent();
        }
      }
    },
    onUnloadBrowser() {
      // Note: the unload event is not triggered in certain situations
      //       e.g. on mobile devices or on Chrome when a user navigates to a different origin
      //       https://developer.mozilla.org/en-US/docs/Web/API/Window/unload_event#usage_notes
      // eslint-disable-next-line no-console
      console.log('EditToolbar.onUnloadBrowser');
      this.performUnlock(true);
    },
    keyboardShortcutListener(event) {
      if ((event.ctrlKey && event.key === 's') || (event.metaKey && event.key === 's')) {
        event.preventDefault();
        this.performSave();
      }
    },
    resetComponent() {
      this.hasChangesValue = false;
      this.previousData = null;
      this.wasReset = true;

      this.lockInfo = null;
      this.lockError = false;

      return this.performUnlock(false);
    }
  }
}
</script>

<style lang="scss" scoped>
.toolbar-sticky {
  position: sticky;
  top: 0;
  z-index: 1;
}

.btn-autosave :deep() {
  .v-label {
    width: max-content;
  }
}
</style>

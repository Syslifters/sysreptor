<template>
  <v-toolbar flat dense tile>
    <v-toolbar-title><slot name="title" /></v-toolbar-title>
    <v-spacer />

    <slot></slot>

    <v-switch v-if="canSave && canAutoSave" v-model="autoSaveEnabled" label="Auto Save" class="align-self-center ml-2 mr-2" hide-details />

    <s-tooltip v-if="canSave" :disabled="savingInProgress">
      <template #activator="{on, attrs}">
        <s-btn :loading="savingInProgress" :disabled="savingInProgress" @click="performSave" v-bind="attrs" v-on="on" color="primary" class="ml-2 mr-2">
          <template #default>
            <v-icon>mdi-content-save</v-icon>
            <v-badge dot :color="hasChanges? 'error' : 'success'">
              Save
            </v-badge>
          </template>

          <template #loader>
            <saving-loader-spinner />
            Save
          </template>
        </s-btn>
      </template>
      <template #default>
        <span v-if="hasChanges">Save with Ctrl+S</span>
        <span v-else>Everything saved</span>
      </template>
    </s-tooltip>
    
    <delete-button v-if="canDelete" @delete="performDelete" icon color="error" />
  </v-toolbar>
</template>

<script>
import { debounce, cloneDeep, isEqual } from 'lodash';

export const EditMode = Object.freeze({
  READONLY: 'READONLY',
  EDIT: 'EDIT',
})

export default {
  props: {
    data: {
      type: Object,
      required: true,
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
    lock: {
      type: Function,
      default: null,
    },
    unlock: {
      type: Function,
      default: null,
    },
    editMode: {
      type: String,
      default: EditMode.EDIT,
    },
  },
  events: ['updateEditMode'],
  data() {
    return {
      hasChanges: false,
      savingInProgress: false,
      deletingInProgress: false,
      lockingInProgress: false,
      previousData: null,
      wasReset: true,
      
      hasLock: false,
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
    }
  },
  watch: {
    data: {
      deep: true,
      immediate: true,
      handler(newValue, oldValue) {
        const valueChanged = isEqual(newValue, this.previousData);
        if (!this.wasReset && !valueChanged) {
          this.hasChanges = true;
          this.previousData = cloneDeep(newValue);

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
      if (newValue === false) {
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
  destroyed() {
    window.removeEventListener('beforeunload', this.beforeLeaveBrowser);
    window.removeEventListener('keydown', this.keyboardShortcutListener);
    window.removeEventListener('unload', this.onUnloadBrowser);

    if (this.refreshLockInterval !== null) {
      clearInterval(this.refreshLockInterval);
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

      this.savingInProgress = true;
      try {
        await this.save(this.data);

        this.hasChanges = false;
        this.previousData = cloneDeep(this.data);
      } catch (error) {
        this.$toast.global.requestError({ error });
      }
      this.savingInProgress = false;
    },
    async performDelete() {
      try {
        await this.delete(this.data);  
      } catch (error) {
        this.$toast.global.requestError({ error });
      }
    },
    async performLock() {
      console.log('EditToolbar.performLock', this);
      if (this.lockingInProgress || !this.lock || this.editMode === EditMode.READONLY || this.wasReset) {
        return;
      }

      this.lockingInProgress = true;
      if (!this.refreshLockInterval) {
        this.refreshLockInterval = setInterval(this.performLock, 30_000);
      }

      try {
        await this.lock(this.data);
        this.hasLock = true;
      } catch (error) {
        this.hasLock = false;
        this.$toast.global.requestError({ error, message: 'Locking failed' });
      }
      this.lockingInProgress = false;
    },
    performUnlock(browserUnload = false) {
      console.log('EditToolbar.performUnlock', this.hasLock, this);
      if (!this.unlock || !this.hasLock) {
        return;
      }
      
      if (this.refreshLockInterval) {
        clearInterval(this.refreshLockInterval);
      }
      
      try {
        this.hasLock = false;
        this.unlock(this.data, browserUnload);
      } catch (error) {
        // silently ignore error
        console.log('Unlock error', error);
        // this.$toast.global.requestError({ error, message: 'Unlocking failed' });
      }
    },
    beforeLeaveBrowser(event) {
      if (!this.canSave || !this.hasChanges || this.autoSaveEnabled || this.actionInProgress) {
        return;
      }
      // Browser navigation event onbeforeunload: user navigates to a different site or refreshes pages
      // Message is not displayed, but should not be empty
      event.returnValue = 'Leave?';
      return 'Leave?';
    },
    async beforeLeave(to, from, next) {
      if (!this.canSave || !this.hasChanges || this.actionInProgress) {
        this.resetComponent();
        next();
      } else if (this.autoSaveEnabled) {
        await this.performSave();
        this.resetComponent();
        next();
      } else {
        // vue-router navigation event: user navigates to a different SPA page
        const answer = window.confirm('Do you really want to leave? You have unsaved changes!');
        if (answer) {
          this.resetComponent();
        }
        next(answer);
      }
    },
    onUnloadBrowser() {
      // Note: the unload event is not triggered in certain situations
      //       e.g. on mobile devices or on Chrome when a user navigates to a different origin
      //       https://developer.mozilla.org/en-US/docs/Web/API/Window/unload_event#usage_notes
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
      this.hasChanges = false;
      this.previousData = null;
      this.wasReset = true;

      this.performUnlock(false);
    }
  }
}
</script>

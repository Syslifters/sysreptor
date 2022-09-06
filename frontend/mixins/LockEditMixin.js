import { cloneDeep } from "lodash";
import urlJoin from "url-join"
import { absoluteApiUrl } from "~/utils/urls";
import { EditMode } from '~/components/EditToolbar.vue';

export default {
  beforeRouteLeave(to, from, next) {
    this.$refs.toolbar.beforeLeave(to, from, next);
  },
  beforeRouteUpdate(to, from, next) {
    this.$refs.toolbar.beforeLeave(to, from, next);
  },
  data() {
    const hasEditPermissions = this.getHasEditPermissions();
    return {
      editMode: hasEditPermissions ? EditMode.EDIT : EditMode.READONLY,
      lockError: !hasEditPermissions,
      lockInfo: null,
    };
  },
  computed: {
    data() {
      throw new Error('Not implemented');
    },
    baseUrl() {
      return this.getBaseUrl(this.data);
    },
    toolbarAttrs() {
      return {
        ref: 'toolbar',
        data: this.data,
        editMode: this.editMode,
        ...(this.performSave ? {
          save: this.performSave,
          lock: this.performLock,
          unlock: this.performUnlock,
        } : {}),
        ...(this.performDelete ? {
          delete: this.performDelete,
        } : {}),
      }
    },
    errorMessageLocked() {
      if (!this.getHasEditPermissions()) {
        return 'You do not have permissions to edit this resource.';
      }
      if (!this.lockError) {
        return null;
      } else if (!this.lockInfo) {
        return 'Could not lock resource for editing.';
      } else if (this.lockInfo.user.id !== this.$auth.user.id) {
        return `${this.lockInfo.user.name} is currenlty editing this page. 
                To prevent overwriting changes, only one user has write access at a time.
                Please wait until he is finished or ask him to leave this page.`;
      } else if (this.lockInfo.user.id === this.$auth.user.id) {
        return `It seems you like are editing this page in another tab or browser session. 
                To prevent overwriting changes, only one instance has write access at a time.`;
      }
      return null;
    },
    readonly() {
      return this.editMode === EditMode.READONLY;
    },
  },
  mounted() {
    // Set initial value in store to update lock info
    this.updateInStore(cloneDeep(this.data));
  },
  methods: {
    getBaseUrl(data) {
      throw new Error('Not implemented');
    },
    getHasEditPermissions() {
      return true;
    },
    updateInStore(data) {
      
    },
    async performLock(data) {
      console.log('LockEditMixin.performLock', data.id);
      this.lockError = false;
      try {
        const response = await this.$axios.post(urlJoin(this.getBaseUrl(data), '/lock/'));
        const lockedData = response.data;
        this.lockInfo = lockedData.lock_info;

        if (response.status !== 201 && !this.$refs.toolbar.hasLock) {
          // Open by current user in another tab or browser session
          this.lockError = true;
          this.editMode = EditMode.READONLY;
          throw new Error('User did not create a new lock: User has lock in another tab or browser session.');
        }

        this.updateInStore(lockedData);
        return lockedData;
      } catch (error) {
        console.log('Lock error', error);
        if (error.response && error.response.status === 403) {
          console.log('Lock error: Another user has the lock. Switching to readonly mode.', data.id, this, error);
          this.editMode = EditMode.READONLY;
          this.lockError = true;
        }
        if (error?.response?.data?.lock_info !== undefined) {
          this.lockInfo = error.response.data.lock_info;
        }
        throw error;
      }
    },
    async performUnlock(data, browserUnload) {
      console.log('LockEditMixin.performUnlock', data.id, browserUnload);
      const unlockUrl = urlJoin(this.getBaseUrl(data), '/unlock/');

      if (browserUnload) {
        // sendbeacon does not support setting headers (including Authorization header)
        // we might want to replace sendBeacon with fetch.keepalive in the future
        // however, fetch.keepalive is currently not supported by Firefox
        window.navigator.sendBeacon(
          absoluteApiUrl(unlockUrl, this.$axios),
          this.$auth.user.id
        );
      } else {
        try {
          const unlockedData = await this.$axios.$post(unlockUrl);
          this.lockInfo = unlockedData.lock_info;
          this.updateInStore(unlockedData);
        } catch (error) {
          if (error?.response?.data?.lock_info !== undefined) {
            this.lockInfo = error.response.data.lock_info;
          }
          throw error;
        }
      }
    }
  },
}

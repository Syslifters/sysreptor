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
    return {
      editMode: EditMode.EDIT,
      lockError: false,
    };
  },
  computed: {
    data() {
      throw new Error('Not implemented');
    },
    baseUrl() {
      return this.getBaseUrl(this.data);
    },
    lockInfo() {
      return this.data.lock_info || null;
    },
    toolbarAttrs() {
      return {
        ref: 'toolbar',
        data: this.data,
        editMode: this.editMode,
        ...(this.performSave ? {
          save: this.performSave,
          canAutoSave: true,
          lock: this.performLock,
          unlock: this.performUnlock,
        } : {}),
        ...(this.performDelete ? {
          delete: this.performDelete,
        } : {}),
      }
    },
    errorMessageLocked() {
      if (!this.lockError || !this.lockInfo) {
        return null;
      } else if (this.lockInfo.user.id !== this.$auth.user.id) {
        return `${this.lockInfo.user.name} is currenlty editing this page. 
                To prevent overwriting changes, only one user has write access at a time.
                Please wait until he is finished or ask him to leave this page.`;
      } else if (this.lockInfo.user.id === this.$auth.user.id) {
        return `It seems you have are editing this page in another tab or browser session. 
                To prevent overwriting changes, only one instance has write access at a time.`;
      }
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
    updateInStore(data) {
      throw new Error('Not implemented');
    },
    async performLock(data) {
      console.log('LockEditMixin.performLock', data.id);
      this.lockError = false;
      try {
        const response = await this.$axios.post(urlJoin(this.getBaseUrl(data), '/lock/'));
        if ((response.status !== 201 && !this.$refs.toolbar.hasLock)) {
          // Open by current user in another tab or browser session
          this.lockError = true;
          this.editMode = EditMode.READONLY;
          throw new Error('Locking failed');
        }

        const lockedData = response.data;
        this.updateInStore(lockedData);
        return lockedData;
      } catch (error) {
        if (error.response && error.response.status === 403) {
          this.lockError = true;
          this.editMode = EditMode.READONLY;
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
        const unlockedData = await this.$axios.$post(unlockUrl);
        this.updateInStore(unlockedData);
      }
    }
  },
}

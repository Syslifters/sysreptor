import { cloneDeep } from "lodash";
import urlJoin from "url-join"
import { EditMode } from '~/utils/other';

export default {
  async beforeRouteLeave(to, from, next) {
    if (this.$refs.toolbar) {
      await this.$refs.toolbar.beforeLeave(to, from, (res = true) => {
        this.navigationInProgress = res;
      });
      await this.$nextTick();
      next(this.navigationInProgress);
    } else {
      next();
    }
  },
  async beforeRouteUpdate(to, from, next) {
    if (this.$refs.toolbar) {
      await this.$refs.toolbar.beforeLeave(to, from, (res = true) => {
        this.navigationInProgress = res;
      });
      await this.$nextTick();
      next(this.navigationInProgress);
      if (this.navigationInProgress) {
        // Synchronize beforeRouteUpdate and $fetch such that no race conditions occur (and toolbar events for unlocking are not handled)
        if (this.$fetch) {
          await this.$fetch();
        }
        this.navigationInProgress = false;
      }
    } else {
      next();
    }
  },
  data() {
    const hasEditPermissions = this.getHasEditPermissions();
    return {
      editMode: hasEditPermissions ? EditMode.EDIT : EditMode.READONLY,
      navigationInProgress: false,
    };
  },
  computed: {
    data() {
      throw new Error('Not implemented');
    },
    baseUrl() {
      return this.data ? this.getBaseUrl(this.data) : null;
    },
    lockUrl() {
      return urlJoin(this.baseUrl, '/lock/');
    },
    unlockUrl() {
      return urlJoin(this.baseUrl, '/unlock/');
    },
    deleteConfirmInput() {
      return null;
    },
    fetchLoaderAttrs() {
      return {
        fetchState: {
          ...this.$fetchState,
          pending: this.$fetchState?.pending || this.navigationInProgress,
        }
      };
    },
    toolbarAttrs() {
      return {
        ref: 'toolbar',
        data: this.data,
        editMode: this.editMode,
        ...(this.performSave && this.getHasEditPermissions() ? {
          save: this.performSave,
          lockUrl: this.lockUrl,
          unlockUrl: this.unlockUrl,
        } : {}),
        ...(!this.getHasEditPermissions() ? {
          errorMessage: this.getErrorMessage(),
        } : {}),
        ...(this.performDelete && this.getHasEditPermissions() ? {
          delete: this.performDelete,
          deleteConfirmInput: this.deleteConfirmInput,
        } : {}),
      }
    },
    toolbarEvents() {
      return {
        'update:data': this.onUpdateData,
        'update:editMode': (v) => { this.editMode = v; },
        'update:lockedData': this.updateInStore,
      }
    },
    readonly() {
      return this.editMode === EditMode.READONLY;
    },
  },
  watch: {
    data: {
      handler() {
        // Update permissions after the data object changed
        // Called after routeUpdate, but not when entering data into the form
        this.editMode = this.getHasEditPermissions() ? EditMode.EDIT : EditMode.READONLY;
      },
      immediate: true,
    },
    '$fetchState.pending'(val) {
      if (!val && this.data) {
        this.updateInStore(cloneDeep(this.data));
      }
    }
  },
  mounted() {
    if (!this.$fetchState || (!this.$fetchState.pending && this.data)) {
      // Set initial value in store to update lock info
      this.updateInStore(cloneDeep(this.data));
    }
  },
  methods: {
    getBaseUrl(data) {
      throw new Error('Not implemented');
    },
    getHasEditPermissions() {
      return true;
    },
    getErrorMessage() {
      return 'You do not have permissions to edit this resource.';
    },
    onUpdateData(event) {},
    updateInStore(data) {},
  },
}

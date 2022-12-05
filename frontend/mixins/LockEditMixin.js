import { cloneDeep } from "lodash";
import urlJoin from "url-join"
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
    };
  },
  computed: {
    data() {
      throw new Error('Not implemented');
    },
    baseUrl() {
      return this.getBaseUrl(this.data);
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
    getErrorMessage() {
      return 'You do not have permissions to edit this resource.';
    },
    onUpdateData(event) {},
    updateInStore(data) {},
  },
}

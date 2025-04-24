import { cloneDeep } from "lodash-es";
import { onBeforeRouteLeave, onBeforeRouteUpdate } from "#vue-router";
import type { VForm } from "vuetify/lib/components/index.mjs";
import { EditMode } from "#imports";
import type { EditToolbar } from "#components";
import { urlJoin } from "@base/utils/helpers";

// @ts-expect-error typeof generic component 
export type ToolbarRef = Ref<InstanceType<typeof EditToolbar>|ComputedRef<InstanceType<typeof EditToolbar>>>;
export type LockEditOptions<T> = {
  toolbarRef?: ToolbarRef;
  data: Ref<T>;
  baseUrl?: ComputedRef<string|null>;
  form?: Ref<VForm|null|undefined>;
  fetchState?: ReturnType<typeof useLazyFetch>;
  hasEditPermissions?: ComputedRef<boolean>;
  canDelete?: ComputedRef<boolean>;
  errorMessage?: ComputedRef<string|null>;
  deleteConfirmInput?: ComputedRef<string|null>;
  performSave?: (data: T) => Promise<any>;
  performDelete?: (data: T) => Promise<any>;
  updateInStore?: (data: T) => void;
  autoSaveOnUpdateData?: (event: { oldValue: T; newValue: T }) => boolean;
}

export function useLockEdit<T>(options: LockEditOptions<T>) {
  const route = useRoute();
  const toolbarRef = options.toolbarRef || useTemplateRef<ToolbarRef['value']>('toolbarRef');
  const lockUrl = computed(() => options.baseUrl?.value ? urlJoin(options.baseUrl.value, '/lock/') : undefined);
  const unlockUrl = computed(() => options.baseUrl?.value ? urlJoin(options.baseUrl.value, '/unlock/') : undefined);
  const hasEditPermissions = computed(() => {
    if (options.hasEditPermissions) {
      return options.hasEditPermissions.value;
    }
    return true;
  });
  const editMode = ref<EditMode>(hasEditPermissions?.value ? EditMode.EDIT : EditMode.READONLY);
  const readonly = computed(() => editMode.value === EditMode.READONLY);
  watch(hasEditPermissions, (val) => {
    if (!val) {
      editMode.value = EditMode.READONLY;
    }
  });
  const data = computed(() => {
    if (options.fetchState && options.fetchState.status.value !== 'success') {
      return null;
    }
    return options.data.value;
  });

  const navigationInProgress = ref(false);
  onBeforeRouteLeave(async (to, from, next) => {
    if (toolbarRef.value) {
      await toolbarRef.value.beforeLeave(to, from, (res = true) => {
        navigationInProgress.value = res;
      });
      await nextTick();
      next(navigationInProgress.value);
    } else {
      next();
    }
  });
  onBeforeRouteUpdate(async (to, from, next) => {
    if (toolbarRef.value && to.path !== from.path) {
      await toolbarRef.value.beforeLeave(to, from, (res = true) => {
        navigationInProgress.value = res;
      });
      await nextTick();
      next(navigationInProgress.value);
    } else {
      next();
    }
  });

  const fetchLoaderAttrs = computed(() => {
    return {
      fetchState: {
        data: options.fetchState?.data.value,
        error: options.fetchState?.error.value,
        status: navigationInProgress.value ? 'pending' : options.fetchState ? options.fetchState.status.value : 'success',
      }
    };
  });
  onMounted(() => {
    if (options.updateInStore && data.value) {
      // Set initial value in store to update lock info
      options.updateInStore(cloneDeep(data.value));
    }
  })
  watch(() => options.fetchState?.status.value, async (val) => {
    if (val === 'success' && data.value) {
      if (options.updateInStore) {
        options.updateInStore(cloneDeep(data.value));
      }

      // Scroll to element
      if (route.hash) {
        await nextTick();
        focusElement(route.hash);
      }
    }
  });
  async function onUpdateData(event: { oldValue: T|null, newValue: T|null }) {
    if (options.autoSaveOnUpdateData &&
      event.oldValue && event.newValue &&
      toolbarRef.value?.autoSaveEnabled &&
      options.autoSaveOnUpdateData({ oldValue: event.oldValue!, newValue: event.newValue! })
    ) {
      await toolbarRef.value.performSave();
    }
  }

  const errorMessage = computed(() => {
    if (hasEditPermissions.value) {
      return null;
    }
    if (options.errorMessage?.value) {
      return options.errorMessage.value
    }
    return 'You do not have permissions to edit this resource.';
  })
  const toolbarAttrs = computed(() => {
    return ({
      ref: 'toolbarRef',
      data: data.value,
      'onUpdate:data': onUpdateData,
      'onUpdate:lockedData': options.updateInStore,
      editMode: editMode.value,
      'onUpdate:editMode': (val: EditMode) => { editMode.value = val; },
      errorMessage: errorMessage.value,
      ...((options.performSave) ? {
        save: options.performSave,
        lockUrl: lockUrl.value,
        unlockUrl: unlockUrl.value,
        form: options.form?.value,
        ...(hasEditPermissions.value ? {
          canSave: hasEditPermissions.value,
        } : {}),
      } : {}),
      ...((options.performDelete) ? {
        delete: options.performDelete,
        deleteConfirmInput: options.deleteConfirmInput?.value || undefined,
        ...(options.canDelete ? {
          canDelete: options.canDelete.value,
        } : {}),
      } : {}),
    });
  });

  return {
    toolbarAttrs,
    readonly,
    fetchLoaderAttrs,
    editMode,
  };
}

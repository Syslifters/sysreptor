import urlJoin from "url-join";
import { formatISO9075 } from "date-fns";
import { levelNameFromLevelNumber } from '@base/utils/cvss';
import {
  ProjectTypeScope,
  UploadedFileType,
  type MarkdownEditorMode,
  type PentestProject,
  type ProjectType,
  type UploadedFileInfo,
} from "#imports";


export function useProjectTypeLockEdit(options: {
  projectType: Ref<ProjectType>,
  performSave?: (data: ProjectType) => Promise<void>;
  performDelete?: (data: ProjectType) => Promise<void>;
  hasEditPermissions?: ComputedRef<boolean>;
  errorMessage?: ComputedRef<string|null>;
}) {
  const auth = useAuth();
  const projectType = computed(() => options.projectType.value);

  const baseUrl = computed(() => `/api/v1/projecttypes/${projectType.value.id}/`);
  useHeadExtended({
    title: projectType.value.name
  });

  const hasEditPermissions = computed(() => {
    if (options.hasEditPermissions && !options.hasEditPermissions.value) {
      return false;
    }
    return (projectType.value.scope === ProjectTypeScope.GLOBAL && auth.permissions.value.designer) ||
            (projectType.value.scope === ProjectTypeScope.PRIVATE && auth.permissions.value.private_designs) ||
            (projectType.value.scope === ProjectTypeScope.PROJECT && projectType.value.source === SourceEnum.CUSTOMIZED);
  });
  const errorMessage = computed(() => {
    if (options.errorMessage?.value) {
      return options.errorMessage.value;
    }
    if (projectType.value.scope === ProjectTypeScope.PROJECT) {
      if (projectType.value.source === SourceEnum.SNAPSHOT) {
        return `This design cannot be edited because it is a snapshot from ${projectType.value.created.split('T')[0]}.`
      } else if (projectType.value.source === SourceEnum.IMPORTED_DEPENDENCY) {
        return 'This design cannot be edited because it is an imported snapshot.';
      } else if (projectType.value.source !== SourceEnum.CUSTOMIZED) {
        return 'This design is readonly and cannot be edited.';
      }
    }
    return null;
  })

  const deleteConfirmInput = computed(() => projectType.value.name);
  return {
    ...useLockEdit<ProjectType>({
      performSave: options.performSave,
      performDelete: options.performDelete,
      deleteConfirmInput,
      data: projectType,
      baseUrl,
      hasEditPermissions,
      errorMessage,
    }),
    projectType,
  }
}

export async function useProjectTypeLockEditOptions(options: {save?: boolean, delete?: boolean, saveFields?: string[], id?: string}) {
  const route = useRoute();
  const projectTypeId = options.id || route.params.projectTypeId;
  const projectType = await useFetchE<ProjectType>(`/api/v1/projecttypes/${projectTypeId}/`, { method: 'GET', deep: true });
  const projectTypeStore = useProjectTypeStore();

  async function performSave(data: ProjectType) {
    await projectTypeStore.partialUpdate(data, options.saveFields);
  }
  async function performDelete(data: ProjectType) {
    await projectTypeStore.delete(data);
    await navigateTo('/designs/');
  }

  return {
    projectType,
    ...(options.save ? { performSave } : {}),
    ...(options.delete ? { performDelete } : {})
  };
}

export function useProjectEditBase(options: {
  project: ComputedRef<PentestProject|undefined|null>|Ref<PentestProject|undefined|null>,
  projectType?: ComputedRef<ProjectType|undefined|null>|Ref<ProjectType|undefined|null>,
  historyDate?: string,
  canUploadFiles?: boolean,
  spellcheckEnabled?: Ref<boolean>;
  markdownEditorMode?: Ref<MarkdownEditorMode>;
}) {
  const route = useRoute();
  const auth = useAuth();
  const localSettings = useLocalSettings();
  const projectStore = useProjectStore();

  const projectId = computed(() => options.project.value?.id || route.params.projectId);

  const hasEditPermissions = computed(() => {
    if (options.historyDate) {
      return false;
    } else if (options.project.value && !options.project.value.readonly) {
      return false;
    } else if (!auth.permissions.value.edit_projects) {
      return false;
    }
    return true;
  });
  const errorMessage = computed(() => {
    if (options.historyDate) {
      return `You are comparing a historic version from ${formatISO9075(new Date(options.historyDate))} to the current version.`;
    } else if (options.project.value?.readonly) {
      return 'This project is finished and cannot be changed anymore. In order to edit this project, re-activate it in the project settings.'
    } else if (!auth.permissions.value.edit_projects) {
      return 'You do not have permissions to edit this resource.';
    }
    return null;
  });

  const projectUrl = computed(() => `/api/v1/pentestprojects/${projectId.value}/`);
  const projectTypeUrl = computed(() => options.project.value ? `/api/v1/projecttypes/${options.project.value.project_type}/` : null);

  async function uploadFile(file: File) {
    const uploadUrl = urlJoin(projectUrl.value, options.canUploadFiles ? '/upload/' : '/images/');
    const res = await uploadFileHelper<UploadedFileInfo>(uploadUrl, file);
    if (res.resource_type === UploadedFileType.IMAGE) {
      return `![](/images/name/${res.name}){width="auto"}`;
    } else {
      return `[${res.name}](/files/name/${res.name})`;
    }
  }
  function rewriteFileUrl(fileSrc: string) {
    if (fileSrc.startsWith('/assets/')) {
      return urlJoin(projectTypeUrl.value || '', fileSrc)
    } else {
      return urlJoin(projectUrl.value, fileSrc);
    }
  }

  const referenceItems = computed(() => {
    return projectStore.findings(options.project.value?.id || '', { projectType: options.projectType?.value })
      .map(f => ({
        id: f.id, 
        title: f.data.title,
        severity: options.projectType?.value ? 
        levelNameFromLevelNumber(getFindingRiskLevel({ finding: f, projectType: options.projectType?.value }) as any)?.toLowerCase() : 
          undefined,
      }))
  });
  function rewriteReferenceLink(refId: string) {
    const findingRef = referenceItems.value.find(f => f.id === refId);
    if (findingRef) {
      return {
        href: `/projects/${options.project.value!.id}/reporting/findings/${findingRef.id}/`,
        title: `[Finding ${findingRef.title}]`,
      };
    }
    return null;
  }

  const spellcheckEnabled = options.spellcheckEnabled || computed({ 
    get: () => localSettings.reportingSpellcheckEnabled && !options.historyDate,
    set: (val: boolean) => { localSettings.reportingSpellcheckEnabled = val; }, 
  });
  const markdownEditorMode = options.markdownEditorMode || computed({
    get: () => localSettings.reportingMarkdownEditorMode,
    set: (val: MarkdownEditorMode) => { localSettings.reportingMarkdownEditorMode = val; },
  })
  const inputFieldAttrs = computed(() => ({
    lang: options.project.value?.language || 'en-US',
    selectableUsers: [...(options.project.value?.members || []), ...(options.project.value?.imported_members || [])],
    referenceItems: referenceItems.value,
    spellcheckEnabled: spellcheckEnabled.value,
    'onUpdate:spellcheckEnabled': (val: boolean) => { spellcheckEnabled.value = val; },
    markdownEditorMode: markdownEditorMode.value,
    'onUpdate:markdownEditorMode': (val: MarkdownEditorMode) => { markdownEditorMode.value = val; },
    uploadFile,
    rewriteFileUrl,
    rewriteReferenceLink,
  }));

  return {
    hasEditPermissions,
    errorMessage,
    inputFieldAttrs,
  }
}

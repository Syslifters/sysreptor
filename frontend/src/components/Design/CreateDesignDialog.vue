<template>
  <s-dialog v-model="dialogVisible">
    <template #activator="{ props: dialogProps }">
      <btn-create 
        :loading="actionInProgress"
        :disabled="!canCreate"
        v-bind="dialogProps"
      />
    </template>
    <template #title>New Design</template>

    <template #default>
      <v-card-text>
        <s-project-type-selection
          v-model="currentDesign"
          label="Copy Existing Design (optional)"
          return-object
          :required="false"
          autofocus
        />
        <s-select 
          v-model="currentScope"
          :items="scopeItems"
          label="Scope"
          class="mt-4"
        />
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <s-btn-other
          @click="dialogVisible = false"
          text="Cancel"
        />
        <s-btn-primary
          v-if="currentDesign"
          @click="copyDesign"
          :loading="actionInProgress"
          text="Copy Existing Design"
        />
        <s-btn-primary
          v-else
          @click="createEmptyDesign"
          :loading="actionInProgress"
          text="Create Empty Design"
        />
      </v-card-actions>
    </template>
  </s-dialog>
</template>

<script setup lang="ts">
import { ProjectTypeScope } from "~/utils/types";

const auth = useAuth();
const apiSettings = useApiSettings();
const projectTypeStore = useProjectTypeStore();

const dialogVisible = ref(false);
const currentDesign = ref<ProjectType|null>(null);
const actionInProgress = ref(false);
watch(actionInProgress, () => { currentDesign.value = null });

const scopeItems = computed(() => {
  return [
    { value: ProjectTypeScope.GLOBAL, title: 'Global Design', props: { subtitle: 'Available for all users', disabled: !auth.hasScope('designer') } },
    { value: ProjectTypeScope.PRIVATE, title: 'Private Design', props: { subtitle: 'Available only for you', disabled: !apiSettings.settings?.features.private_designs } },
  ];
});
const currentScope = ref<ProjectTypeScope>(scopeItems.value.find(item => !item.props.disabled)?.value || ProjectTypeScope.GLOBAL);
const canCreate = computed(() => scopeItems.value.some(item => !item.props.disabled));

async function actionWrapper(action: () => Promise<ProjectType>) {
  if (actionInProgress.value) {
    return;
  }

  actionInProgress.value = true;
  try {
    const obj = await action();
    successToast('Created new design');
    await navigateTo(`/designs/${obj.id}`)
  } catch (error) {
    requestErrorToast({ error });
  } finally {
    actionInProgress.value = false;
  }
}

async function createEmptyDesign() {
  return await actionWrapper(async () => {
    return await projectTypeStore.create({
      scope: currentScope.value,
      name: 'New Design',
    } as ProjectType);
  })
}

async function copyDesign() {
  return await actionWrapper(async () => {
    return await projectTypeStore.copy({
      id: currentDesign.value!.id,
      scope: currentScope.value,
    });
  })
}
</script>

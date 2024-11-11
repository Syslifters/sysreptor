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
import { ProjectTypeScope } from "#imports";

const props = withDefaults(defineProps<{
  projectTypeScope: ProjectTypeScope
}>(), {
  projectTypeScope: ProjectTypeScope.GLOBAL
});

const auth = useAuth();
const projectTypeStore = useProjectTypeStore();

const canCreate = computed(() => {
  if (props.projectTypeScope === ProjectTypeScope.GLOBAL) {
    return auth.permissions.value.designer;
  } else {
    return auth.permissions.value.private_designs;
  }
});

const dialogVisible = ref(false);
const currentDesign = ref<ProjectType|null>(null);
const actionInProgress = ref(false);
watch(actionInProgress, () => { currentDesign.value = null });

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
      scope: props.projectTypeScope,
      name: 'New Design',
    } as ProjectType);
  })
}

async function copyDesign() {
  return await actionWrapper(async () => {
    return await projectTypeStore.copy({
      id: currentDesign.value!.id,
      scope: props.projectTypeScope,
    });
  })
}
</script>

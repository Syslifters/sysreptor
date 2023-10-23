<template>
  <s-dialog v-model="dialogVisible">
    <template #activator="{ props: dialogProps }">
      <s-btn
        color="primary"
        :loading="actionInProgress"
        class="ml-1 mr-1" v-bind="dialogProps"
        prepend-icon="mdi-plus"
        text="Create"
      />
    </template>
    <template #title>New Design</template>

    <template #default>
      <v-card-text>
        <s-project-type-selection
          v-model="currentDesign"
          return-object
          :required="false"
          autofocus
        />
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <s-btn
          @click="dialogVisible = false"
          variant="text"
          text="Cancel"
        />
        <s-btn
          v-if="currentDesign"
          @click="copyDesign"
          :loading="actionInProgress"
          color="primary"
          text="Copy Existing Design"
        />
        <s-btn
          v-else
          @click="createEmptyDesign"
          :loading="actionInProgress"
          color="primary"
          text="Create Empty Design"
        />
      </v-card-actions>
    </template>
  </s-dialog>
</template>

<script setup lang="ts">
import { ProjectType, ProjectTypeScope } from "~/utils/types";

const props = withDefaults(defineProps<{
  projectTypeScope: ProjectTypeScope
}>(), {
  projectTypeScope: ProjectTypeScope.GLOBAL
});

const projectTypeStore = useProjectTypeStore();

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

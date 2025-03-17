<template>
  <btn-confirm
    :action="customizeDesign"
    :confirm="!isAlreadyCustomized"
    button-text="Customize Design"
    button-icon="mdi-pencil-ruler"
    tooltip-text="Customize Design for this project"
    dialog-text="Customize the current Design for this project. This allows you to adapt the appearence (HTML, CSS) of the design for this project only. The original design is not affected. Any changes made to the original design will not be automatically applied to the adapted design."
    :disabled="project.readonly || !auth.permissions.value.update_project_settings"
    :button-variant="props.buttonVariant"
    class="mr-1 mb-1"
  />
</template>

<script setup lang="ts">
const props = defineProps<{
  project: PentestProject;
  projectType: ProjectType|null;
  action: () => Promise<void>;
  buttonVariant?: 'default' | 'list-item';
}>();

const auth = useAuth();

const isAlreadyCustomized = computed(() => props.projectType?.source === SourceEnum.CUSTOMIZED);

async function customizeDesign() {
  // Directly navigate designer, if the design is already customized
  if (!isAlreadyCustomized.value) {
    await props.action();
  }
  await navigateTo(`/projects/${props.project.id}/designer/`);
}

</script>

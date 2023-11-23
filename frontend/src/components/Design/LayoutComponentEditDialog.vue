<template>
  <s-dialog v-model="dialogVisible" :disabled="props.disabled">
    <template #activator="{ props: dialogProps }">
      <s-btn
        @click="showDialog"
        v-bind="dialogProps"
        icon
        variant="text"
        size="small"
        density="comfortable"
        class="ml-1 mr-1"
      >
        <v-icon>mdi-pencil</v-icon>
        <s-tooltip activator="parent" text="Edit" />
      </s-btn>
    </template>
    <template #title>Edit</template>
    <template #default>
      <v-card-text>
        <design-layout-component-form
          v-model="form"
          :lang="item.context.projectType.language"
          :upload-file="uploadFile"
          :rewrite-file-url="rewriteFileUrl"
          :disabled="disabled"
        />
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <s-btn @click="dialogVisible = false" variant="text" text="Cancel" />
        <s-btn @click="saveDialog" color="primary" text="Save" />
      </v-card-actions>
    </template>
  </s-dialog>
</template>

<script setup lang="ts">
import type { MarkdownProps } from "@/composables/markdown";
import type { DesignerComponentBlock } from "@/components/Design/designer-components";

const props = defineProps<MarkdownProps & {
  item: DesignerComponentBlock;
  disabled?: boolean;
}>();
const emit = defineEmits<{
  update: [CodeChange[]];
}>();

const dialogVisible = ref(false);
const form = ref<any|null>(null);

function showDialog() {
  if (!form.value) {
    form.value = props.item.component.getUpdateForm(props.item);
  }
  dialogVisible.value = true;
}

function saveDialog() {
  dialogVisible.value = false;
  emit('update', props.item.component.update(props.item, form.value));
}
</script>

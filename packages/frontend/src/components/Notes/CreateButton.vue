<template>
  <v-btn-group 
    divided
    class="w-100 h-auto overflow-hidden"
  >
    <s-btn-secondary
      @click="performCreate()"
      :disabled="props.disabled"
      :loading="actionInProgress"
      prepend-icon="mdi-plus"
      class="flex-grow-width"
      size="small"
      data-testid="create-note-button"
    >
      Add
      <s-tooltip activator="parent" location="top" text="Add Note (Ctrl+J)" />
    </s-btn-secondary>
    
    <s-btn-secondary
      :disabled="props.disabled"
      size="small"
      class="split-button-menu"
    >
      <v-icon icon="mdi-menu-down" />
      
      <v-menu activator="parent" location="top end" :close-on-content-click="true">
        <v-list density="compact">
          <v-list-item
            @click="performCreate({ type: NoteType.TEXT })"
            prepend-icon="mdi-note-text-outline"
            title="Add Text Note"
            link
          />
          <v-list-item
            @click="performCreate({ type: NoteType.EXCALIDRAW })"
            prepend-icon="mdi-drawing"
            title="Add Excalidraw Note"
            link
            :disabled="props.preventCreateExcalidraw"
          />
        </v-list>
      </v-menu>
    </s-btn-secondary>
  </v-btn-group>
</template>

<script setup lang="ts">
const props = defineProps<{
  createNote: (data?: Partial<NoteBase>) => Promise<void>;
  disabled?: boolean;
  preventCreateExcalidraw?: boolean;
}>();

const actionInProgress = ref(false);
async function performCreate(data?: Partial<NoteBase>) {
  if (props.disabled || actionInProgress.value) {
    return;
  }
  try {
    actionInProgress.value = true;
    await Promise.resolve(props.createNote(data));
  } catch (error) {
    requestErrorToast({ error });
  } finally {
    actionInProgress.value = false;
  }
}

useKeyboardShortcut('ctrl+j', () => performCreate());

defineExpose({
  click: performCreate,
})
</script>

<style lang="scss" scoped>
.split-button-menu {
  min-width: 0;
}
</style>

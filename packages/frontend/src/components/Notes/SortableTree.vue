<template>
  <Draggable
    ref="draggableRef"
    :model-value="props.modelValue"
    @update:model-value="emit('update:modelValue', $event)"
    @open:node="setExpanded($event.data?.note, true)"
    @close:node="setExpanded($event.data?.note, false)"
    :stat-handler="statHandler"
    :disable-drag="props.disabled"
    :disable-drop="props.disabled"
    :update-behavior="props.disabled ? 'disabled' : 'new'"
    :tree-line="true"
    :tree-line-offset="12"
    :keep-placeholder="true"
    :indent="20"
  >
    <template #default="{ node: { note }, stat }">
      <!-- 
        The random URL parameter "?c" is required to prevent "Vuetify error: multiple nodes with the same ID". 
        While moving a note in the tree, two list items with the same URL exist in the DOM for a short time, 
        which triggers these Vuetify errors. 
        The random suffix gets re-generated on every move/update of the tree, which results in two different URLs for the same note list item.
      -->
      <v-list-item
        v-if="note"
        :to="(props.toPrefix) ? `${props.toPrefix}${note.id}/?c=${uuidv4()}` : undefined"
        @click="emit('update:selected', note)"
        link
        :active="props.selected ? props.selected.id === note.id : (props.toPrefix ? router.currentRoute.value.path.startsWith(props.toPrefix + note.id) : undefined)"
        :ripple="false"
        draggable="false"
        class="note-list-item"
      >
        <template #prepend>
          <div class="note-list-children-icon">
            <v-icon
              v-if="stat.children.length > 0"
              @click.stop.prevent="stat.open = !stat.open"
              :icon="stat.open ? 'mdi-menu-down' : 'mdi-menu-right'"
            />
          </div>
          <div class="note-icon">
            <v-icon v-if="note.checked === true" @click.stop.prevent="updateChecked(note, false)" size="small" class="text-disabled" icon="mdi-checkbox-marked" />
            <v-icon v-else-if="note.checked === false" @click.stop.prevent="updateChecked(note, true)" size="small" class="text-disabled" icon="mdi-checkbox-blank-outline" />
            <s-emoji v-else-if="note.icon_emoji" :value="note.icon_emoji" size="small" class="emoji-icon" />
            <v-icon v-else-if="stat.children.length > 0" size="small" class="text-disabled" icon="mdi-folder-outline" />
            <v-icon v-else size="small" class="text-disabled" icon="mdi-note-text-outline" />
          </div>
        </template>
        <template #default>
          <v-list-item-title class="text-body-2">
            <v-icon v-if="note.is_shared" size="small" icon="mdi-share-variant" />
            {{ note.title }}
          </v-list-item-title>
          <v-list-item-subtitle>
            <span v-if="note.assignee" :class="{'assignee-self': note.assignee.id == auth.user.value?.id}">
              @{{ note.assignee.username }}
            </span>
          </v-list-item-subtitle>
        </template>
        <template #append>
          <collab-avatar-group 
            v-if="props.collab"
            :collab="collabSubpath(props.collab, `notes.${note.id}`)"
          />
        </template>
      </v-list-item>
    </template>
  </Draggable>
</template>

<script setup lang="ts">
import { Draggable } from "@he-tree/vue";
import '@he-tree/vue/style/default.css';

const router = useRouter();
const auth = useAuth();
const localSettings = useLocalSettings();

const props = defineProps<{
  modelValue: NoteGroup<NoteBase>;
  selected?: NoteBase|null;
  toPrefix?: string;
  disabled?: boolean;
  collab?: CollabPropType;
}>();
const emit = defineEmits<{
  'update:modelValue': [NoteGroup<NoteBase>];
  'update:selected': [NoteBase|null];
  'update:checked': [NoteBase];
}>();

function statHandler(stat: any) {
  stat.open = localSettings.isNoteExpanded(stat.data.note.id);
  return stat;
}
function setExpanded(note: NoteBase|undefined, value: boolean) {
  if (!note) {
    return;
  }
  localSettings.setNoteExpandState({ noteId: note.id, isExpanded: value });
}
function updateChecked(note: NoteBase, checked: boolean) {
  if (props.disabled || !note) {
    return;
  }
  emit('update:checked', { ...note, checked });
}

const draggableRef = ref<InstanceType<typeof Draggable>>();
watch(() => props.modelValue, () => {
  if (!draggableRef.value) {
    return;
  }
  // Ensure that he-tree uses the same deeply reactive data as modelValue
  // If it is not explicitly set to the same instance, note titles are not reactive in certain conditions (after moving)
  // The update logic is similar to he-tree-vue BaseTree watch valueComputed 
  const processor = draggableRef.value.processor
  const isDragging = draggableRef.value.dragOvering || draggableRef.value.dragNode;
  if (processor && processor.data !== props.modelValue && !isDragging) {
    processor.data = props.modelValue;
    processor.init();
    draggableRef.value.stats = processor.stats!;
    draggableRef.value.statsFlat = processor.statsFlat!;
  }
}, { deep: true });

</script>

<style scoped lang="scss">
.note-list-item {
  min-height: 1em;
  padding-left: 0 !important;

  .note-list-children-icon {
    width: 1.5rem;
    min-width: 1.5rem;
    height: 1.5rem;

    :deep(.v-icon) {
      width: 1.5rem;
    }
  }

  .note-icon {
    width: 1.5rem;
    height: 1.5rem;

    .emoji-icon {
      padding-top: 2px
    }
  }
}

:deep() {
  .tree-hline {
    width: 10px;

    &:has(+ .tree-node-inner .note-list-children-icon):not(:has(+ .tree-node-inner .note-list-children-icon > i)) {
      width: 24px;
    }
  }

  .drag-placeholder {
    height: 2rem !important;
    width: 100%;
    background: rgba(var(--v-theme-on-surface), calc(var(--v-activated-opacity) * 2));
    border: 1px dashed rgba(var(--v-theme-on-surface), var(--v-high-emphasis-opacity));
  }

}
</style>

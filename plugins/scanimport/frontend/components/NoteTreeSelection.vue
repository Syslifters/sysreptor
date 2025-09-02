<template>
  <v-list density="compact">
    <Draggable
      ref="draggableRef"
      :model-value="props.noteGroup"
      @open:node="setExpanded($event.data?.note, true)"
      @close:node="setExpanded($event.data?.note, false)"
      :stat-handler="statHandler"
      update-behavior="disabled"
      :tree-line="true"
      :tree-line-offset="12"
      :keep-placeholder="true"
      :indent="20"
    >
      <template #default="{ node: { note }, stat }">
        <v-list-item
          v-if="note"
          @click="onClickNote($event, note, stat)"
          link
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
              <v-icon v-if="selectedNoteIds.includes(note.id)" size="small" class="text-disabled" icon="mdi-checkbox-marked" />
              <v-icon v-else size="small" class="text-disabled" icon="mdi-checkbox-blank-outline" />
            </div>
          </template>
          <template #default>
            <v-list-item-title class="text-body-2">
              <s-emoji v-if="note.icon_emoji" :value="note.icon_emoji" size="small" start class="emoji-icon" />
              {{ note.title }}
            </v-list-item-title>
          </template>
        </v-list-item>
      </template>
    </Draggable>
  </v-list>
</template>

<script setup lang="ts">
import { isEqual } from 'lodash-es';
import { Draggable } from "@he-tree/vue";
import '@he-tree/vue/style/default.css';

const props = defineProps<{
  noteGroup: NoteGroup<NoteBase>;
}>();

// Local reactive variable synced to model
const selectedNoteIdsModel = defineModel<string[]>('selectedNoteIds', { default: [] });
const selectedNoteIds = ref<string[]>([]);
watch(selectedNoteIdsModel, (newValue) => {
  if (!isEqual(newValue, selectedNoteIds.value)) {
    selectedNoteIds.value = [...(newValue || [])];
  }
}, { immediate: true });
watch(selectedNoteIds, (newValue) => { 
  if (!isEqual(newValue, selectedNoteIdsModel.value)) {
    selectedNoteIdsModel.value = [...newValue];
  }
}, { deep: 1 });

const collapsedNoteIds = ref<Set<string>>(new Set());
const lastSelectedNoteId = ref<string|null>(null);

function statHandler(stat: any) {
  stat.open = !collapsedNoteIds.value.has(stat.data.note.id);
  return stat;
}
function setExpanded(note: NoteBase|undefined, value: boolean) {
  if (!note) {
    return;
  }
  if (value) {
    collapsedNoteIds.value.delete(note.id);
  } else {
    collapsedNoteIds.value.add(note.id);
  }
}

const draggableRef = useTemplateRef('draggableRef');
watch(() => props.noteGroup, () => {
  if (!draggableRef.value) {
    return;
  }
  // Ensure that he-tree uses the same deeply reactive data as modelValue
  // If it is not explicitly set to the same instance, note titles are not reactive in certain conditions (after moving)
  // The update logic is similar to he-tree-vue BaseTree watch valueComputed 
  const processor = draggableRef.value.processor
  if (processor && processor.data !== props.noteGroup) {
    processor.data = props.noteGroup;
    processor.init();
    draggableRef.value.stats = processor.stats!;
    draggableRef.value.statsFlat = processor.statsFlat!;
  }
}, { deep: true });

function getNoteGroupById(id?: string|null, group?: NoteGroup<NoteBase>): NoteGroup<NoteBase>[0]|null {
  if (!id) {
    return null;
  }

  for (const item of group || props.noteGroup) {
    if (item.note.id === id) {
      return item;
    }
    if (item.children.length > 0) {
      const found = getNoteGroupById(id, item.children);
      if (found) {
        return found;
      }
    }
  }
  return null;
}
function selectNote(note?: NoteBase|null, value: boolean = true) {
  const group = getNoteGroupById(note?.id);
  console.log('selectNote', value, note, group)
  if (!note || !group) {
    return;
  }

  if (value) {
    // Select note and parents
    selectedNoteIds.value = selectedNoteIds.value.concat([note.id]);
    for (
      let n = note as (typeof note|null);
      n;
      n = getNoteGroupById(n.parent, props.noteGroup)?.note as (typeof note|null)
    ) {
      selectedNoteIds.value.push(n.id);
    }
  } else {
    selectedNoteIds.value = selectedNoteIds.value.filter(id => id !== note.id);
  }
  
  // Select children
  for (const c of group.children) {
    selectNote(c.note, value);
  }
}
function onClickNote(event: MouseEvent|KeyboardEvent, note?: NoteBase, stat?: any) {
  if (!note || !stat) {
    return;
  }
  console.log('onClickNote', event, note, stat)

  if (event.shiftKey) {
    // Select all leaf notes between the last selected note and the current one.
    // Parents are auto-selected if any child is selected.
    const idxSelectionStart = (draggableRef.value?.statsFlat || []).findIndex(s => (s.data as NoteGroup<NoteBase>[0]|null)?.note?.id === (lastSelectedNoteId.value || props.noteGroup[0]?.note.id));
    const idxSelectionEnd = (draggableRef.value?.statsFlat || []).findIndex(s => (s.data as NoteGroup<NoteBase>[0]|null)?.note?.id === note.id);
    
    if (idxSelectionStart === -1 || idxSelectionEnd === -1) {
      selectNote(note);
    } else {
      const notesToSelect = draggableRef.value?.statsFlat
        .slice(Math.min(idxSelectionStart, idxSelectionEnd), Math.max(idxSelectionStart, idxSelectionEnd) + 1)
        .map((s: any) => (s.data as NoteGroup<NoteBase>[0]|null)?.note)
        .filter(n => !!n);
      const allSelected = notesToSelect.every(s => s && selectedNoteIds.value.includes(s.id));
      notesToSelect.forEach(s => selectNote(s, !allSelected));
    }

    lastSelectedNoteId.value = note.id;
    event.preventDefault();
  } else {
    selectNote(note, !selectedNoteIds.value.includes(note.id));
    lastSelectedNoteId.value = note.id;
    event.preventDefault()
  }
}

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
      vertical-align: text-bottom;
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
}
</style>

<template>
  <Draggable
    ref="draggableRef"
    :model-value="props.modelValue"
    @update:model-value="onUpdateModelValue"
    @open:node="setExpanded($event.data?.note, true)"
    @close:node="setExpanded($event.data?.note, false)"
    :stat-handler="statHandler"
    :disable-drag="props.disabled"
    :disable-drop="props.disabled"
    :update-behavior="props.disabled ? 'disabled' : 'new'"
    :ondragstart="onDragStart"
    @after-drop="onAfterDrop"
    :tree-line="true"
    :tree-line-offset="12"
    :keep-placeholder="true"
    :indent="20"
    :virtualization="true"
    class="h-100"
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
        @click="onClickNote($event, note, stat)"
        link
        :active="note.id === currentNoteId"
        :class="{
          'note-list-item--selected': selectedNoteIds.has(note.id),
        }"
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
            <v-icon v-else-if="note.type === NoteType.EXCALIDRAW" size="small" class="text-disabled" icon="mdi-drawing" />
            <v-icon v-else size="small" class="text-disabled" icon="mdi-note-text-outline" />
          </div>
        </template>
        <template #default>
          <v-list-item-title class="text-body-medium">
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
          <collab-avatar-group :collab="collabSubpathProps[`notes.${note.id}`]"/>
        </template>
      </v-list-item>
    </template>
  </Draggable>
</template>

<script setup lang="ts">
import { Draggable, dragContext } from "@he-tree/vue";
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

const currentNoteId = computed(() => props.selected ? props.selected.id : router.currentRoute.value.params.noteId as string || null);
const selectedNoteIds = ref<Set<string>>(new Set());
const isBulkDragging = ref(false);

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

const draggableRef = useTemplateRef('draggableRef');
watch(() => props.modelValue, () => {
  if (!draggableRef.value) {
    return;
  }
  // Ensure that he-tree uses the same deeply reactive data as modelValue
  // If it is not explicitly set to the same instance, note titles are not reactive in certain conditions (after moving)
  // The update logic is similar to he-tree-vue BaseTree watch valueComputed 
  const processor = draggableRef.value.processor
  const isDragging = draggableRef.value.dragOvering || !!draggableRef.value.dragNode || isBulkDragging.value;
  if (processor && processor.data !== props.modelValue && !isDragging) {
    processor.data = props.modelValue;
    processor.init();
    draggableRef.value.stats = processor.stats!;
    draggableRef.value.statsFlat = processor.statsFlat!;
  }
}, { deep: true });

const subpathNames = computedCached(() => flattenNotes(props.modelValue).map(n => `notes.${n.id}`));
const collabSubpathProps = useCollabSubpaths(() => props.collab, subpathNames);

const lastSelectedNoteId = ref<string|null>(null);
function getNoteGroupById(id?: string|null, group?: NoteGroup<NoteBase>): NoteGroup<NoteBase>[0]|null {
  if (!id) {
    return null;
  }

  for (const item of group || props.modelValue) {
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
  if (!note || !group) {
    return;
  }

  if (value) {
    selectedNoteIds.value.add(note.id);
  } else {
    // Unselect note and parents
    for (
      let n = note as (typeof note|null);
      n;
      n = getNoteGroupById(n.parent, props.modelValue)?.note as (typeof note|null)
    ) {
      selectedNoteIds.value.delete(n.id);
    }
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

  if (event.shiftKey) {
    // Select all leaf notes between the last selected note and the current one.
    // Parents are auto-selected if all children are selected.
    const idxSelectionStart = (draggableRef.value?.statsFlat || []).findIndex(s => (s.data as NoteGroup<NoteBase>[0]|null)?.note?.id === lastSelectedNoteId.value);
    const idxSelectionEnd = (draggableRef.value?.statsFlat || []).findIndex(s => (s.data as NoteGroup<NoteBase>[0]|null)?.note?.id === note.id);
    
    if (idxSelectionStart === -1 || idxSelectionEnd === -1) {
      selectNote(note);
    } else {
      draggableRef.value?.statsFlat
        .slice(Math.min(idxSelectionStart, idxSelectionEnd), Math.max(idxSelectionStart, idxSelectionEnd) + 1)
        .forEach(s => {
          const sNote = (s.data as NoteGroup<NoteBase>[0]|null)?.note;
          if (sNote) {
            selectNote(sNote, true);
          }
        });
    }

    lastSelectedNoteId.value = note.id;
    event.preventDefault();
  } else if (event.ctrlKey) {
    selectNote(note, !selectedNoteIds.value.has(note.id) || currentNoteId.value === note.id);
    lastSelectedNoteId.value = note.id;
    event.preventDefault();
  } else {
    emit('update:selected', note);
  }
}
watch(currentNoteId, () => {
  // On navigate: reset selection
  selectedNoteIds.value.clear();
  if (currentNoteId.value) {
    selectedNoteIds.value.add(currentNoteId.value);
  }
  lastSelectedNoteId.value = currentNoteId.value;
}, { immediate: true });

const selectedNotes = computed(() => {
  return Array.from(selectedNoteIds.value)
    .map(id => getNoteGroupById(id)?.note)
    .filter(n => !!n);
});
const selectedNoteGroupsTopLevel = computed(() => {
  // Preserve original order as in the tree
  const noteIdsOrdered = draggableRef.value?.statsFlat
    .filter(s => selectedNoteIds.value.has((s.data as any)?.note?.id))
    .map(s => (s.data as any)?.note?.id) 
    ?? Array.from(selectedNoteIds.value);
  return noteIdsOrdered
    .map(id => getNoteGroupById(id))
    .filter(g => g && (!g.note.parent || !selectedNoteIds.value.has(g.note.parent)))
    .filter(g => !!g)
});

function cloneTree(tree: NoteGroup<NoteBase>, options?: { removeIds?: Set<string> }): NoteGroup<NoteBase> {
  return tree
    .filter(g => !options?.removeIds?.has(g.note.id))
    .map(g => ({ note: g.note, children: cloneTree(g.children, options) }));
}

function onDragStart() {
  const draggedId = draggableRef.value?.dragNode?.data?.note?.id;
  if (!draggedId || !selectedNoteIds.value.has(draggedId) || selectedNoteIds.value.size <= 1) {
    return;
  }

  isBulkDragging.value = true;
  // Ensure we always clean up even if drop is cancelled
  window.addEventListener('dragend', () => {
    draggableRef.value?.statsFlat
      .filter(s => selectedNoteIds.value.has((s.data as any)?.note?.id))
      .forEach(s => { s.hidden = false; });
  }, { once: true });

  // Hide moving notes from tree
  setTimeout(() => {
    draggableRef.value?.statsFlat
      .filter(s => selectedNoteIds.value.has((s.data as any)?.note?.id))
      .forEach(s => { s.hidden = true; });
  }, 0);
}

function onAfterDrop() {
  try {
    const draggedId = dragContext?.dragNode?.data?.note?.id;
    if (!draggedId || !selectedNoteIds.value.has(draggedId) || !isBulkDragging.value) {
      // Single note dragged, use default logic
      return;
    }

    // Move selected notes to drop position
    const newValue = cloneTree(props.modelValue, { removeIds: selectedNoteIds.value });
    const dropParentId = (dragContext?.targetInfo?.parent?.data as NoteGroup<NoteBase>[0] | null)?.note?.id ?? null;
    const dropParentGroup = getNoteGroupById(dropParentId, newValue);
    const dropIndex = dragContext?.targetInfo?.indexBeforeDrop;
    if (!dropParentGroup || !Number.isInteger(dropIndex)) {
      return;
    }
    dropParentGroup.children.splice(dropIndex, 0, ...selectedNoteGroupsTopLevel.value);

    // Exit drag mode
    if (draggableRef.value) {
      draggableRef.value.dragOvering = false;
      draggableRef.value.dragNode = null;
      isBulkDragging.value = false;
    }
    emit('update:modelValue', newValue);
  } finally {
    isBulkDragging.value = false;
  }
}

function onUpdateModelValue(tree: NoteGroup<NoteBase>) {
  if (isBulkDragging.value) {
    return;
  }
  emit('update:modelValue', tree);
}

async function focusCurrentNote() {
  if (!currentNoteId.value || !draggableRef.value || !props.modelValue.length) { 
    return;
  }
  const noteGroupItem = getNoteGroupById(currentNoteId.value);
  if (!noteGroupItem) { 
    return;
  }
  // Expand all ancestors via he-tree's built-in API
  let parentId = noteGroupItem.note.parent;
  while (parentId) {
    localSettings.setNoteExpandState({ noteId: parentId, isExpanded: true });
    parentId = getNoteGroupById(parentId)?.note.parent ?? null;
  }
  await nextTick();

  // Scroll in virtual tree such that the note gets rendered to DOM
  const vtlist = draggableRef.value.$refs.vtlist as any|null;
  const nodeIndex = vtlist?.items.findIndex((s: any) => s.data && s.data?.note.id === noteGroupItem.note.id);
  const scrollOffset = vtlist?.positions[nodeIndex] ?? 0;
  vtlist?.listElRef?.scrollTo({ top: scrollOffset, behavior: 'instant' });
  await nextTick();
  
  // Scroll to note
  draggableRef.value.$el
    ?.querySelector('.v-list-item--active')
    ?.scrollIntoView({ block: 'center', behavior: 'instant' });
}
whenever(() => props.modelValue.length > 0 && !!draggableRef.value, async () => {
  await focusCurrentNote();
}, { immediate: true, once: true });

defineExpose({
  selectedNotes,
});
</script>

<style scoped lang="scss">
.note-list-item {
  min-height: 1em;
  padding-left: 0;

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
    background: color-mix(in srgb, rgb(var(--v-theme-on-surface)) calc((var(--v-activated-opacity) * 2) * 100%), transparent);
    border: 1px dashed color-mix(in srgb, rgb(var(--v-theme-on-surface)) calc(var(--v-high-emphasis-opacity) * 100%), transparent);
  }
}
.note-list-item--selected {
  background: color-mix(in srgb, rgb(var(--v-theme-on-surface)) calc((var(--v-activated-opacity)) * 100%), transparent);
}
</style>

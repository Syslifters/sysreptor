<template>
  <draggable
    :model-value="localValue"
    @update:model-value="updateModelValue"
    :item-key="item => item.note.id"
    group="notes"
    :delay="50"
    :disabled="props.disabled"
    class="pb-1"
  >
    <template #item="{ element: item }">
      <div>
        <v-list-item
          :to="toPrefix + item.note.id + '/'"
          :ripple="false"
          class="note-list-item"
        >
          <template #prepend>
            <div class="note-list-children-icon">
              <v-icon
                v-if="item.children.length > 0"
                @click.stop.prevent="toggleExpanded(item.note)"
                :icon="isExpanded(item.note) ? 'mdi-menu-down' : 'mdi-menu-right'"
              />
            </div>
            <div class="note-icon">
              <v-icon v-if="item.note.checked === true" @click.stop.prevent="updateChecked(item.note, false)" size="small" class="text-disabled" icon="mdi-checkbox-marked" />
              <v-icon v-else-if="item.note.checked === false" @click.stop.prevent="updateChecked(item.note, true)" size="small" class="text-disabled" icon="mdi-checkbox-blank-outline" />
              <s-emoji v-else-if="item.note.icon_emoji" :value="item.note.icon_emoji" size="small" class="emoji-icon" />
              <v-icon v-else-if="item.children.length > 0" size="small" class="text-disabled" icon="mdi-folder-outline" />
              <v-icon v-else size="small" class="text-disabled" icon="mdi-note-text-outline" />
            </div>
            <s-lock-info :value="item.note.lock_info" />
          </template>
          <template #default>
            <v-list-item-title class="text-body-2">{{ item.note.title }}</v-list-item-title>
            <v-list-item-subtitle>
              <span v-if="item.note.assignee" :class="{'assignee-self': item.note.assignee.id == auth.user.value!.id}">
                @{{ item.note.assignee.username }}
              </span>
            </v-list-item-subtitle>
          </template>
          <template #append>
            <div v-if="item.note.status_emoji" class="note-icon">
              <s-emoji :value="item.note.status_emoji" size="small" class="emoji-icon" />
            </div>
          </template>
        </v-list-item>

        <v-list v-if="isExpanded(item.note)" density="compact" class="pt-0 pb-0">
          <notes-sortable-list
            :model-value="item.children || []"
            @update:model-value="v => updateChildren(item, v)"
            @update:note="$emit('update:note', $event)"
            :disabled="props.disabled"
            :to-prefix="props.toPrefix"
            class="child-list"
          />
        </v-list>
      </div>
    </template>
  </draggable>
</template>

<script setup lang="ts">
import Draggable from "vuedraggable";

const auth = useAuth();
const localSettings = useLocalSettings();

const props = defineProps<{
  modelValue: NoteGroup<UserNote>;
  toPrefix: string;
  disabled?: boolean;
}>();
const emit = defineEmits<{
  (e: 'update:modelValue', value: NoteGroup<UserNote>): void;
  (e: 'update:note', value: UserNote): void;
}>();

const localValue = ref([...props.modelValue]);
watch(() => props.modelValue, (val) => {
  localValue.value = val;
}, { immediate: true });

function isExpanded(note: UserNote) {
  return localSettings.isNoteExpanded(note.id);
}
function toggleExpanded(note: UserNote) {
  localSettings.setNoteExpandState({ noteId: note.id, isExpanded: !isExpanded(note) });
}

function updateModelValue(val: NoteGroup<UserNote>) {
  localValue.value = val;
  emit('update:modelValue', localValue.value);
}
function updateChildren(item: { note: UserNote, children: NoteGroup<UserNote> }, children: NoteGroup<UserNote>) {
  const itemIdx = localValue.value.findIndex(i => i.note.id === item.note.id);
  localValue.value[itemIdx] = Object.assign({}, localValue.value[itemIdx], { children });
  emit('update:modelValue', localValue.value);
}
function updateChecked(note: UserNote, checked: boolean) {
  if (note.lock_info) {
    return;
  }
  emit('update:note', { ...note, checked });
}
</script>

<style lang="scss" scoped>
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

.child-list {
  padding-left: 1rem;
}

:deep(.v-list-item-subtitle) {
  font-size: x-small !important;
}
</style>

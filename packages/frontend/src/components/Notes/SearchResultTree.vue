<template>
  <Draggable
    :model-value="props.modelValue"
    update-behavior="disabled"
    :disable-drag="true"
    :disable-drop="true"
    :tree-line="false"
    :indent="20"
  >
    <template #default="{ node: { item: note }, stat }">
      <v-list-item
        :to="noteUrl(note)"
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
            <v-icon v-if="note.checked === true" size="small" class="text-disabled" icon="mdi-checkbox-marked" />
            <v-icon v-else-if="note.checked === false" size="small" class="text-disabled" icon="mdi-checkbox-blank-outline" />
            <s-emoji v-else-if="note.icon_emoji" :value="note.icon_emoji" size="small" class="emoji-icon" />
            <v-icon v-else-if="stat.children.length > 0" size="small" class="text-disabled" icon="mdi-folder-outline" />
            <v-icon v-else size="small" class="text-disabled" icon="mdi-note-text-outline" />
          </div>
        </template>
        <template #default>
          <v-list-item-title class="text-body-2">{{ note.title }}</v-list-item-title>
        </template>
      </v-list-item>

      <search-match-list
        :result="stat.data"
        :to-prefix="noteUrl(note)"
        class="match-list"
      />
    </template>
  </Draggable>
</template>

<script setup lang="ts">
import { Draggable } from "@he-tree/vue";
import '@he-tree/vue/style/default.css';

const props = defineProps<{
  modelValue: NoteSearchResults<NoteBase>;
  toPrefix: string;
}>();

function noteUrl(note: NoteBase,) {
  return `${props.toPrefix}${note.id}/`;
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
      padding-top: 2px
    }
  }
}

.match-list {
  padding-left: 1.2rem;
}
</style>

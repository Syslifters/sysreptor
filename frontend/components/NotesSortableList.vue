<template>
  <draggable 
    :value="localValue"
    @input="updateValue"
    draggable=".draggable-item" 
    group="notes" 
    :delay="50"
    :disabled="disabled"
    class="pb-1"
  >
    <div v-for="item in value" :key="item.note.id" class="draggable-item">
      <v-list-item 
        :to="toPrefix + item.note.id + '/'" nuxt
        :ripple="false"
        class="note-list-item" :class="item.children.length > 0 ? 'note-list-item--children': 'note-list-item--no-children'"
      >
        <v-icon v-if="item.children.length > 0" @click.stop.prevent="toggleExpanded(item.note)" class="note-list-children-icon">
          <template v-if="isExpanded(item.note)">mdi-menu-down</template>
          <template v-else>mdi-menu-right</template>
        </v-icon>

        <v-list-item-content>
          <v-list-item-title>
            <v-icon v-if="item.note.checked === true" @click.stop.prevent="updateChecked(item.note, false)" dense class="text--disabled">mdi-checkbox-marked</v-icon>
            <v-icon v-else-if="item.note.checked === false" @click.stop.prevent="updateChecked(item.note, true)" dense class="text--disabled">mdi-checkbox-blank-outline</v-icon>
            <s-emoji v-else-if="item.note.icon_emoji" :value="item.note.icon_emoji" small />
            <v-icon v-else-if="item.children.length > 0" dense class="text--disabled">mdi-folder-outline</v-icon>
            <v-icon v-else dense class="text--disabled">mdi-note-text-outline</v-icon>

            <lock-info :value="item.note.lock_info" />
            {{ item.note.title }}
          </v-list-item-title>
        </v-list-item-content>

        <v-list-item-icon v-if="item.note.status_emoji" class="emoji-status">
          <s-emoji :value="item.note.status_emoji" small />
        </v-list-item-icon>
      </v-list-item>

      <v-list v-if="isExpanded(item.note)" dense class="pt-0 pb-0">
        <notes-sortable-list 
          :value="item.children || []" 
          @input="v => updateChildren(item, v)"
          @update:note="$emit('update:note', $event)"
          :disabled="disabled" 
          :to-prefix="toPrefix" 
          class="child-list"
        />
      </v-list>
    </div>
  </draggable>
</template>

<script>
import Draggable from 'vuedraggable';

export default {
  components: { Draggable },
  props: {
    value: {
      type: Array,
      required: true,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    toPrefix: {
      type: String,
      required: true,
    },
  },
  emits: ['input'],
  data() {
    return {
      localValue: [...this.value],
    }
  },
  watch: {
    value: {
      immediate: true,
      handler(val) {
        this.localValue = [...val];
      }
    },
  },
  methods: {
    isExpanded(note) {
      return this.$store.getters['settings/isNoteExpanded'](note.id);
    },
    toggleExpanded(note) {
      this.$store.commit('settings/setNoteExpandState', { noteId: note.id, isExpanded: !this.isExpanded(note) })
    },
    updateValue(val) {
      this.localValue = val;
      this.$emit('input', this.localValue);
    },
    updateChildren(item, children) {
      const itemIdx = this.localValue.findIndex(i => i.note.id === item.note.id);
      this.localValue[itemIdx] = Object.assign({}, this.localValue[itemIdx], { children });
      this.$emit('input', this.localValue);
    },
    updateChecked(note, checked) {
      if (note.lock_info !== null) {
        return;
      }

      this.$emit('update:note', { id: note.id, checked });
    }
  }
}
</script>

<style lang="scss" scoped>
.note-list-item {
  min-height: 1em;

  &--children {
    padding-left: 0;
  }
  &--no-children {
    padding-left: 1rem;
  }

  .note-list-children-icon {
    width: 1rem;
  }

  :deep() {
    .v-icon:focus::after {
      opacity: 0;
    }

    .lock-info-icon {
      margin: 0 !important;
      height: 1rem;
    }
  }
}

.child-list {
  padding-left: 1rem;
}

.emoji-status {
  margin-top: 6px !important;
  margin-bottom: 6px !important;
  
  &:deep(.emoji-mart-emoji) {
    padding: 2px;
  }
}
</style>

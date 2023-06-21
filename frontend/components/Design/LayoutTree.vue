<template>
  <draggable
    :value="value.children"
    draggable=".draggable-item"
    filter=".draggable-item-disabled"
    :group="{name: 'designerComponents', put: ['designerComponents', 'predefinedDesignerCompnents']}" 
    @change="onChange"
    :delay="50"
    :disabled="disabled"
    class="pb-1"
  >
    <div v-for="item in value.children" :key="item.id" class="draggable-item" :class="{'draggable-item-disabled': !item.canMove}">
      <v-list-item class="list-item" link :ripple="false">
        <v-list-item-icon>
          <v-icon>mdi-drag-horizontal</v-icon>
        </v-list-item-icon>
        <v-list-item-content>
          <v-list-item-title>
            {{ item.component.name }}<template v-if="item.title">: <code>{{ item.title }}</code></template>
            <template v-if="item.tagInfo.attributes.id">(<code>id="{{ item.tagInfo.attributes.id.value }}"</code>)</template>
          </v-list-item-title>
        </v-list-item-content>
        <v-list-item-action v-if="['markdown', 'headline'].includes(item.component.type) && item.canUpdate">
          <design-layout-component-edit-dialog 
            :item="item" 
            :upload-file="uploadFile"
            :rewrite-file-url="rewriteFileUrl"
            :disabled="disabled"
            @update="$emit('update', $event)"
          />
        </v-list-item-action>
        <v-list-item-action v-if="item.cssPosition">
          <s-tooltip>
            <template #activator="{on, attrs}">
              <s-btn
                @click="$emit('jump-to-code', {tab: 'css', position: item.cssPosition})"
                v-bind="attrs"
                v-on="on"
                icon
                small
              >
                <v-icon small>mdi-code-braces</v-icon>
              </s-btn>
            </template>

            <span>Go to CSS</span>
          </s-tooltip>
        </v-list-item-action>
        <v-list-item-action v-if="item.htmlPosition">
          <s-tooltip>
            <template #activator="{on, attrs}">
              <s-btn
                @click="$emit('jump-to-code', {tab: 'html', position: item.htmlPosition})"
                v-bind="attrs"
                v-on="on"
                icon
                small
              >
                <v-icon small>mdi-code-tags</v-icon>
              </s-btn>
            </template>

            <span>Go to HTML</span>
          </s-tooltip>
        </v-list-item-action>
      </v-list-item>

      <v-list v-if="item.component.supportsChildren" dense class="pt-0 pb-0">
        <design-layout-tree
          :value="item"
          :upload-file="uploadFile"
          :rewrite-file-url="rewriteFileUrl"
          :disabled="disabled"
          v-on="$listeners"
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
      type: Object,
      required: true,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    uploadFile: {
      type: Function,
      default: null,
    },
    rewriteFileUrl: {
      type: Function,
      default: null,
    },
  },
  emits: ['change-list', 'update', 'jump-to-code'],
  methods: {
    onChange(e) {
      if (e.moved) {
        e.moved.parent = this.value;
      }
      if (e.added) {
        e.added.parent = this.value;
      }
      if (e.removed) {
        e.removed.parent = this.value;
      }
      this.$emit('change-list', e);
    },
  }
}
</script>

<style lang="scss" scoped>
.child-list {
  margin-left: 1rem;
}

.list-item {
  cursor: grab;
  min-height: 1em;

  & .v-list-item__action {
    margin-top: 0;
    margin-bottom: 0;
  }

  & .v-list-item__icon {
    margin-right: 0.5em;
    margin-top: 2px;
    margin-bottom: 2px;
  }
}
</style>

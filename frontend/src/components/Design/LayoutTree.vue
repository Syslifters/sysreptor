<template>
  <draggable
    :model-value="value.children"
    item-key="id"
    handle=".draggable-handle"
    filter=".draggable-item-disabled"
    :group="{name: 'designerComponents', put: ['designerComponents', 'predefinedDesignerComponents']}"
    @change="onChange"
    :disabled="disabled"
    class="pb-1"
  >
    <template #item="{ element: item }">
      <div>
        <v-list-item class="list-item" link :ripple="false">
          <template #prepend>
            <v-icon :disabled="props.disabled" icon="mdi-drag-horizontal" class="draggable-handle" />
          </template>

          <template #default>
            <v-list-item-title class="text-body-2">
              {{ item.component.name }}<span v-if="item.title">: <s-code>{{ item.title }}</s-code></span>
              <span v-if="item.tagInfo.attributes.id"> (<s-code>id="{{ item.tagInfo.attributes.id.value }}"</s-code>)</span>
            </v-list-item-title>
          </template>

          <template #append>
            <design-layout-component-edit-dialog
              v-if="['markdown', 'headline'].includes(item.component.type) && item.canUpdate"
              :item="item"
              v-bind="markdownProps"
              @update="emit('update', $event)"
            />

            <s-btn
              v-if="item.cssPosition"
              @click="emit('jumpToCode', {tab: PdfDesignerTab.CSS, position: item.cssPosition})"
              icon
              variant="text"
              size="small"
              density="comfortable"
              class="ml-1 mr-1"
            >
              <v-icon>mdi-code-braces</v-icon>
              <s-tooltip activator="parent" text="Go to CSS" />
            </s-btn>

            <s-btn
              @click="emit('jumpToCode', {tab: PdfDesignerTab.HTML, position: item.htmlPosition})"
              icon
              variant="text"
              size="small"
              density="comfortable"
              class="ml-1 mr-1"
            >
              <v-icon>mdi-code-tags</v-icon>
              <s-tooltip activator="parent" text="Go to HTML" />
            </s-btn>
          </template>
        </v-list-item>

        <v-list v-if="item.component.supportsChildren" density="compact" class="pt-0 pb-0">
          <design-layout-tree
            :value="item"
            v-bind="markdownProps"
            @jump-to-code="emit('jumpToCode', $event)"
            @update="emit('update', $event)"
            @change-list="emit('changeList', $event)"
            class="child-list"
          />
        </v-list>
      </div>
    </template>
  </draggable>
</template>

<script setup lang="ts">
import Draggable from "vuedraggable";
import pick from "lodash/pick";
import type { MarkdownProps } from "~/composables/markdown";
import type { DesignerComponentBlock } from "~/components/Design/designer-components";
import { PdfDesignerTab } from "~/utils/types";

const props = defineProps<MarkdownProps & {
  value: DesignerComponentBlock;
  disabled?: boolean;
}>();
const emit = defineEmits<{
  changeList: [any];
  update: [CodeChange[]];
  jumpToCode: [{ tab: PdfDesignerTab, position: DocumentSelectionPosition }];
}>();

const markdownProps = computed(() => pick(props, ['disabled', 'lang', 'uploadFile', 'rewriteFileUrl', 'rewriteReferenceLink']));

function onChange(e: any) {
  if (e.moved) {
    e.moved.parent = props.value;
  }
  if (e.added) {
    e.added.parent = props.value;
  }
  if (e.removed) {
    e.removed.parent = props.value;
  }
  emit('changeList', e);
}
</script>

<style lang="scss" scoped>
.child-list {
  margin-left: 1rem;
}

.draggable-handle {
  cursor: grab;
}

.list-item {
  min-height: 1em;

  & :deep(.v-list-item__prepend) {
    margin-top: 0;
    margin-bottom: 0;

    .v-list-item__spacer {
      width: 0.5em;
    }
  }

  & .v-list-item__append {
    margin-right: 0.5em;
    margin-top: 2px;
    margin-bottom: 2px;
  }
}
</style>

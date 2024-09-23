<template>
  <div v-intersect="onIntersect" class="h-100">
    <split-menu :model-value="20">
      <template #menu>
        <v-list density="compact">
          <div v-for="group in predefinedDesignerComponentGroups" :key="group.name">
            <v-list-subheader>{{ group.name }}</v-list-subheader>
            <draggable
              :model-value="group.components"
              :item-key="(c: DesignerComponent) => group.name + '-' + c.type"
              :sort="false"
              :group="{name: 'predefinedDesignerComponents', pull: 'clone', put: false}"
            >
              <template #item="{ element: c }">
                <v-list-item link :ripple="false" prepend-icon="mdi-drag" class="draggable-item">
                  <v-list-item-title class="text-body-2">{{ c.name }}</v-list-item-title>
                </v-list-item>
              </template>
            </draggable>
          </div>
        </v-list>
      </template>

      <template #default>
        <v-list v-if="htmlTree" density="compact">
          <design-layout-tree
            :value="htmlTree"
            v-bind="markdownProps"
            @change-list="onChangeList"
            @update="updateCode"
            @jump-to-code="emit('jump-to-code', $event)"
            class="draggable-component-tree"
          />
        </v-list>
        <div v-else class="text-center">
          <v-progress-circular indeterminate />
        </div>

        <s-dialog
          v-if="addDialog?.form"
          v-model="addDialog.visible"
        >
          <template #title>{{ addDialog.component!.name }}</template>
          <template #default>
            <v-card-text>
              <design-layout-component-form
                v-model="addDialog.form"
                v-bind="markdownProps"
              />
            </v-card-text>
            <v-card-actions>
              <v-spacer />
              <s-btn-other @click="addDialog.visible = false" text="Cancel" />
              <s-btn-primary @click="addPredefinedComponent" text="Add" />
            </v-card-actions>
          </template>
        </s-dialog>
      </template>
    </split-menu>
  </div>
</template>

<script setup lang="ts">
import { sortBy } from "lodash-es";
import Draggable from "vuedraggable";
import type { MarkdownProps, PdfDesignerTab } from "#imports";
import {
  type DesignerComponent,
  type DesignerComponentBlock,
  predefinedDesignerComponentGroups,
  parseToComponentTree,
  DesignerComponentBase
} from '~/components/Design/designer-components';

const props = defineProps<{
  projectType: ProjectType;
  disabled?: boolean;
} & MarkdownProps>();
const emit = defineEmits<{
  'update': [{ html: string, css: string, formatHtml?: boolean, reloadPdf?: boolean }];
  'jump-to-code': [{ tab: PdfDesignerTab, position: DocumentSelectionPosition }];
}>();

const markdownProps = computed(() => ({
  disabled: props.disabled,
  lang: props.lang || props.projectType.language,
  uploadFile: props.uploadFile,
  rewriteFileUrl: props.rewriteFileUrl,
  rewriteReferenceLink: props.rewriteReferenceLink,
}));

const isVisible = ref(true);
const htmlTreeUpdatePending = ref(true);
const htmlTree = ref<DesignerComponentBlock|null>(null);
const pendingListEvents = ref<any[]>([]);
const addDialog = ref({
  visible: false,
  component: null as DesignerComponent|null,
  form: null as any|number,
  event: null as any|null,
});

function refreshHtmlTree() {
  htmlTree.value = parseToComponentTree(props.projectType.report_template, props.projectType.report_styles, props.projectType);
  htmlTreeUpdatePending.value = false;
}
watch([
  () => props.projectType.report_template,
  () => props.projectType.report_styles
], () => {
  if (isVisible.value) {
    refreshHtmlTree();
  } else {
    htmlTreeUpdatePending.value = true;
  }
})
function onIntersect(isIntersecting: boolean) {
  // Do not refresh htmlTree if this tab is not visible because its slow (e.g. when editing HTML)
  // When the tab becomes visible again
  isVisible.value = isIntersecting;
  if (isVisible.value && htmlTreeUpdatePending.value) {
    refreshHtmlTree();
  }
}

function spliceStringChanges(original: string, changes: StringChange[]) {
  let out = '';
  let lastChange = { from: 0, deleteCount: 0, add: '' };
  for (const change of sortBy(changes, 'from')) {
    out += original.slice(lastChange.from + lastChange.deleteCount, change.from);
    out += change.add;
    lastChange = change;
  }
  out += original.slice(lastChange.from + lastChange.deleteCount);
  return out;
}
function updateCode(changes: CodeChange[]) {
  emit('update', {
    html: spliceStringChanges(props.projectType.report_template, changes.filter(c => c.type === 'html')),
    css: spliceStringChanges(props.projectType.report_styles, changes.filter(c => c.type === 'css')),
    formatHtml: true,
    reloadPdf: true,
  });
}
function addPredefinedComponent() {
  const addedCode = addDialog.value.component?.createCode(addDialog.value.form, htmlTree.value!.context);
  if (addedCode) {
    const changes = [];
    if (addedCode.html) {
      const ea = addDialog.value.event!;
      const destinationOffset = (ea.newIndex < ea.parent.children.length) ? ea.parent.children[ea.newIndex].htmlPosition.from : ea.parent.childrenArea.to;
      changes.push({ type: 'html', from: destinationOffset, deleteCount: 0, add: '\n\n' + addedCode.html + '\n\n' });
    }
    if (addedCode.css) {
      changes.push({ type: 'css', from: props.projectType.report_styles.length, deleteCount: 0, add: '\n\n' + addedCode.css })
    }
    updateCode(changes);
  }

  addDialog.value.visible = false;
}
async function onChangeList(event: any) {
  // When moving items from different list levels, two events are fired: first add, then remove
  // We need to process them in one tick, otherwise the offsets may be incorrect.
  pendingListEvents.value.push(event);
  const lastEventState = [...pendingListEvents.value];
  await nextTick();
  if (lastEventState.length !== pendingListEvents.value.length || !lastEventState.every((elem, idx) => pendingListEvents.value[idx] === elem)) {
    return;
  }

  if (pendingListEvents.value.length === 1 && pendingListEvents.value[0].moved) {
    // Element moved within the same list
    const e = pendingListEvents.value[0].moved;
    const destinationIndex = (e.newIndex <= e.oldIndex) ? e.newIndex : e.newIndex + 1;
    const destinationOffset = (destinationIndex < e.parent.children.length) ? e.parent.children[destinationIndex].htmlPosition.from : e.parent.childrenArea.to;
    const movedCode = '\n\n' + props.projectType.report_template.slice(e.element.htmlPosition.from, e.element.htmlPosition.to) + '\n\n';
    updateCode([
      { type: 'html', from: e.element.htmlPosition.from, deleteCount: e.element.htmlPosition.to - e.element.htmlPosition.from, add: '' },
      { type: 'html', from: destinationOffset, deleteCount: 0, add: movedCode },
    ]);
  } else if (pendingListEvents.value.length === 2 && pendingListEvents.value[0].added && pendingListEvents.value[1].removed) {
    // Element moved from one list to another
    const ea = pendingListEvents.value[0].added;
    const er = pendingListEvents.value[1].removed;
    const destinationOffset = (ea.newIndex < ea.parent.children.length) ? ea.parent.children[ea.newIndex].htmlPosition.from : ea.parent.childrenArea.to;
    const movedCode = '\n\n' + props.projectType.report_template.slice(er.element.htmlPosition.from, er.element.htmlPosition.to) + '\n\n';
    updateCode([
      { type: 'html', from: er.element.htmlPosition.from, deleteCount: er.element.htmlPosition.to - er.element.htmlPosition.from, add: '' },
      { type: 'html', from: destinationOffset, deleteCount: 0, add: movedCode }
    ]);
  } else if (pendingListEvents.value.length === 1 && pendingListEvents.value[0].added && pendingListEvents.value[0].added.element instanceof DesignerComponentBase) {
    // Predefined component added
    const component = pendingListEvents.value[0].added.element;
    const form = component.getCreateForm();
    addDialog.value = {
      component,
      form,
      event: pendingListEvents.value[0].added,
      visible: !!form,
    };
    if (!addDialog.value.visible) {
      // No form options: immediately add component
      addPredefinedComponent();
    }
  }

  // Clear event buffer
  pendingListEvents.value = [];
}

</script>

<style lang="scss" scoped>
.draggable-item {
  cursor: grab;

  &:deep(.v-list-item__prepend .v-list-item__spacer) {
    width: 0.5em;
  }
}

.draggable-component-tree {
  min-height: 50vh;
}
</style>

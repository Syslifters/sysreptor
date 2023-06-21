<template>
  <div v-intersect="onIntersect">
    <split-menu :value="20">
      <template #menu>
        <v-list dense>
          <div v-for="group in predefinedComponentGroups" :key="group.name">
            <v-subheader :key="group.name">{{ group.name }}</v-subheader>
            <draggable
              v-model="group.components"
              draggable=".draggable-item"
              :sort="false"
              :group="{name: 'predefinedDesignerCompnents', pull: 'clone', put: false}"
            >
              <v-list-item v-for="c in group.components" :key="group.name + '-' + c.type" class="draggable-item" link :ripple="false">
                <v-list-item-icon>
                  <v-icon>mdi-drag</v-icon>
                </v-list-item-icon>
                <v-list-item-content>
                  <v-list-item-title>{{ c.name }}</v-list-item-title>
                </v-list-item-content>
              </v-list-item>
            </draggable>
          </div>
        </v-list>
      </template>
      
      <template #default>
        <v-list v-if="htmlTree" dense>
          <design-layout-tree
            :value="htmlTree"
            :upload-file="uploadFile"
            :rewrite-file-url="rewriteFileUrl"
            :disabled="disabled"
            @change-list="onChangeList"
            @update="updateCode"
            @jump-to-code="$emit('jump-to-code', $event)"
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
          <template #title>{{ addDialog.component.name }}</template>
          <template #default>
            <v-card-text>
              <design-layout-component-form
                v-model="addDialog.form"
                :lang="projectType.language"
                :upload-file="uploadFile"
                :rewrite-file-url="rewriteFileUrl"
                :disabled="disabled"
              />
            </v-card-text>
            <v-card-actions>
              <v-spacer />
              <s-btn @click="addDialog.visible = false" color="secondary">Cancel</s-btn>
              <s-btn @click="addPredefinedComponent" color="primary">Add</s-btn>
            </v-card-actions>
          </template>
        </s-dialog>
      </template>
    </split-menu>
  </div>
</template>

<script>
import Draggable from 'vuedraggable';
import { sortBy } from 'lodash';
import { DesignerComponent, predefinedDesignerComponentGroups, parseToComponentTree } from '~/components/Design/designer-components';

export default {
  components: { Draggable },
  props: {
    projectType: {
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
  emits: ['update'],
  data() {
    return {
      pendingListEvents: [],
      isVisible: true,
      htmlTreeUpdatePending: true,
      htmlTree: null,
      addDialog: {
        visible: false,
        component: null,
        form: null,
        event: null,
      }
    };
  },
  computed: {
    predefinedComponentGroups() {
      return predefinedDesignerComponentGroups;
    },
  },
  watch: {
    'projectType.report_template'() {
      if (this.isVisible) {
        this.refreshHtmlTree();
      } else {
        this.htmlTreeUpdatePending = true;
      }
    },
    'projectType.report_styles'() {
      if (this.isVisible) {
        this.refreshHtmlTree();
      } else {
        this.htmlTreeUpdatePending = true;
      }
    }
  },
  methods: {
    onIntersect(event, observer, isIntersecting) {
      // Do not refresh htmlTree if this tab is not visible because its slow (e.g. when editing HTML)
      // When the tab becomes visible again
      this.isVisible = isIntersecting;
      if (this.isVisible && this.htmlTreeUpdatePending) {
        this.refreshHtmlTree();
      }
    },
    refreshHtmlTree() {
      this.htmlTree = parseToComponentTree(this.projectType.report_template, this.projectType.report_styles, this.projectType);
      this.htmlTreeUpdatePending = false;
    },
    async onChangeList(event) {
      // When moving items from different list levels, two events are fired: first add, then remove
      // We need to process them in one tick, otherwise the offsets may be incorrect.
      this.pendingListEvents.push(event);
      const lastEventState = [...this.pendingListEvents];
      await this.$nextTick();
      if (lastEventState.length !== this.pendingListEvents.length || !lastEventState.every((elem, idx) => this.pendingListEvents[idx] === elem)) {
        return;
      }

      if (this.pendingListEvents.length === 1 && this.pendingListEvents[0].moved) {
        // Element moved within the same list
        const e = this.pendingListEvents[0].moved;
        const destinationIndex = (e.newIndex <= e.oldIndex) ? e.newIndex : e.newIndex + 1;
        const destinationOffset = (destinationIndex < e.parent.children.length) ? e.parent.children[destinationIndex].htmlPosition.from : e.parent.childrenArea.to;
        const movedCode = '\n\n' + this.projectType.report_template.slice(e.element.htmlPosition.from, e.element.htmlPosition.to) + '\n\n';
        this.updateCode([
          { type: 'html', from: e.element.htmlPosition.from, deleteCount: e.element.htmlPosition.to - e.element.htmlPosition.from, add: '' },
          { type: 'html', from: destinationOffset, deleteCount: 0, add: movedCode },
        ]);
      } else if (this.pendingListEvents.length === 2 && this.pendingListEvents[0].added && this.pendingListEvents[1].removed) {
        // Element moved from one list to another
        const ea = this.pendingListEvents[0].added;
        const er = this.pendingListEvents[1].removed;
        const destinationOffset = (ea.newIndex < ea.parent.children.length) ? ea.parent.children[ea.newIndex].htmlPosition.from : ea.parent.childrenArea.to;
        const movedCode = '\n\n' + this.projectType.report_template.slice(er.element.htmlPosition.from, er.element.htmlPosition.to) + '\n\n';
        this.updateCode([
          { type: 'html', from: er.element.htmlPosition.from, deleteCount: er.element.htmlPosition.to - er.element.htmlPosition.from, add: '' },
          { type: 'html', from: destinationOffset, deleteCount: 0, add: movedCode }
        ]);
      } else if (this.pendingListEvents.length === 1 && this.pendingListEvents[0].added && this.pendingListEvents[0].added.element instanceof DesignerComponent) {
        // Predefined component added
        const component = this.pendingListEvents[0].added.element;
        const form = component.getCreateForm();
        this.addDialog = {
          component,
          form,
          event: this.pendingListEvents[0].added,
          visible: !!form,
        };
        if (!this.addDialog.visible) {
          // No form options: immediately add component
          this.addPredefinedComponent();
        }
      }

      // Clear event buffer
      this.pendingListEvents = [];
    },
    addPredefinedComponent() {
      const addedCode = this.addDialog.component.createCode(this.addDialog.form, this.htmlTree.context);
      const changes = [];
      if (addedCode.html) {
        const ea = this.addDialog.event;
        const destinationOffset = (ea.newIndex < ea.parent.children.length) ? ea.parent.children[ea.newIndex].htmlPosition.from : ea.parent.childrenArea.to;
        changes.push({ type: 'html', from: destinationOffset, deleteCount: 0, add: '\n\n' + addedCode.html + '\n\n' });
      }
      if (addedCode.css) {
        changes.push({ type: 'css', from: this.projectType.report_styles.length, deleteCount: 0, add: '\n\n' + addedCode.css })
      }
      this.updateCode(changes);

      this.addDialog.visible = false;
    },
    spliceStringChanges(original, changes) {
      let out = '';
      let lastChange = { from: 0, deleteCount: 0, add: '' };
      for (const change of sortBy(changes, 'from')) {
        out += original.slice(lastChange.from + lastChange.deleteCount, change.from);
        out += change.add;
        lastChange = change;
      }
      out += original.slice(lastChange.from + lastChange.deleteCount);
      return out;
    },
    updateCode(changes) {
      this.$emit('update', {
        html: this.spliceStringChanges(this.projectType.report_template, changes.filter(c => c.type === 'html')),
        css: this.spliceStringChanges(this.projectType.report_styles, changes.filter(c => c.type === 'css')),
        formatHtml: true,
        reloadPdf: true,
      });
    },
  }
}
</script>

<style lang="scss" scoped>
.draggable-item {
  cursor: grab;

  & .v-list-item__icon {
    margin-right: 0.5em;
  }
}

.draggable-component-tree {
  min-height: 50vh;
}
</style>

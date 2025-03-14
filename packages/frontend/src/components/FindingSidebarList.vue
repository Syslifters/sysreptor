<template>
  <draggable
    :model-value="findingGroups"
    @update:model-value="sortGroups"
    :item-key="(item: FindingGroup) => findingGroups.indexOf(item)"
    handle=".draggable-handle-group"
    :disabled="props.readonly || !sortManual"
  >
    <template #item="{ element: group }">
      <v-list class="pa-0">
        <v-list-subheader v-if="isGrouped" class="group-header" :class="{'ml-2': !sortManual}">
          <div v-if="sortManual" class="draggable-handle-group mr-2">
            <v-icon :disabled="props.readonly" icon="mdi-drag-horizontal" />
          </div>
          
          <!-- TODO: how to display empty group label? -->
          <span v-if="group.label">{{ group.label }}</span>
          <i v-else>(unnamed group)</i>

          <s-btn-icon
            @click="createFinding(group)"
            :disabled="props.readonly"
            icon="mdi-plus"
            size="small"
            variant="flat"
            color="secondary"
            density="compact"
            class="ml-2"
          />
        </v-list-subheader>

        <!-- TODO: @update:model-value="sortFindingsInGroup(group, $event)" -->
        <draggable
          :model-value="group.findings"
          :group="{name: 'findings'}"
          @change="sortFindings($event, group)"
          item-key="id"
          handle=".draggable-handle-finding"
          :disabled="props.readonly || !sortManual"
        >
          <template #item="{element: finding}">
            <div>
              <v-list-item
                :to="findingUrl(finding)"
                :value="finding.id"
                :active="props.toPrefix ? router.currentRoute.value.path.startsWith(findingUrl(finding)!) : undefined"
                :ripple="false"
                density="compact"
                :class="'finding-level-' + riskLevel(finding)"
                :data-testid="'finding-' + findingTitle(finding)"
              >
                <template #prepend v-if="sortManual">
                  <div class="draggable-handle-finding mr-2">
                    <v-icon :disabled="props.readonly" icon="mdi-drag-horizontal" />
                  </div>
                </template>
                <template #default>
                  <v-list-item-title class="text-body-2">{{ findingTitle(finding) }}</v-list-item-title>
                  <slot name="finding-subtitle" :finding="finding" />
                </template>
                <template #append v-if="$slots['finding-item-append']"><slot name="finding-item-append" :finding="finding" /></template>
              </v-list-item>
              <slot name="finding-append" :finding="finding" />
            </div>
          </template>
        </draggable>
      </v-list>
    </template>
  </draggable>
</template>

<script setup lang="ts">
import Draggable from 'vuedraggable';
import { groupFindings, type FindingGroup } from '@base/utils/project';
import { pick } from 'lodash-es';
import { ChangeSet } from '@sysreptor/markdown/editor';

const props = defineProps<{
  modelValue: PentestFinding[];
  projectType: ProjectType;
  overrideFindingOrder?: boolean;
  topLevelFields?: boolean;
  readonly?: boolean;
  toPrefix?: string;
  hideDragHandle?: boolean;
  disableGrouping?: boolean;
  collab?: CollabPropType;
}>();
const emit = defineEmits<{
  'update:modelValue': [value: PentestFinding[]];
  'create': [value?: Partial<PentestFinding>];
  'collab': [value: any];
}>();

const router = useRouter();

const sortManual = computed(() => (props.overrideFindingOrder || props.projectType.finding_ordering.length === 0) && !props.hideDragHandle);
const findingGroups = computed(() => groupFindings({
  findings: props.modelValue,
  projectType: props.projectType,
  overrideFindingOrder: props.overrideFindingOrder,
  topLevelFields: props.topLevelFields,
}));
const isGrouped = computed(() => 
  !props.disableGrouping &&
  (props.projectType.finding_grouping || []).length > 0 && 
  (findingGroups.value.length > 1 || (findingGroups.value.length === 1 && findingGroups.value[0]?.findings[0]?.label))
);

function findingUrl(finding: PentestFinding) {
  return props.toPrefix ? `${props.toPrefix}${finding.id}/` : undefined;
}

function findingTitle(finding: PentestFinding) {
  const findingData = props.topLevelFields ? (finding as PentestFinding['data']) : finding.data;
  return findingData.title;
}

function riskLevel(finding: PentestFinding) {
  return getFindingRiskLevel({ finding, projectType: props.projectType, topLevelFields: props.topLevelFields });
}

function sortGroups(groups: FindingGroup[]) {
  const value = groups.flatMap(g => g.findings)
    .map((f, idx) => ({ ...f, order: idx + 1 }));
  emit('update:modelValue', value);
}

const pendingSortEvents = ref<any[]>([]);
async function sortFindings(event: any, group: FindingGroup) {
  const groupIndex = findingGroups.value.findIndex(g => g === group);

  if (event.moved) {
    // Finding moved inside group: update order
    const findingsInGroup = [...group.findings];
    const fMoved = findingsInGroup.splice(event.moved.oldIndex, 1);
    findingsInGroup.splice(event.moved.newIndex, 0, ...fMoved);
    const value = findingGroups.value.flatMap((g, idx) => (idx === groupIndex) ? findingsInGroup : g.findings)
      .map((f, idx) => ({ ...f, order: idx + 1 }));
    emit('update:modelValue', value);
  } else {
    // Finding moved between groups: update order and group field
    event.group = group;
    event.groupIndex = groupIndex;

    // When moving items from different list levels, two events are fired: first add, then remove
    // We need to process them in one tick, to prevent multiple sort requests and inconsistent states.
    pendingSortEvents.value.push(event);
    const lastEventState = [...pendingSortEvents.value];
    await nextTick();
    if (lastEventState.length !== pendingSortEvents.value.length || !lastEventState.every((elem, idx) => pendingSortEvents.value[idx] === elem)) {
      return;
    }

    if (pendingSortEvents.value.length === 2 && pendingSortEvents.value[0].added && pendingSortEvents.value[1].removed) {
      const eventAdded = pendingSortEvents.value[0];
      const eventRemoved = pendingSortEvents.value[1];

      const findingsGroupRemoved = [...eventRemoved.group.findings];
      const fMoved = findingsGroupRemoved.splice(eventRemoved.removed.oldIndex, 1)[0] as PentestFinding|undefined;
      if (!fMoved) {
        return;
      }
      const findingsGroupAdded = [...eventAdded.group.findings];
      findingsGroupAdded.splice(eventAdded.added.newIndex, 0, fMoved);

      const groupFieldName = props.projectType.finding_grouping![0]!.field;
      const groupFieldValue = props.topLevelFields ? eventAdded.group.findings[0]![groupFieldName] : eventAdded.group.findings[0]!.data[groupFieldName];

      const value = findingGroups.value.flatMap((g, idx) => 
          (idx === eventRemoved.groupIndex) ? findingsGroupRemoved : 
          (idx === eventAdded.groupIndex) ? findingsGroupAdded : 
          g.findings
      ).map((f, idx) => ({ 
          ...f, 
          ...(props.topLevelFields ? {[groupFieldName]: groupFieldValue} : {data: { ...f.data, [groupFieldName]: groupFieldValue }}),
          order: idx + 1,
        }));
      emit('update:modelValue', value);
      
      // Update group field via collab
      const d = props.projectType.finding_fields.find(d => d.id === groupFieldName);
      if (props.collab && d) {
        emit('collab', {
          type: CollabEventType.UPDATE_KEY,
          path: collabSubpath(props.collab, `findings.${fMoved.id}.data.${groupFieldName}`).path,
          value: groupFieldValue,
          updateAwareness: false,
        })
      }
    }
  }

  // Clear event buffer
  pendingSortEvents.value = [];
}

function createFinding(group?: FindingGroup) {
  const finding = group?.findings.at(-1);
  const groupFieldName = props.projectType.finding_grouping![0]!.field;
  const findingData = finding ? {
    ...(props.topLevelFields ? pick(finding, [groupFieldName]) : {data: pick(finding.data, [groupFieldName])}),
    order: finding.order + 1,
  } : undefined;
  emit('create', findingData);
}

</script>

<!-- TODO:
* [x] group findings if defined in projectType
* [x] flat list or list of groups 
* [x] @sort => update finding.order
* [x] @create => open CreateFindingDialog + set group value
* [ ] use in reporting.vue + slots
* [ ] use in DesignPreviewDataForm.vue + slots
-->

<style lang="scss" scoped>
@use 'sass:map';
@use "@base/assets/settings" as settings;

@for $level from 1 through 5 {
  .finding-level-#{$level} {
    border-left: 0.4em solid map.get(settings.$risk-color-levels, $level);
  }
}

.group-header {
  margin-top: 0 !important;

  :deep(.v-list-subheader__text) {
    display: flex;
    flex-direction: row;
    width: 100%;
  }
}

.draggable-handle-finding, .draggable-handle-group {
  cursor: grab;

  &:deep(.v-icon) {
    cursor: inherit;
  }
}
</style>

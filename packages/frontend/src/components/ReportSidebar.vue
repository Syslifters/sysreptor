<template>
  <v-list 
    select-strategy="single-leaf"
    density="compact" 
    class="pb-0 pt-0 h-100 d-flex flex-column"
  >
    <v-list-subheader v-if="isInSearchMode" class="subheader-section pr-2">
      <s-text-field 
        v-model="search"
        placeholder="Search..."
        density="compact"
        variant="underlined"
        prepend-inner-icon="mdi-magnify"
        append-inner-icon="$clear"
        @click:append-inner="hideSearch"
        autofocus
        autocomplete="off"
        spellcheck="false"
      >
        <template #prepend-inner-icon>
          <v-icon icon="mdi-magnify" size="small" />
        </template>
        <template #append-inner-icon>
          <v-icon icon="mdi-close" size="small" />
        </template>
      </s-text-field>
    </v-list-subheader>

    <div v-if="!showSearchResults" class="flex-grow-1 overflow-y-auto">
      <v-list-subheader class="subheader-section pr-2">
        <span>Sections</span>
        <v-spacer />
        <s-btn-icon
          v-if="!isInSearchMode && search !== undefined"
          @click="showSearch"
          icon="mdi-magnify"
          size="small"
          density="compact"
          class="ml-2"
        />
        <s-btn-icon
          :disabled="props.readonly"
          size="small"
          density="compact"
          class="ml-2"
        >
          <v-icon icon="mdi-dots-vertical" />
          <v-menu activator="parent" eager :close-on-content-click="false" location="bottom right">
            <v-list>
              <v-list-item
                v-if="props.collab"
                title="Set status"
                prepend-icon="mdi-pencil"
                :disabled="props.readonly || (selectedFindings.length === 0 || selectedSections.length === 0)"
              >
                <v-menu activator="parent" submenu>
                  <v-list>
                    <v-list-item
                      v-for="status in statusItems"
                      :key="`status-${status.id}`"
                      @click="setStatusOfSelectedItems(status.id)"
                      :disabled="props.readonly || (selectedFindings.length === 0 || selectedSections.length === 0) || status.props?.disabled"
                    >
                      <template #prepend>
                        <v-icon :icon="status.icon || 'mdi-help'" :class="'status-' + status.id" />
                      </template>
                      <v-list-item-title>{{ status.label }}</v-list-item-title>
                    </v-list-item>
                  </v-list>
                </v-menu>
              </v-list-item>
              <btn-delete
                :delete="deleteSelectedFindings"
                :disabled="props.readonly || selectedFindings.length === 0"
                button-variant="list-item"
              >
                <template #dialog-text>
                  <p class="mt-0">
                      Do you really want to delete {{ selectedFindings.length }} findings?
                  </p>
                  <ul class="mt-0">
                    <li v-for="f in selectedFindings" :key="f.id">
                      {{ f.data.title }}
                    </li>
                  </ul>
                </template>
              </btn-delete>
            </v-list>
          </v-menu>
        </s-btn-icon>
      </v-list-subheader>
      <v-list-item
        v-for="section in sections"
        :key="section.id"
        :value="section.id"
        :to="sectionUrl(section)"
        :active="section.id === currentPageId"
        density="compact"
        :class="{ 'list-item--selected': selectedIds.has(section.id) }"
        @click="onClickListItem($event, section)"
      >
        <template #default>
          <v-list-item-title class="text-body-medium">{{ section.label }}</v-list-item-title>
          <v-list-item-subtitle>
            <span v-if="section.assignee">@{{ section.assignee.username }}</span>
          </v-list-item-subtitle>
        </template>
        <template #append>
          <slot name="section-item-append" :section="section">
            <collab-avatar-group 
              :collab="collabSubpathProps[`sections.${section.id}`]"
              :class="{'mr-2': section.status && section.status !== ReviewStatus.IN_PROGRESS}"
            />
            <s-status-info :value="section.status" />
          </slot>
        </template>
      </v-list-item>

      <v-list-subheader>
        <span>Findings</span>
        <s-btn-icon
          v-if="!isGrouped"
          @click="emit('create:finding')"
          :disabled="props.readonly"
          size="small"
          variant="flat"
          color="secondary"
          density="compact"
          class="ml-2"
        >
          <v-icon icon="mdi-plus" />
          <s-tooltip activator="parent" location="top">Add Finding (Ctrl+J)</s-tooltip>
        </s-btn-icon>
        <v-spacer />
        <s-btn-icon
          v-if="overrideFindingOrder !== undefined && projectType.finding_ordering.length > 0"
          @click="overrideFindingOrder = !overrideFindingOrder"
          :disabled="props.readonly"
          size="small"
          density="compact"
        >
          <v-icon :icon="overrideFindingOrder ? 'mdi-sort-variant-off' : 'mdi-sort-variant'" />
          <s-tooltip activator="parent" location="top">
            <span v-if="overrideFindingOrder">Custom order</span>
            <span v-else>Default order</span>
          </s-tooltip>
        </s-btn-icon>
      </v-list-subheader>

      <draggable
        :model-value="findingGroups"
        @update:model-value="sortGroups"
        :item-key="(item: FindingGroup) => findingGroups.indexOf(item)"
        handle=".draggable-handle-group"
        :disabled="props.readonly || !sortManual"
      >
        <template #item="{ element: group }">
          <div>
            <v-list-subheader v-if="isGrouped" class="group-header" :class="{'ml-2': !sortManual}">
              <div v-if="sortManual" class="draggable-handle-group mr-2">
                <v-icon :disabled="props.readonly" icon="mdi-drag-horizontal" />
              </div>
              
              <span v-if="group.label">{{ group.label }}</span>
              <span class="font-italic" v-else>(unnamed group)</span>

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

            <draggable
              :model-value="group.findings"
              :group="{name: 'findings'}"
              @change="sortFindings($event, group)"
              item-key="id"
              handle=".draggable-handle-finding"
              :disabled="props.readonly || !sortManual"
            >
              <template #item="{element: finding}">
                <v-list-item
                  :to="findingUrl(finding)"
                  :value="finding.id"
                  :active="finding.id === currentPageId"
                  :ripple="false"
                  density="compact"
                  :class="[
                    `finding-level-${riskLevel(finding)}`,
                    `finding-retest-${findingRetestStatus(finding)?.value}`,
                    { 'list-item--selected': selectedIds.has(finding.id) }
                  ]"
                  :data-testid="'finding-' + findingTitle(finding)"
                  @click="onClickListItem($event, finding)"
                >
                  <template #prepend v-if="sortManual">
                    <div class="draggable-handle-finding mr-2">
                      <v-icon :disabled="props.readonly" icon="mdi-drag-horizontal" />
                    </div>
                  </template>
                  <template #default>
                    <v-list-item-title class="text-body-medium">{{ findingTitle(finding) }}</v-list-item-title>
                    <v-list-item-subtitle v-if="finding.assignee">@{{ finding.assignee.username }}</v-list-item-subtitle>
                    <s-tooltip v-if="['resolved', 'accepted', 'partial'].includes(findingRetestStatus(finding)?.value || '')" activator="parent">
                      Retest status: {{ findingRetestStatus(finding)?.label }}
                    </s-tooltip>
                  </template>
                  <template #append>
                    <slot name="finding-item-append" :finding="finding" >
                      <collab-avatar-group
                        :collab="collabSubpathProps[`findings.${finding.id}`]"
                        :class="{'mr-2': finding.status !== ReviewStatus.IN_PROGRESS}"
                      />
                      <s-status-info :value="finding.status" />
                    </slot>
                  </template>
                </v-list-item>
              </template>
            </draggable>
          </div>
        </template>
      </draggable>
    </div>

    <div v-else>
      <!-- Search result list -->
      <template v-if="searchResultsSections.length > 0">
        <v-list-subheader title="Sections" class="mt-0 pr-2" />
        <div v-for="result in searchResultsSections" :key="result.item.id">
          <v-list-item
            :to="sectionUrl(result.item)"
            :active="result.item.id === currentPageId"
            density="compact"
          >
            <template #default>
              <v-list-item-title class="text-body-medium">{{ result.item.label }}</v-list-item-title>
            </template>
          </v-list-item>
          <search-match-list 
            :result="result"
            :to-prefix="sectionUrl(result.item)"
            class="match-list"
          />
        </div>
      </template>

      <template v-if="searchResultsFindings.length > 0">
        <v-list-subheader title="Findings" />
        <div v-for="result in searchResultsFindings" :key="result.item.id">
          <v-list-item
            :to="findingUrl(result.item)"
            :active="result.item.id === currentPageId"
            :class="'finding-level-' + riskLevel(result.item)"
            density="compact"
          >
            <v-list-item-title class="text-body-medium">{{ findingTitle(result.item) }}</v-list-item-title>
          </v-list-item>
          <search-match-list 
            :result="result"
            :to-prefix="findingUrl(result.item)"
            class="match-list"
          />
        </div>
      </template>
    </div>
    
    <div v-if="!isInSearchMode">
      <v-divider class="mb-1" />
      <v-list-item>
        <btn-confirm
          :action="createFinding"
          :confirm="false"
          :disabled="props.readonly"
          data-testid="create-finding-button"
          button-text="Add"
          button-icon="mdi-plus"
          tooltip-text="Add Finding (Ctrl+J)"
          keyboard-shortcut="ctrl+j"
          color="secondary"
          size="small"
          block
        />
      </v-list-item>
    </div>
  </v-list>
</template>

<script setup lang="ts">
import { orderBy, pick, uniq } from 'lodash-es';
import Draggable from 'vuedraggable';
import { groupFindings, type FindingGroup } from '@base/utils/project';

const search = defineModel<string|null|undefined>('search', { default: undefined });
const overrideFindingOrder = defineModel<boolean|undefined>('overrideFindingOrder', { default: undefined });
const selected = defineModel<string|null>('selected');
const props = defineProps<{
  sections: ReportSection[];
  findings: PentestFinding[];
  projectType: ProjectType;
  readonly?: boolean;
  toPrefix?: string;
  collab?: CollabPropType;
}>();
const emit = defineEmits<{
  'update:findings': [value: PentestFinding[]];
  'create:finding': [value?: Partial<PentestFinding>|null];
  'delete:findings': [value: PentestFinding[]];
  'collab': [value: any];
}>();

const router = useRouter();
const auth = useAuth();
const apiSettings = useApiSettings();

function sectionUrl(section: ReportSection, trailingSlash = true) {
  return props.toPrefix ? `${props.toPrefix}sections/${section.id}${trailingSlash ? '/' : ''}` : undefined;
}
function findingUrl(finding: PentestFinding, trailingSlash = true) {
  return props.toPrefix ? `${props.toPrefix}findings/${finding.id}${trailingSlash ? '/' : ''}` : undefined;
}
function findingTitle(finding: PentestFinding) {
  return finding.data.title;
}
function riskLevel(finding: PentestFinding) {
  return getFindingRiskLevel({ finding, projectType: props.projectType });
}
function findingRetestStatus(finding: PentestFinding) {
  const d = props.projectType.finding_fields.find(f => f.id === 'retest_status' && f.type === FieldDataType.ENUM);
  return d?.choices?.find(c => c.value === finding.data.retest_status) || null;
}

function createFinding(group?: FindingGroup) {
  if (props.readonly) {
    return;
  }

  const finding = group?.findings.at(-1);
  const groupFieldName = props.projectType.finding_grouping?.[0]?.field;
  const findingData = (finding && groupFieldName) ? {
    data: pick(finding.data, [groupFieldName]),
    order: finding.order + 1,
  } : undefined;
  emit('create:finding', findingData);
}

const sections = computed(() => orderBy(props.sections, [s => props.projectType.report_sections.findIndex(rs => rs.id === s.id)]));

// Grouping and sorting
const sortManual = computed(() => overrideFindingOrder.value || props.projectType.finding_ordering.length === 0);
const findingGroups = computedList<FindingGroup>(() => groupFindings({
  findings: props.findings,
  projectType: props.projectType,
  overrideFindingOrder: overrideFindingOrder.value,
}), g => ({...g, findings: g.findings.map(f => f.id)}));
const isGrouped = computed(() => 
  (props.projectType.finding_grouping || []).length > 0 && 
  (findingGroups.value.length > 1 || (findingGroups.value.length === 1 && findingGroups.value[0]?.label))
);

const subpathNames = computedCached(() => props.findings.map(f => `findings.${f.id}`).concat(props.sections.map(s => `sections.${s.id}`)));
const collabSubpathProps = useCollabSubpaths(() => props.collab, subpathNames);

function sortGroups(groups: FindingGroup[]) {
  const value = groups.flatMap(g => g.findings)
    .map((f, idx) => ({ ...f, order: idx + 1 }));
  emit('update:findings', value);
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
    emit('update:findings', value);
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
      const groupFieldValue = eventAdded.group.findings[0]!.data[groupFieldName];

      const value = findingGroups.value.flatMap((g, idx) => 
          (idx === eventRemoved.groupIndex) ? findingsGroupRemoved : 
          (idx === eventAdded.groupIndex) ? findingsGroupAdded : 
          g.findings
      ).map((f, idx) => ({ 
          ...f, 
          data: f.id === fMoved.id ? { ...f.data, [groupFieldName]: groupFieldValue } : f.data,
          order: idx + 1,
        }));
      emit('update:findings', value);
      
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


// Search
const isInSearchMode = computed(() => search.value !== undefined && search.value !== null);
const showSearchResults = computed(() => isInSearchMode.value && (search.value || '').length >= 3)
const searchResultsSections = computed(() => searchSections(props.sections, props.projectType, search.value));
const searchResultsFindings = computed(() => searchFindings(props.findings, props.projectType, search.value));
function showSearch() {
  search.value = '';
}
function hideSearch() {
  search.value = null;
}
useKeyboardShortcut('ctrl+shift+f', () => showSearch());


// Selection
const currentPageId = computed(() => 
  selected.value ?? 
  router.currentRoute.value.params.sectionId as string|undefined ?? 
  router.currentRoute.value.params.findingId as string|undefined ?? 
  null);
const selectedIds = ref<Set<string>>(new Set());
const selectedSections = computed(() => sections.value.filter(s => selectedIds.value.has(s.id)));
const selectedFindings = computed(() => props.findings.filter(f => selectedIds.value.has(f.id)));

const lastSelectedId = ref<string|null>(null);
watch(currentPageId, () => {
  // On navigate: reset selection
  selectedIds.value.clear();
  if (currentPageId.value) {
    selectedIds.value.add(currentPageId.value);
  }
  lastSelectedId.value = currentPageId.value;
}, { immediate: true });

function selectItem(item: ReportSection|PentestFinding, value: boolean = true) {
  const itemId = item.id;
  if (value) {
    selectedIds.value.add(itemId);
  } else {
    selectedIds.value.delete(itemId);
  }
}
function onClickListItem(event: MouseEvent|KeyboardEvent, item: ReportSection|PentestFinding) {
  if (event.shiftKey) {
    // Select all items between the last selected item and the current one.
    const itemsFlat = sections.value.concat(findingGroups.value.flatMap(g => g.findings));
    const idxSelectionStart = itemsFlat.findIndex(i => i.id === lastSelectedId.value);
    const idxSelectionEnd = itemsFlat.findIndex(i => i.id === item.id);
    if (idxSelectionStart === -1 || idxSelectionEnd === -1) {
      selectItem(item, true);
    } else {
      itemsFlat.slice(Math.min(idxSelectionStart, idxSelectionEnd), Math.max(idxSelectionStart, idxSelectionEnd) + 1).forEach(i => {
        selectItem(i, true);
      });
    }
    event.preventDefault();
  } else if (event.ctrlKey) {
    selectItem(item, !selectedIds.value.has(item.id) || currentPageId.value === item.id);
    lastSelectedId.value = item.id;
    event.preventDefault();
  } else if (selected.value !== undefined) {
    selected.value = item.id;
  }
}

const statusItems = computed(() => {
  const currentStatuses = uniq(selectedFindings.value.map(f => f.status).concat(selectedSections.value.map(s => s.status)))
    .map(s => apiSettings.getStatusDefinition(s));
  return (apiSettings.settings?.statuses || []).map(s => ({
    ...s,
    props: {
      // Disable status when the status transition is not allowed for any selected item
      disabled: !currentStatuses.every(cs => 
        (cs.allowed_next_statuses?.length || 0) === 0 || 
        cs.allowed_next_statuses?.includes(s.id) || 
        auth.permissions.value.admin),
    },
  }));
});
function setStatusOfSelectedItems(status: string) {
  if (props.readonly || !props.collab) {
    return;
  }
  for (const s of selectedSections.value) {
    emit('collab', {
      type: CollabEventType.UPDATE_KEY,
      path: collabSubpath(props.collab, `sections.${s.id}.status`).path,
      value: status,
      updateAwareness: false,
    });
  }
  for (const f of selectedFindings.value) {
    emit('collab', {
      type: CollabEventType.UPDATE_KEY,
      path: collabSubpath(props.collab, `findings.${f.id}.status`).path,
      value: status,
      updateAwareness: false,
    });
  }
}
function deleteSelectedFindings() {
  if (props.readonly || selectedFindings.value.length === 0) {
    return;
  }
  emit('delete:findings', selectedFindings.value);
}
</script>

<style lang="scss" scoped>
@use 'sass:map';
@use "@base/assets/settings" as settings;

@for $level from 1 through 5 {
  .finding-level-#{$level} {
    border-left: 0.4em solid map.get(settings.$risk-color-levels, $level);
  }
}

.status-finished {
  color: settings.$status-color-finished;
}
.status-deprecated {
  color: settings.$status-color-deprecated;
}

.finding-retest-resolved, .finding-retest-accepted, .finding-retest-partial {
  &:not(.v-list-item--active) > :deep(.v-list-item__overlay)  {
    opacity: 0.1;
  }
  &.v-list-item--active > :deep(.v-list-item__overlay)  {
    opacity: 0.2;
  }
}
.finding-retest-resolved, .finding-retest-accepted {
  &:deep(.v-list-item__overlay) {
    background-color: rgb(var(--v-theme-success));
  }
}
.finding-retest-partial:deep(.v-list-item__overlay) {
  background-color: rgb(var(--v-theme-warning));
}

:deep(.v-list-item-subtitle) {
  font-size: x-small;
}

.subheader-section {
  margin-top: 0 !important;
}

:deep(.v-list-subheader) {
  margin-top: 1em;
  padding-left: 0.5em;

  .v-list-subheader__text {
    display: flex;
    flex-direction: row;
    width: 100%;
  }
}

.match-list {
  padding-left: 0.75rem;
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

.list-item--selected {
  background: color-mix(in srgb, rgb(var(--v-theme-on-surface)) calc((var(--v-activated-opacity)) * 100%), transparent);
}
</style>

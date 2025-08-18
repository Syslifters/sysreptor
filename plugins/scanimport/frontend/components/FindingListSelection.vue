<template>
  <v-list 
    :selected="selectedFindingIdsModel"
    select-strategy="leaf"
    density="compact"
  >
    <v-list-item 
      v-for="finding in props.findings"
      :title="finding.data.title"
      :value="finding.id"
      @click="onClickFinding($event, finding)"
      density="compact"
      :class="'finding-level-' + riskLevel(finding)"
    >
      <template v-slot:prepend="{ isSelected }">
        <v-list-item-action start>
          <v-checkbox-btn 
            :model-value="isSelected" 
            density="compact"  
          />
        </v-list-item-action>
      </template>
    </v-list-item>
  </v-list>
</template>

<script setup lang="ts">
import { isEqual } from 'lodash-es';
import { scoreFromVector, levelNumberFromLevelName, levelNumberFromScore } from "@base/utils/cvss";

const props = defineProps<{
  findings: PentestFinding[];
}>();

const selectedFindingIdsModel = defineModel<string[]>('selectedFindingIds', { default: [] });
const selectedIds = ref<string[]>(selectedFindingIdsModel);
watch(selectedFindingIdsModel, (newValue) => {
  if (!isEqual(newValue, selectedIds.value)) {
    selectedIds.value = [...(newValue || [])];
  }
}, { immediate: true });
watch(selectedIds, (newValue) => {
  if (!isEqual(newValue, selectedFindingIdsModel.value)) {
    selectedFindingIdsModel.value = [...newValue]; 
  }
}, { deep: 1 });

const lastSelectedId = ref<string|null>(null);

function riskLevel(finding: PentestFinding) {
  const cvss = finding.data.cvss;
  const severity = finding.data.severity;
  if (severity) {
    return levelNumberFromLevelName(severity);
  } else if (cvss && cvss !== 'n/a') {
    return levelNumberFromScore(scoreFromVector(cvss));
  } else {
    return 1;
  }
}

function selectFinding(finding: PentestFinding, value: boolean = true) {
  if (value && !selectedIds.value.includes(finding.id)) {
    selectedIds.value = selectedIds.value.concat([finding.id]);
  } else if (!value && selectedIds.value.includes(finding.id)) {
    selectedIds.value = selectedIds.value.filter(id => id !== finding.id);
  }
}

function onClickFinding(event: MouseEvent|KeyboardEvent, finding: PentestFinding) {
  console.log('onClickFinding', event, finding, lastSelectedId.value);
  if (event.shiftKey) {
    // Select all findings between the last selected finding and the current one.
    const idxSelectionStart = props.findings.findIndex(f => f.id === (lastSelectedId.value || props.findings[0]?.value));
    const idxSelectionEnd = props.findings.findIndex(f => f.id === finding.id);

    if (idxSelectionStart === -1 || idxSelectionEnd === -1) {
      selectFinding(finding);
    } else {
      const findingsToSelect = props.findings
        .slice(Math.min(idxSelectionStart, idxSelectionEnd), Math.max(idxSelectionStart, idxSelectionEnd) + 1);
      const allSelected = findingsToSelect.every(f => selectedIds.value.includes(f.id));
      
      // Batch update: accumulate all changes first, then apply in single update
      let newSelectedIds = [...selectedIds.value];
      findingsToSelect.forEach(f => {
        if (!allSelected && !newSelectedIds.includes(f.id)) {
          newSelectedIds.push(f.id);
        } else if (allSelected && newSelectedIds.includes(f.id)) {
          newSelectedIds = newSelectedIds.filter(id => id !== f.id);
        }
      });
      selectedIds.value = newSelectedIds;
    }

    lastSelectedId.value = finding.id;
    event.preventDefault();
  } else {
    selectFinding(finding, !selectedIds.value.includes(finding.id));
    lastSelectedId.value = finding.id;
    event.preventDefault();
  }
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
</style>

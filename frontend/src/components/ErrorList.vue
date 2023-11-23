<template>
  <div class="pa-4">
    <v-expansion-panels v-if="group" multiple>
      <v-expansion-panel v-if="props.showNoMessageInfo && messageGroups.length === 0" class="error-group" readonly>
        <v-expansion-panel-title hide-actions>
          <div class="error-header text-body-1">
            <v-icon color="green" start icon="mdi-checkbox-marked" />
            All clear! Your report is ready for download.
          </div>
        </v-expansion-panel-title>
      </v-expansion-panel>

      <v-expansion-panel v-for="(msgGroup, groupIdx) in messageGroups" :key="'group-' + groupIdx" class="error-group">
        <v-expansion-panel-title>
          <div class="error-header text-body-1">
            <v-chip class="mr-2 flex-shrink-0" :class="'bg-' + msgGroup.level" size="small" label>{{ msgGroup.level.toUpperCase() }}</v-chip>
            {{ msgGroup.message }}
            <v-spacer />
            <span class="mr-2">&times;{{ msgGroup.entries.length }}</span>
          </div>
        </v-expansion-panel-title>

        <v-expansion-panel-text class="pl-8">
          <div v-for="(msg, entryIdx) in msgGroup.entries" :key="'group-' + groupIdx + '-' + entryIdx" class="mb-2">
            {{ msg.message }}
            <span v-if="msg.location" class="error-location">
              <slot name="location" :msg="msg">
                in {{ msg.location.type }}
                <span v-if="msg.location.name">"{{ msg.location.name }}"</span>
                <span v-if="msg.location.path">field {{ msg.location.path }}</span>
              </slot>
            </span>

            <pre v-if="msg.details" class="error-details ml-4">{{ msg.details }}</pre>
            <v-divider />
          </div>
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>

    <div v-else>
      <div v-if="showNoMessageInfo && messageList.length === 0" class="error-group">
        <div class="error-header text-body-1">
          <v-icon color="green" start icon="mdi-checkbox-marked" />
          Everything looks fine. There are no errors or warnings.
        </div>
      </div>

      <div v-for="(msg, idx) in messageList" :key="'list' + idx" class="mb-4">
        <div class="error-header">
          <v-chip class="ma-2 mt-0 flex-shrink-0" :class="'bg-' + msg.level" size="small" label>{{ msg.level.toUpperCase() }}</v-chip>
          <p class="error-message">
            <slot name="message" :msg="msg">
              {{ msg.message }}
              <span v-if="msg.location && msg.location.name" class="error-location">
                in {{ msg.location.type }}
                <span v-if="msg.location.name">"{{ msg.location.name }}"</span>
                <span v-if="msg.location.path"> field {{ msg.location.path }}</span>
              </span>
            </slot>
          </p>
        </div>

        <pre v-if="msg.details" class="error-details ml-4">{{ msg.details }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import sortBy from "lodash/sortBy";
import groupBy from "lodash/groupBy";
import type { MessageLevel as MessageLevelType } from '~/utils/types';

const props = defineProps<{
  value: ErrorMessage[];
  group?: boolean;
  showNoMessageInfo?: boolean;
}>();

function levelToNumber(level: MessageLevelType) {
  const out = [MessageLevel.ERROR, MessageLevel.WARNING, MessageLevel.INFO, MessageLevel.DEBUG].indexOf(level as any);
  if (out < 0) {
    return 9;
  }
  return out;
}
const messageList = computed(() => sortBy(props.value, [m => levelToNumber(m.level), 'message']))
const messageGroups = computed(() => {
  // Group by level and message text
  const grouped = groupBy(messageList.value, m => [m.level, m.message]);
  const formattedGroups = Object.values(grouped)
    .map(msgs => ({
      level: msgs[0].level,
      message: msgs[0].message,
      entries: msgs
    }));
  return sortBy(formattedGroups, [g => levelToNumber(g.level), 'message']);
});

</script>

<style lang="scss" scoped>
.error-header {
  margin-bottom: 0;
  display: flex;
}
.error-message {
  display: inline-block;
  flex-grow: 1;
  margin-bottom: 0;
}
.error-location {
  font-size: smaller;
}
.error-details {
  font-size: small;
  white-space: pre-wrap;
}

.error-group {
  background-color: inherit !important;
}
</style>

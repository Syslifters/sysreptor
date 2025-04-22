<template>
  <s-user-selection
    v-if="lgAndUp"
    v-model="modelValue"
    label="Assignee"
    prepend-inner-icon="mdi-account"
    variant="underlined"
    density="compact"
    class="assignee-lg"
    v-bind="{...props, ...$attrs}"
  />
  <s-btn-icon
    v-else
    class="assignee-sm"
    v-bind="$attrs"
  >
    <user-avatar v-if="modelValue" :user="modelValue" />
    <v-icon v-else icon="mdi-account" />

    <v-menu activator="parent" :disabled="props.readonly || props.disabled">
      <v-list
        :selected="modelValue ? [modelValue] : []"
        @update:selected="modelValue = $event.length > 0 ? $event[0]! : null"
      >
        <v-list-item
          v-for="user in props.selectableUsers"
          :key="user.id"
          :value="user"
          :title="formatUsername(user)"
        >
          <template #prepend>
            <user-avatar :user="user" />
          </template>
        </v-list-item>
        <v-list-item
          @click="modelValue = null"
          prepend-icon="mdi-account"
          title="unassigned"
          link
        />
      </v-list>
    </v-menu>
  </s-btn-icon>
</template>

<script setup lang="ts">
const modelValue = defineModel<UserShortInfo|null>({ required: true });
const props = defineProps<{
  selectableUsers: UserShortInfo[];
  readonly?: boolean;
  disabled?: boolean;
}>()

const { lgAndUp } = useDisplay();

function formatUsername(u: UserShortInfo) {
  return (u.username && u.name) ? `${u.username} (${u.name})` : (u.username || u.name || 'Unknown User')
}
</script>

<style lang="scss" scoped>
.assignee-lg {
  max-width: 17em;
}
.assignee-sm {
  text-transform: initial;
}

.v-list-item:deep(.v-list-item__prepend .v-list-item__spacer) {
  width: 0.5em;
}

.assignee-container-sm:deep() {
  max-width: 2em;
  max-height: var(--v-btn-height);
  
  // Hide text field components and only show the icon
  .v-field__field, .v-field__clearable, .v-field__outline, .v-field__overlay, .v-field__loader, .v-field__append-inner {
    display: none;
  }
  
  // Ensure the icon is always visible
  .v-input__prepend {
    margin-right: 0;
    padding-right: 0;
  }
  
  // Make component more compact on small screens
  .v-input {
    width: auto;
    min-width: auto;
    padding: 0;
  }
}
</style>

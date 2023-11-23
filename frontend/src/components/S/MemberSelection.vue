<template>
  <s-user-selection
    :model-value="modelValue"
    @update:model-value="updateMembers"
    label="Members"
    :multiple="true"
    :disabled="disabled || disableAdd"
    :prevent-unselecting-self="preventUnselectingSelf"
    menu-icon=""
    :clearable="false"
  >
    <template #chip="{item: { title, raw: user}}">
      <v-list-item
        :disabled="props.disabled"
        class="member-item elevation-2 mt-1 mb-1"
        lines="two"
        density="compact"
      >
        <v-list-item-title>{{ title }}</v-list-item-title>

        <s-member-role-selection
          :model-value="getRoles(user)"
          @update:model-value="setRoles(user, $event)"
          :items="allRoles"
          :disabled="props.disabled"
        />

        <template #append>
          <s-btn
            @click.stop="removeMember(user)"
            :disabled="disabled || (preventUnselectingSelf && user.id === auth.user.value!.id)"
            icon="mdi-delete"
            variant="text"
          />
        </template>
      </v-list-item>
    </template>

    <template #append-inner>
      <s-btn
        :disabled="disabled || disableAdd"
        size="small"
        color="secondary"
        prepend-icon="mdi-plus"
        text="Add"
      />
    </template>
  </s-user-selection>
</template>

<script setup lang="ts">
import cloneDeep from "lodash/cloneDeep";
import uniq from "lodash/uniq";

const props = withDefaults(defineProps<{
  modelValue: ProjectMember[],
  disabled?: boolean,
  disableAdd?: boolean,
  preventUnselectingSelf?: boolean,
}>(), {});
const emit = defineEmits<{
  (e: 'update:modelValue', value: ProjectMember[]): void,
}>();

const auth = useAuth();
const apiSettings = useApiSettings();

const rolesCache = ref(Object.fromEntries(props.modelValue.filter(m => Array.isArray(m.roles)).map(m => [m.id, m.roles])));
const allRoles = computed(() =>
  uniq(apiSettings.settings!.project_member_roles.map(r => r.role)
    .concat(Object.values(rolesCache.value).flat()))
)
const defaultRoles = computed(() => apiSettings.settings!.project_member_roles.filter(r => r.default).map(r => r.role));

function updateMembers(members: ProjectMember[]) {
  members = cloneDeep(members);
  for (const m of members) {
    if (!Array.isArray(m.roles)) {
      m.roles = rolesCache.value[m.id] || defaultRoles.value;
      rolesCache.value[m.id] = m.roles;
    }
  }
  emit('update:modelValue', members);
}
function removeMember(member: ProjectMember) {
  emit('update:modelValue', props.modelValue.filter(m => m.id !== member.id));
}
function getRoles(user: ProjectMember|null) {
  return cloneDeep(props.modelValue.find(m => m.id === user?.id)?.roles || []);
}
function setRoles(user: ProjectMember, roles: string[]) {
  emit('update:modelValue', props.modelValue.map((m) => {
    if (m.id === user.id) {
      m = { ...m, roles };
      rolesCache.value[m.id] = m.roles;
    }
    return m;
  }));
}
</script>

<style lang="scss" scoped>
// Always show text input line at end of user-selection
.v-autocomplete :deep() {
  & > .v-input__control > .v-field > .v-field__field > .v-field__input {
    display: flex;
    flex-direction: column;
    row-gap: 0;
    padding-bottom: calc(var(--v-field-input-padding-bottom) / 2);

    .member-item {
      width: 100%;
      min-width: 64px !important;
      max-height: inherit !important;
    }

    .v-autocomplete__selection {
      width: 100%;
      height: auto;
    }

    input {
      width: 100%;
      height: 0;
    }
  }
}
</style>

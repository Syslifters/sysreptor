<template>
  <s-user-selection
    :model-value="modelValue"
    @update:model-value="updateMembers"
    label="Members"
    :multiple="true"
    :disabled="props.disabled"
    :readonly="props.readonly || disableAdd"
    :prevent-unselecting-self="preventUnselectingSelf"
    menu-icon=""
    :clearable="false"
  >
    <template #chip="{item: { title, raw: user}}">
      <v-list-item
        class="member-item elevation-2 mt-1 mb-1"
        lines="two"
        density="compact"
      >
        <template #prepend>
          <user-avatar :user="user" size="default" />
        </template>
        <v-list-item-title>{{ title }}</v-list-item-title>

        <s-member-role-selection
          :model-value="getRoles(user)"
          @update:model-value="setRoles(user, $event)"
          :items="allRoles"
          :readonly="props.readonly"
        />

        <template #append>
          <s-btn-icon
            @click.stop="removeMember(user)"
            :disabled="props.readonly || preventUnselectingSelf && user.id === auth.user.value!.id"
            icon="mdi-delete"
          />
        </template>
      </v-list-item>
    </template>

    <template #append-inner>
      <s-btn-secondary
        size="small"
        prepend-icon="mdi-plus"
        text="Add"
        :disabled="props.readonly || disableAdd"
      />
    </template>
  </s-user-selection>
</template>

<script setup lang="ts">
import { cloneDeep, uniq } from "lodash-es";

const modelValue = defineModel<ProjectMember[]>({ required: true });
const props = withDefaults(defineProps<{
  disabled?: boolean,
  readonly?: boolean,
  disableAdd?: boolean,
  preventUnselectingSelf?: boolean,
}>(), {});

const auth = useAuth();
const apiSettings = useApiSettings();

const rolesCache = ref(Object.fromEntries(modelValue.value.filter(m => Array.isArray(m.roles)).map(m => [m.id, m.roles])));
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
  modelValue.value = members;
}
function removeMember(member: ProjectMember) {
  modelValue.value = modelValue.value.filter(m => m.id !== member.id);
}
function getRoles(user: ProjectMember|null) {
  return cloneDeep(modelValue.value.find(m => m.id === user?.id)?.roles || []);
}
function setRoles(user: ProjectMember, roles: string[]) {
  modelValue.value = modelValue.value.map((m) => {
    if (m.id === user.id) {
      m = { ...m, roles };
      rolesCache.value[m.id] = m.roles;
    }
    return m;
  });
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

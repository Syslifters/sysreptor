<template>
  <user-selection 
    :value="value"
    @input="updateMembers"
    :multiple="true"
    :disabled="disabled || disableAdd"
    :prevent-unselecting-self="preventUnselectingSelf"
    :append-icon="null"
    :clearable="false"
    class="mt-4"
    v-bind="$attrs" 
  >
    <template #selection="{item: user, index}">
      <v-list-item :disabled="disabled" class="member-item elevation-2 mt-1 mb-1" two-line>
        <v-list-item-content>
          <v-list-item-title>
            <template v-if="user.username && user.name">{{ user.username }} ({{ user.name }})</template>
            <template v-else>{{ user.username || user.name }}</template>
          </v-list-item-title>
          
          <v-list-item-subtitle>
            <v-select
              :value="getRoles(user)"
              @input="setRoles(user, $event)"
              :items="allRoles"
              :disabled="disabled"
              multiple
              solo flat tile dense
              hide-details="auto"
              append-icon=""
              @click.stop=""
              class="select-roles"
            >
              <template #selection="{item: role, parent}">
                <v-chip
                  small
                  close
                  :disabled="disabled"
                  @click="parent.activateMenu()"
                  @click:close="parent.onChipInput(role)"
                >
                  {{ role }}
                </v-chip>
              </template>
              <template #append>
                <v-chip small :disabled="disabled">
                  <v-icon small>mdi-plus</v-icon>
                </v-chip>
              </template>
            </v-select>
          </v-list-item-subtitle>
        </v-list-item-content>

        <v-list-item-action>
          <s-btn @click.stop="removeMember(user)" :disabled="disabled || (preventUnselectingSelf && user.id === $auth.user.id)" icon>
            <v-icon>mdi-delete</v-icon>
          </s-btn>
        </v-list-item-action>
      </v-list-item>

      <s-btn v-if="index === value.length - 1" :disabled="disabled || disableAdd" small color="secondary">
        <v-icon>mdi-plus</v-icon> Add
      </s-btn>
    </template>

    <template #append-icon></template>
  </user-selection>
</template>

<script>
import { cloneDeep, uniq } from 'lodash';

export default {
  props: {
    value: {
      type: Array,
      required: true,
    },
    disabled: {
      type: Boolean,
      default: false
    },
    disableAdd: {
      type: Boolean,
      default: false,
    },
    preventUnselectingSelf: {
      type: Boolean,
      default: false,
    }
  },
  data() {
    return {
      rolesCache: Object.fromEntries(this.value?.filter(m => Array.isArray(m.roles)).map(m => [m.id, m.roles])),
    };
  },
  computed: {
    predefinedRoles() {
      return this.$store.getters['apisettings/settings'].project_member_roles;
    },
    allRoles() {
      return uniq(
        this.predefinedRoles.map(r => r.role)
          .concat(Object.values(this.rolesCache).flat())
      );
    },
    defaultRoles() {
      return this.predefinedRoles
        .filter(r => r.default)
        .map(r => r.role);
    },
  },
  methods: {
    updateMembers(members) {
      members = members.map(cloneDeep);
      for (const m of members) {
        if (!Array.isArray(m.roles)) {
          m.roles = this.rolesCache[m.id] || this.defaultRoles;
          this.rolesCache[m.id] = m.roles;
        }
      }
      this.$emit('input', members);
    },
    removeMember(member) {
      this.$emit('input', this.value.filter(m => m.id !== member.id));
    },
    getRoles(user) {
      return cloneDeep(this.value.find(m => m.id === user?.id)?.roles) || [];
    },
    setRoles(user, roles) {
      const members = cloneDeep(this.value);
      for (const m of members) {
        if (m.id === user.id) {
          m.roles = roles;
          this.rolesCache[m.id] = roles;
        }
      }
      this.$emit('input', members);
    }
  }
}
</script>

<style lang="scss" scoped>
// Always show text input line at end of user-selection
:deep() {
  .v-select__selections {
    .member-item + input:not([disabled]) {
      min-width: 64px !important;
      max-height: inherit !important;
      padding: inherit !important;
    }
  }

  .select-roles {
    width: min-content;

    .v-input__control {
      min-height: 0 !important;
    }
    .v-input__slot {
      padding: 0 !important;
    }
    .v-select__slot {
      width: auto !important;
    }

    .v-select__selections {
      min-height: 0 !important;
      padding: 0 !important;
      width: max-content;

      input {
        display: none;
      }
    }

    .v-chip {
      margin: 0.2em 0.2em 0 0 !important;

      &:not(.v-chip--disabled) {
        cursor: pointer;
      }
    }
    .v-input__append-inner {
      padding-left: 0 !important;
    }
  }
}
</style>

<template>
  <div>
    <s-card class="mt-4">
      <v-card-title>Login information</v-card-title>
      <v-card-text>
        <v-row>
          <v-col>
            <s-text-field
              :model-value="user.username" @update:model-value="updateField('username', $event)"
              label="Username"
              hint="Use this name for logging in"
              autocomplete="off"
              :rules="rules.required"
              :error-messages="props.errors?.username || []"
              required
              :disabled="!canEditUsername"
              spellcheck="false"
            />
          </v-col>
          <v-col cols="auto">
            <s-color-picker
              :model-value="user.color"
              @update:model-value="updateField('color', $event)"
              :disabled="!canEdit"
            >
              <template #activator="{ props: colorPickerProps }">
                <user-avatar 
                  :user="user" 
                  size="large" 
                  class="cursor-pointer mt-1"
                  v-bind="colorPickerProps"
                />
              </template>
            </s-color-picker>
          </v-col>
        </v-row>
        <slot name="login-information" />
      </v-card-text>
    </s-card>

    <s-card class="mt-4">
      <v-card-title>Personal information</v-card-title>
      <v-card-text>
        <v-row class="mt-4">
          <v-col :md="5">
            <s-text-field
              :model-value="user.first_name" @update:model-value="updateField('first_name', $event)"
              label="First name"
              :rules="rules.required"
              required
              :error-messages="props.errors?.first_name || []"
              :disabled="!canEdit"
              spellcheck="false"
              autocomplete="given-name"
            />
          </v-col>
          <v-col :md="2">
            <s-text-field
              :model-value="user.middle_name" @update:model-value="updateField('middle_name', $event)"
              label="Middle name"
              :error-messages="props.errors?.middle_name || []"
              :disabled="!canEdit"
              spellcheck="false"
              autocomplete="middle-name"
            />
          </v-col>
          <v-col :md="5">
            <s-text-field
              :model-value="user.last_name" @update:model-value="updateField('last_name', $event)"
              label="Last name"
              :rules="rules.required"
              required
              :error-messages="props.errors?.last_name || []"
              :disabled="!canEdit"
              spellcheck="false"
              autocomplete="family-name"
            />
          </v-col>
        </v-row>
        <v-row class="mt-4">
          <v-col :md="6">
            <s-text-field
              :model-value="user.title_before" @update:model-value="updateField('title_before', $event)"
              label="Title (before name)"
              :error-messages="props.errors?.title_before || []"
              :disabled="!canEdit"
              spellcheck="false"
              autocomplete="honorific-prefix"
            />
          </v-col>
          <v-col :md="6">
            <s-text-field
              :model-value="user.title_after" @update:model-value="updateField('title_after', $event)"
              label="Title (after name)"
              :error-messages="props.errors?.title_after || []"
              :disabled="!canEdit"
              spellcheck="false"
              autocomplete="honorific-suffix"
            />
          </v-col>
        </v-row>

        <s-text-field
          :model-value="user.email" @update:model-value="updateField('email', $event)"
          type="email"
          label="Email"
          hint="Email address to receive notifications and password reset links on (if enabled)"
          :rules="rules.required_email"
          :error-messages="props.errors?.email || []"
          :disabled="!canEditUsername"
          spellcheck="false"
          autocomplete="email"
          class="mt-8"
        />
        <v-row class="mt-4">
          <v-col :md="6">
            <s-text-field
              :model-value="user.phone" @update:model-value="updateField('phone', $event)"
              type="tel"
              label="Phone number (optional)"
              :error-messages="props.errors?.phone || []"
              :disabled="!canEdit"
              spellcheck="false"
              autocomplete="work tel"
            />
          </v-col>
          <v-col :md="6">
            <s-text-field
              :model-value="user.mobile" @update:model-value="updateField('mobile', $event)"
              type="tel"
              label="Mobile phone number (optional)"
              :error-messages="props.errors?.mobile || []"
              :disabled="!canEdit"
              spellcheck="false"
              autocomplete="mobile tel"
            />
          </v-col>
        </v-row>
      </v-card-text>
    </s-card>

    <s-card class="mt-4">
      <v-card-title><pro-info>Permissions</pro-info></v-card-title>
      <v-card-text>
        <s-autocomplete
          :model-value="user.roles"
          @update:model-value="updateField('roles', $event)"
          :items="roleItems"
          item-title="name"
          item-value="id"
          :item-props="(role: { description?: string|null }) => ({ subtitle: role.description || undefined })"
          label="Roles"
          hint="Users have the combined permissions of all assigned roles."
          persistent-hint
          multiple
          chips
          closable-chips
          :error-messages="props.errors?.roles || []"
          :disabled="!canEditGeneralPermissions"
          data-testid="roles-select"
          class="mb-4"
        />
        <s-checkbox
          :model-value="user.is_superuser" @update:model-value="updateField('is_superuser', $event)"
          label="Superuser"
          hint="Superusers have the highest privileges available. They have all permissions without explicitly assigning them."
          :error-messages="props.errors?.is_superuser || []"
          :disabled="!canEditSuperuserPermissions"
          density="compact"
        >
          <template #label><permission-info :value="canEditSuperuserPermissions" permission-name="Superuser">Superuser</permission-info></template>
        </s-checkbox>
        <s-checkbox
          v-if="user.is_system_user"
          :model-value="user.is_system_user"
          label="System User"
          hint="System users have access to internal functions such as creating backups."
          disabled
          density="compact"
        />

        <div v-if="user.effective_permissions?.length" class="mt-6">
          <div class="text-subtitle-1 mb-1">Effective permissions</div>
          <v-chip
            v-for="permission in user.effective_permissions"
            :key="permission"
            :text="permission"
            size="small"
            class="ma-1"
          />
        </div>
      </v-card-text>
    </s-card>
  </div>
</template>

<script setup lang="ts">
const user = defineModel<User>({ required: true });
const props = defineProps<{
  errors?: any,
}>();

const auth = useAuth();
const apiSettings = useApiSettings();
const canEdit = computed(() => 
  (auth.hasPermission(UserPermission.USER_EDIT) && !user.value.is_superuser && !user.value.is_system_user) || 
  (auth.permissions.value.admin && !user.value.is_system_user) || 
  user.value.id === auth.user.value!.id);
const canEditUsername = computed(() => canEdit.value && auth.hasPermission(UserPermission.USER_EDIT));
const canEditGeneralPermissions = computed(() => canEdit.value && auth.hasPermission(UserPermission.USER_EDIT) && apiSettings.settings!.features.permissions);
const canEditSuperuserPermissions = computed(() => canEdit.value && auth.hasPermission(UserPermission.USER_EDIT) && auth.permissions.value.admin);

const roleItems = computed(() => {
  const roles = apiSettings.settings?.permissions.roles || [];
  // Keep unknown roles selectable/removable
  const unknownRoles = (user.value.roles || [])
    .filter(r => !roles.some(role => role.id === r))
    .map(r => ({ id: r, name: `${r} (unknown role)` }));
  return [...roles, ...unknownRoles];
});

const rules = {
  required: [(v: any) => !!v || 'This field is required!'],
  required_email: [(v: any) => canEditUsername.value ? rules.required[0]!(v) : true],
};

function updateField(fieldName: keyof User, val: any) {
  const newUser = Object.assign({}, user.value);
  // @ts-expect-error no readonly fields are updated
  newUser[fieldName] = val;
  user.value = newUser;
}

</script>

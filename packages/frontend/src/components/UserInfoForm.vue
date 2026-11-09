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
        <s-checkbox
          :model-value="user.is_template_editor" @update:model-value="updateField('is_template_editor', $event)"
          label="Template Editor"
          data-testid="template-editor-checkbox"
          hint="Template Editors are allowed to create and edit finding templates."
          :error-messages="props.errors?.is_template_editor || []"
          :disabled="!canEditGeneralPermissions"
          density="compact"
        />
        <s-checkbox
          :model-value="user.is_designer" @update:model-value="updateField('is_designer', $event)"
          label="Designer"
          data-testid="designer-checkbox"
          hint="Designers can create and edit report designs. Users without this permission can create and edit private designs."
          :error-messages="props.errors?.is_designer || []"
          :disabled="!canEditGeneralPermissions"
          density="compact"
        />
        <s-checkbox
          :model-value="user.is_user_manager" @update:model-value="updateField('is_user_manager', $event)"
          label="User Manager"
          data-testid="user-manager-checkbox"
          hint="User Managers can create and update other users, assign permissions and reset passwords (except superusers)."
          :error-messages="props.errors?.is_user_manager || []"
          :disabled="!canEditGeneralPermissions"
          density="compact"
        />
        <s-checkbox
          :model-value="user.is_global_archiver" @update:model-value="updateField('is_global_archiver', $event)"
          label="Global Archiver"
          data-testid="global-archiver-checkbox"
          hint="Global Archivers will be added to archives when archiving projects (besides project members) and are able to restore these projects. They need to have archiving public keys configured for this permission take effect."
          :error-messages="props.errors?.is_global_archiver || []"
          :disabled="!canEditGeneralPermissions || !apiSettings.settings!.features.archiving"
          density="compact"
        />
        <s-checkbox
          :model-value="user.is_project_admin" @update:model-value="updateField('is_project_admin', $event)"
          label="Project Admin"
          data-testid="project-admin-checkbox"
          hint="Project Admins can access and manage all projects, regardless if they are members of the project or not."
          :error-messages="props.errors?.is_project_admin || []"
          :disabled="!canEditGeneralPermissions"
          density="compact"
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

        <div class="d-flex align-center justify-space-between mt-6 mb-2">
          <div class="text-subtitle-1">Restrictions</div>
          <s-btn-secondary
            v-if="canEditGeneralPermissions"
            size="small"
            text="Reset to defaults"
            prepend-icon="mdi-restore"
            @click="resetPermissionsToDefaults"
          />
        </div>
        <s-checkbox
          v-for="permission in restrictedPermissions"
          :key="permission.field"
          :model-value="isPermissionEnabled(permission)"
          @update:model-value="updateField(permission.field, $event)"
          :label="permission.label"
          :hint="permissionHint(permission)"
          :error-messages="props.errors?.[permission.field] || []"
          :disabled="!canEditGeneralPermissions || isPermissionImplied(permission)"
          density="compact"
        />
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
  (auth.permissions.value.user_manager && !user.value.is_superuser && !user.value.is_system_user) || 
  (auth.permissions.value.admin && !user.value.is_system_user) || 
  user.value.id === auth.user.value!.id);
const canEditUsername = computed(() => canEdit.value && auth.permissions.value.user_manager);
const canEditGeneralPermissions = computed(() => canEdit.value && auth.permissions.value.user_manager && apiSettings.settings!.features.permissions);
const canEditSuperuserPermissions = computed(() => canEdit.value && auth.permissions.value.user_manager && auth.permissions.value.admin);

const restrictedPermissions: { field: keyof User; label: string; hint: string; impliedBy: 'project_admin' | 'user_manager' | 'template_editor' | 'designer' | 'global_archiver' }[] = [
  { field: 'can_create_projects', label: 'Create projects', hint: 'Allow creating and copying projects.', impliedBy: 'project_admin' },
  { field: 'can_import_projects', label: 'Import projects', hint: 'Allow importing projects.', impliedBy: 'project_admin' },
  { field: 'can_edit_projects', label: 'Edit projects', hint: 'Allow editing project content such as findings, sections and notes.', impliedBy: 'project_admin' },
  { field: 'can_update_project_settings', label: 'Update project settings', hint: 'Allow updating project settings like name, design and members.', impliedBy: 'project_admin' },
  { field: 'can_delete_projects', label: 'Delete projects', hint: 'Allow deleting projects.', impliedBy: 'project_admin' },
  { field: 'can_share_notes', label: 'Share notes', hint: 'Allow creating and managing note sharing links.', impliedBy: 'project_admin' },
  { field: 'can_see_all_users', label: 'See all users', hint: 'Allow listing all users. When disabled, only users working in the same projects are listed.', impliedBy: 'user_manager' },
  { field: 'can_see_all_templates', label: 'See all templates', hint: 'Allow listing all templates. When disabled, the user cannot use templates to create findings.', impliedBy: 'template_editor' },
];

const rules = {
  required: [(v: any) => !!v || 'This field is required!'],
  required_email: [(v: any) => canEditUsername.value ? rules.required[0]!(v) : true],
};

function isPermissionImplied(permission: typeof restrictedPermissions[number]) {
  if (permission.impliedBy === 'project_admin') {
    return !!user.value.is_project_admin || !!user.value.is_superuser;
  }
  return !!user.value.is_user_manager || !!user.value.is_superuser;
}

function isPermissionEnabled(permission: typeof restrictedPermissions[number]) {
  return isPermissionImplied(permission) || !!user.value[permission.field];
}

function permissionHint(permission: typeof restrictedPermissions[number]) {
  if (!isPermissionImplied(permission)) {
    return permission.hint;
  }
  const role = permission.impliedBy === 'project_admin' ? 'Project Admin / Superuser' : 'User Manager / Superuser';
  return `${permission.hint} Currently implied by ${role}. The stored value applies again if the role is removed.`;
}

function resetPermissionsToDefaults() {
  const defaults = apiSettings.settings?.permissions.default_user_permissions;
  if (!defaults) {
    return;
  }
  user.value = {
    ...user.value,
    ...defaults,
  };
}

function updateField(fieldName: keyof User, val: any) {
  const newUser = Object.assign({}, user.value);
  // @ts-expect-error no readonly fields are updated
  newUser[fieldName] = val;
  user.value = newUser;
}

</script>

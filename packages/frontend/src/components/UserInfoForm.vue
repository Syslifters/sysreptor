<template>
  <div>
    <s-card class="mt-4">
      <v-card-title>Login information</v-card-title>
      <v-card-text>
        <s-text-field
          :model-value="user.username" @update:model-value="updateField('username', $event)"
          label="Username"
          hint="Use this name for logging in"
          autocomplete="off"
          :rules="rules.required"
          :error-messages="errors?.username || []"
          required
          :disabled="!canEdit || !canEditUsername"
          spellcheck="false"
        />
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
              :error-messages="errors?.first_name || []"
              :disabled="!canEdit"
              spellcheck="false"
            />
          </v-col>
          <v-col :md="2">
            <s-text-field
              :model-value="user.middle_name" @update:model-value="updateField('middle_name', $event)"
              label="Middle name"
              :error-messages="errors?.middle_name || []"
              :disabled="!canEdit"
              spellcheck="false"
            />
          </v-col>
          <v-col :md="5">
            <s-text-field
              :model-value="user.last_name" @update:model-value="updateField('last_name', $event)"
              label="Last name"
              :rules="rules.required"
              required
              :error-messages="errors?.last_name || []"
              :disabled="!canEdit"
              spellcheck="false"
            />
          </v-col>
        </v-row>
        <v-row class="mt-4">
          <v-col :md="6">
            <s-text-field
              :model-value="user.title_before" @update:model-value="updateField('title_before', $event)"
              label="Title (before name)"
              :error-messages="errors?.title_before || []"
              :disabled="!canEdit"
              spellcheck="false"
            />
          </v-col>
          <v-col :md="6">
            <s-text-field
              :model-value="user.title_after" @update:model-value="updateField('title_after', $event)"
              label="Title (after name)"
              :error-messages="errors?.title_after || []"
              :disabled="!canEdit"
              spellcheck="false"
            />
          </v-col>
        </v-row>
        <s-text-field
          :model-value="user.email" @update:model-value="updateField('email', $event)"
          type="email"
          label="Email (optional)"
          :error-messages="errors?.email || []"
          :disabled="!canEdit"
          spellcheck="false"
          class="mt-8"
        />
        <v-row class="mt-4">
          <v-col :md="6">
            <s-text-field
              :model-value="user.phone" @update:model-value="updateField('phone', $event)"
              type="tel"
              label="Phone number (optional)"
              :error-messages="errors?.phone || []"
              :disabled="!canEdit"
              spellcheck="false"
            />
          </v-col>
          <v-col :md="6">
            <s-text-field
              :model-value="user.mobile" @update:model-value="updateField('mobile', $event)"
              type="tel"
              label="Mobile phone number (optional)"
              :error-messages="errors?.mobile || []"
              :disabled="!canEdit"
              spellcheck="false"
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
          :error-messages="errors?.is_template_editor || []"
          :disabled="!canEditGeneralPermissions"
          density="compact"
        />
        <s-checkbox
          :model-value="user.is_designer" @update:model-value="updateField('is_designer', $event)"
          label="Designer"
          data-testid="designer-checkbox"
          hint="Designers can create and edit report designs. Users without this permission can create and edit private designs."
          :error-messages="errors?.is_designer || []"
          :disabled="!canEditGeneralPermissions"
          density="compact"
        />
        <s-checkbox
          :model-value="user.is_user_manager" @update:model-value="updateField('is_user_manager', $event)"
          label="User Manager"
          data-testid="user-manager-checkbox"
          hint="User Managers can create and update other users, assign permissions and reset passwords (except superusers)."
          :error-messages="errors?.is_user_manager || []"
          :disabled="!canEditGeneralPermissions"
          density="compact"
        />
        <s-checkbox
          :model-value="user.is_guest" @update:model-value="updateField('is_guest', $event)"
          label="Guest"
          hint="Guest are not allowed to list other users and might be further restricted by your system operator."
          :error-messages="errors?.is_guest || []"
          :disabled="!canEditGeneralPermissions"
          density="compact"
        />
        <s-checkbox
          :model-value="user.is_global_archiver" @update:model-value="updateField('is_global_archiver', $event)"
          label="Global Archiver"
          data-testid="global-archiver-checkbox"
          hint="Global Archivers will be added to archives when archiving projects (besides project members) and are able to restore these projects. They need to have archiving public keys configured for this permission take effect."
          :error-messages="errors?.is_global_archiver || []"
          :disabled="!canEditGeneralPermissions || !apiSettings.settings!.features.archiving"
          density="compact"
        />
        <s-checkbox
          :model-value="user.is_project_admin" @update:model-value="updateField('is_project_admin', $event)"
          label="Project Admin"
          data-testid="project-admin-checkbox"
          hint="Project Admins can access and manage all projects, regardless if they are members of the project or not."
          :error-messages="errors?.is_project_admin || []"
          :disabled="!canEditGeneralPermissions"
          density="compact"
        />
        <s-checkbox
          :model-value="user.is_superuser" @update:model-value="updateField('is_superuser', $event)"
          label="Superuser"
          hint="Superusers have the highest privileges available. They have all permissions without explicitly assigning them."
          :error-messages="errors?.is_superuser || []"
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
      </v-card-text>
    </s-card>
  </div>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  modelValue: User,
  errors?: any,
  canEditPermissions?: boolean,
  canEditUsername?: boolean,
}>(), {
  errors: null,
  canEditPermissions: false,
  canEditUsername: false,
});
const emit = defineEmits<{(e: 'update:modelValue', modelValue: User): void }>();
const user = computed(() => props.modelValue);

const auth = useAuth();
const apiSettings = useApiSettings();
const canEdit = computed(() => (auth.permissions.value.user_manager && !user.value.is_system_user) || user.value.id === auth.user.value!.id);
const canEditGeneralPermissions = computed(() => canEdit.value && props.canEditPermissions && auth.permissions.value.user_manager && apiSettings.settings!.features.permissions);
const canEditSuperuserPermissions = computed(() => canEdit.value && props.canEditPermissions && auth.permissions.value.user_manager && auth.permissions.value.admin);

const rules = {
  required: [(v: any) => !!v || 'This field is required!'],
};

function updateField(fieldName: keyof User, val: any) {
  const newUser = Object.assign({}, user.value);
  // @ts-expect-error no readonly fields are updated
  newUser[fieldName] = val;
  emit('update:modelValue', newUser);
}

</script>

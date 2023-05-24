<template>
  <div>
    <s-card class="mt-4">
      <v-card-title>Login information</v-card-title>
      <v-card-text>
        <s-text-field 
          :value="user.username" @input="updateField('username', $event)"
          label="Username" 
          hint="Use this name for logging in"
          autocomplete="off"
          :rules="rules.required"
          :error-messages="errors?.username"
          required
          :disabled="!canEdit || !canEditUsername"
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
              :value="user.first_name" @input="updateField('first_name', $event)" 
              label="First name"
              required
              :error-messages="errors?.first_name"
              :disabled="!canEdit"
            />
          </v-col>
          <v-col :md="2">
            <s-text-field 
              :value="user.middle_name" @input="updateField('middle_name', $event)" 
              label="Middle name" 
              :error-messages="errors?.middle_name"
              :disabled="!canEdit"
            />
          </v-col>
          <v-col :md="5">
            <s-text-field
              :value="user.last_name" @input="updateField('last_name', $event)" 
              label="Last name"
              required
              :error-messages="errors?.last_name"
              :disabled="!canEdit"
            />
          </v-col>
        </v-row>
        <v-row class="mt-4">
          <v-col :md="6">
            <s-text-field 
              :value="user.title_before" @input="updateField('title_before', $event)"  
              label="Title (before name)" 
              :error-messages="errors?.title_before"
              :disabled="!canEdit"
            />
          </v-col>
          <v-col :md="6">
            <s-text-field 
              :value="user.title_after" @input="updateField('title_after', $event)" 
              label="Title (after name)" 
              :error-messages="errors?.title_after"
              :disabled="!canEdit"
            />
          </v-col>
        </v-row>
        <s-text-field 
          :value="user.email" @input="updateField('email', $event)" 
          type="email" 
          label="Email (optional)" 
          :error-messages="errors?.email"
          :disabled="!canEdit"
          class="mt-8" 
        />
        <v-row class="mt-4">
          <v-col :md="6">
            <s-text-field 
              :value="user.phone" @input="updateField('phone', $event)" 
              type="tel" 
              label="Phone number (optional)" 
              :error-messages="errors?.phone"
              :disabled="!canEdit"
            />
          </v-col>
          <v-col :md="6">
            <s-text-field 
              :value="user.mobile" @input="updateField('mobile', $event)" 
              type="tel" 
              label="Mobile phone number (optional)" 
              :error-messages="errors?.mobile"
              :disabled="!canEdit"
            />
          </v-col>
        </v-row>
      </v-card-text>
    </s-card>

    <s-card class="mt-4">
      <v-card-title>Permissions</v-card-title>
      <v-card-text>
        <s-checkbox
          :value="user.is_template_editor" @change="updateField('is_template_editor', $event)" 
          label="Template Editor"
          hint="Template Editors are allowed to create and edit finding templates."
          :error-messages="errors?.is_template_editor"
          :disabled="!canEditGeneralPermissions"
        />
        <s-checkbox 
          :value="user.is_designer" @change="updateField('is_designer', $event)" 
          label="Designer"
          hint="Designers can create and edit report designs. Users without this permission can create and edit private designs."
          :error-messages="errors?.is_designer"
          :disabled="!canEditGeneralPermissions"
        />
        <s-checkbox
          :value="user.is_user_manager" @change="updateField('is_user_manager', $event)" 
          label="User Manager"
          hint="User Managers can create and update other users, assign permissions and reset passwords (except superusers)."
          :error-messages="errors?.is_user_manager"
          :disabled="!canEditGeneralPermissions"
        />
        <s-checkbox 
          :value="user.is_superuser" @change="updateField('is_superuser', $event)" 
          label="Superuser" 
          hint="Superusers have the highest privileges available. They have all permissions without explicitly assigning them."
          :error-messages="errors?.is_superuser"
          :disabled="!canEditSuperuserPermissions"
        />
        <s-checkbox
          :value="user.is_guest" @change="updateField('is_guest', $event)" 
          label="Guest"
          hint="Guest are not allowed to list other users and might be further restricted by your system operator."
          :error-messages="errors?.is_guest"
          :disabled="!canEditGeneralPermissions"
        />
        <s-checkbox 
          v-if="archivingEnabled"
          :value="user.is_global_archiver" @change="updateField('is_global_archiver', $event)"
          label="Global Archiver"
          hint="Global Archivers will be added to archives when archiving projects (besides project members) and are able to restore these projects. They need to have archiving public keys configured for this permission take effect."
          :error-messages="errors?.is_global_archiver"
          :disabled="!canEditGeneralPermissions"
        />
        <s-checkbox
          v-if="user.is_system_user"
          :value="user.is_system_user"
          label="System User"
          hint="System users have access to internal functions such as creating backups."
          disabled
        />
      </v-card-text>
    </s-card>
  </div>
</template>

<script>
export default {
  props: {
    value: {
      type: Object,
      required: true,
    },
    errors: {
      type: [Object, null],
      default: null,
    },
    canEditPermissions: {
      type: Boolean,
      default: false,
    },
    canEditUsername: {
      type: Boolean,
      default: false,
    }
  },
  data() {
    return {
      rules: {
        required: [v => !!v || 'This field is required!'],
      }
    }
  },
  computed: {
    user() {
      return this.value;
    },
    canEdit() {
      return (this.$auth.hasScope('user_manager') && !this.user.is_system_user) || this.user.id === this.$auth.user.id;
    },
    canEditGeneralPermissions() {
      return this.canEdit && this.canEditPermissions && this.$auth.hasScope('user_manager');
    },
    canEditSuperuserPermissions() {
      return this.canEdit && this.canEditPermissions && this.$auth.hasScope('admin');
    },
    archivingEnabled() {
      return this.$store.getters['apisettings/settings'].features.archiving;
    },
  },
  methods: {
    updateField(fieldName, val) {
      const newUser = Object.assign({}, this.user);
      newUser[fieldName] = val;
      this.$emit('input', newUser);
    },
  },
}
</script>

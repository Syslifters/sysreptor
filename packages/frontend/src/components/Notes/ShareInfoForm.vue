<template>
  <div>
    <v-row>
      <v-col cols="12" class="pt-0 pb-0">
        <slot name="header">
          <div v-if="publicLink">
            <v-code>
              <s-btn-icon
                @click="copyToClipboard(publicLink)"
                icon="mdi-content-copy"
                size="small"
                density="compact"
              />
              {{ publicLink }}
            </v-code>
            <p class="mt-2">
              Shared by 
              <chip-member :value="modelValue.shared_by || ({username: 'unknown'} as unknown as UserShortInfo)" /> 
              <chip-created :value="modelValue.created" />
            </p>
          </div>
          <div v-else>
            <v-card-title class="pa-0">New Share Link</v-card-title>
            <p>Share notes to allow public access via a share link.</p>
          </div>
        </slot>
      </v-col>

      <v-col v-if="showField('password')" cols="6">
        <s-password-field
          :model-value="modelValue.password"
          @update:model-value="updateProp('password', $event)"
          label="Link Password (optional)"
          generate
          :disabled="props.disabled"
          :error-messages="props.error?.password"
        />
      </v-col>
      <v-col v-if="showField('permissions_write')" cols="6">
        <s-checkbox
          :model-value="modelValue.permissions_write"
          @update:model-value="updateProp('permissions_write', $event)"
          label="Write access"
          messages="Allow public users to edit note contents"
          :disabled="props.disabled"
          :error-messages="props.error?.permissions_write"
        />
      </v-col>

      <v-col v-if="showField('expire_date')" cols="6">
        <s-date-picker
          :model-value="modelValue.expire_date"
          @update:model-value="updateProp('expire_date', $event)"
          label="Expire Date"
          :disabled="props.disabled"
          :error-messages="props.error?.expire_date"
        />
      </v-col>
      <v-col v-if="showField('is_revoked')" cols="6">
        <s-checkbox 
          :model-value="modelValue.is_revoked"
          @update:model-value="updateProp('is_revoked', $event)"
          label="Is Revoked?"
          messages="Revoked share links can no longer be accessed"
          :disabled="props.disabled"
          :error-messages="props.error?.is_revoked"
        />
      </v-col>

      <slot name="append-fields" />
    </v-row>
    <v-alert v-if="props.error?.detail" color="error">
      {{ props.error.detail }}
    </v-alert>
  </div>
</template>

<script setup lang="ts">
const modelValue = defineModel<ShareInfo>('modelValue', { required: true });
const props = defineProps<{
  disabled?: boolean;
  error?: any|null;
  hiddenFields?: string[];
}>();

const publicLink = computed(() => {
  if (!modelValue.value.id) {
    return null;
  }
  return `${window.location.origin}/shared/${modelValue.value.id}/`;
});

function updateProp(prop: string, value: any) {
  modelValue.value = {
    ...modelValue.value,
    [prop]: value,
  };
}

function showField(field: string) {
  return !props.hiddenFields || !props.hiddenFields.includes(field);
}
</script>

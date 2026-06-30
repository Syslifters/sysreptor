<template>
  <s-text-field
    v-model="password"
    label="PDF password (optional)"
    spellcheck="false"
  >
    <template #prepend>
      <s-checkbox v-model="shouldEncryptPdf" v-tooltip:top="'Encrypt PDF'" />
    </template>
    <template #append-inner>
      <v-icon-btn
        icon="mdi-lock-reset"
        @click="password = generateRandomPassword()"
      />
      <v-icon-btn
        icon="mdi-download"
        @click="downloadPassword()"
        :disabled="!shouldEncryptPdf"
      />
      <v-icon-btn
        icon="mdi-content-copy"
        @click="copyToClipboard(password)"
        :disabled="!shouldEncryptPdf"
      />
    </template>
  </s-text-field>
</template>

<script setup lang="ts">
const password = defineModel<string>({ required: true });
const props = defineProps<{
  filename?: string;
}>();

const shouldEncryptPdf = computed({
  get: () => !!password.value,
  set: (value) => { password.value = value ? generateRandomPassword() : '' }
});

function downloadPassword() {
  let filename = props.filename || 'password.txt';
  if (filename.endsWith('.pdf')) {
    filename = filename.replace(/\.pdf$/, '_password.txt');
  }
  if (!filename.endsWith('.txt')) {
    filename += '.txt';
  }
  fileDownload(password.value, filename, 'text/plain');
}
</script>

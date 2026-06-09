<template>
  <div>
    <p>
      <slot name="message" />
    </p>
    <p class="mt-2">
      <s-code>{{ gpgCommand }}</s-code>
      <s-btn-icon 
        @click="copyToClipboard(gpgCommand)"
        icon="mdi-content-copy"
        v-tooltip.top="'Copy to clipboard'"
        size="small" 
        density="compact"
        class="ml-1"
      />
    </p>
    <s-codeblock-field
      :model-value="props.encryptedData"
      readonly
    >
      <template #append-inner>
        <s-btn-icon 
          @click="copyToClipboard(props.encryptedData)"
          icon="mdi-content-copy"
          v-tooltip.top="'Copy to clipboard'"
          size="small"
          density="compact"
        />
        <s-btn-icon 
          @click="fileDownload(props.encryptedData, filename, 'text/plain')"
          icon="mdi-download"
          v-tooltip.top="`Download ${filename}`"
          size="small"
          density="compact"
          class="mt-2"
        />
      </template>
    </s-codeblock-field>

    <s-text-field
      v-model="modelValue"
      label="Decrypted data"
      :error-messages="props.errorMessages || []"
      spellcheck="false"
      class="mt-4"
    />
  </div>
</template>

<script lang="ts" setup>
import { sampleSize } from 'lodash-es';

const modelValue = defineModel<string>();
const props = defineProps<{
  encryptedData: string;
  errorMessages?: string[]|null;
}>();

const filename = computed(() => `message_${sampleSize('abcdefghijklmnopqrstuvwxyz', 6).join('')}.txt`)
const gpgCommand = computed(() => `gpg --decrypt ${filename.value}`);

</script>

<style lang="scss" scoped>
:deep(.v-field__append-inner) {
  flex-direction: column;
}
</style>

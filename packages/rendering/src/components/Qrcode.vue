<template>
  <img v-if="imageUrl" :src="imageUrl" :alt="value || ''" />
</template>

<script setup lang="ts">
import { useRenderTask } from '@/utils';
import * as QRCode from 'qrcode';
import { ref, watch } from 'vue';

const props = defineProps<{
  value?: string|null;
  options?: QRCode.QRCodeToDataURLOptions|null;
}>();

const imageUrl = ref<string | null>(null);
watch(() => props.value, useRenderTask(async () => {
  if (!props.value) {
    imageUrl.value = null;
    return;
  }

  try {
    imageUrl.value = await QRCode.toDataURL(props.value, props.options || {});
  } catch (error) {
    console.warn('QR code error', { message: 'QR code error', details: (error as Error).message });
    imageUrl.value = null;
  }
}), { immediate: true });
</script>


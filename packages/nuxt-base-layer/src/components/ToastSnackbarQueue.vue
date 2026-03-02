<template>
  <div class="toast-snackbar-queue">
    <v-snackbar-queue
      v-model="toastQueue"
      location="bottom right"
      display-strategy="overflow"
      :total-visible="5"
      closable
      close-on-content-click
    >
      <template #actions="{ props: actionsProps }">
        <s-btn-icon
          class="toast-snackbar-btn"
          variant="text"
          icon="mdi-close"
          size="small"
          @click="actionsProps.onClick"
        />
      </template>
    </v-snackbar-queue>
    <v-snackbar
      :model-value="!!confirmState"
      location="bottom right"
      color="warning"
      timeout="-1"
      @update:model-value="onConfirmSnackbarUpdate"
    >
      <template v-if="confirmState" #text>
        {{ confirmState.message }}
      </template>
      <template v-if="confirmState" #actions>
        <v-btn
          class="toast-snackbar-btn"
          variant="text"
          size="small"
          @click="confirmState!.resolve(true)"
        >
          {{ confirmState!.buttonText }}
        </v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
import { useToast } from "@base/composables/toast";

const { toastQueue, confirmState } = useToast();

function onConfirmSnackbarUpdate(value: boolean) {
  if (!value && confirmState.value) {
    confirmState.value.resolve(false);
  }
}
</script>

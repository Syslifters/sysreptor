<template>
  <s-dialog v-model="confirmDialogVisible" :disabled="props.disabled || !props.confirm" max-width="500">
    <template #activator="{ props: dialogProps }">
      <s-tooltip :disabled="!tooltipText" :text="tooltipText">
        <template #activator="{ props: tooltipProps }">
          <v-list-item
            v-if="buttonVariant === 'list-item'"
            :title="buttonText"
            :disabled="props.disabled"
            @click="!props.confirm ? performAction() : null"
            link
            v-bind="{...$attrs, ...tooltipProps, ...dialogProps}"
          >
            <template #prepend v-if="buttonIcon">
              <v-progress-circular v-if="actionInProgress" indeterminate size="24" />
              <v-icon v-else :icon="buttonIcon" :color="($attrs.color as string|undefined) || buttonColor" />
            </template>
          </v-list-item>
          <s-btn
            v-else-if="buttonVariant === 'icon'"
            :icon="buttonIcon"
            :loading="actionInProgress"
            :disabled="disabled"
            :color="($attrs.color as string|undefined) || buttonColor || 'secondary'"
            variant="text"
            @click="!props.confirm ? performAction() : null"
            v-bind="{...$attrs, ...tooltipProps, ...dialogProps}"
          />
          <s-btn
            v-else
            :prepend-icon="buttonIcon"
            :text="buttonText"
            :loading="actionInProgress"
            :disabled="disabled"
            :color="($attrs.color as string|undefined) || buttonColor || 'secondary'"
            class="ml-1 mr-1"
            @click="!props.confirm ? performAction() : null"
            v-bind="{...$attrs, ...tooltipProps, ...dialogProps}"
          />
        </template>
      </s-tooltip>
    </template>

    <template #title>{{ props.dialogTitle }}</template>
    <template #default>
      <v-card-text>
        <template v-if="props.dialogText">{{ props.dialogText }}</template>
        <template v-if="props.confirmInput">
          <br><br>
          Enter the following text to confirm: <br>
          <strong>{{ props.confirmInput }}</strong>
          <s-text-field
            v-model="confirmUserInput"
            :rules="rules.confirm"
            density="compact"
            spellcheck="false"
            class="mt-2"
          />
        </template>
      </v-card-text>
      <v-divider />
      <v-card-actions>
        <v-spacer />
        <s-btn
          @click="confirmDialogVisible = false"
          variant="text"
          text="Cancel"
        />
        <s-btn
          :disabled="props.confirmInput && props.confirmInput !== confirmUserInput"
          :loading="actionInProgress"
          :color="props.buttonColor || 'primary'"
          @click="performAction"
          :prepend-icon="props.buttonIcon"
          :text="props.buttonText"
        />
      </v-card-actions>
    </template>
  </s-dialog>
</template>

<script setup lang="ts">
export type BtnConfirmVariant = 'default' | 'icon' | 'list-item';

const props = withDefaults(defineProps<{
  buttonText: string;
  action: (() => Promise<void>)|(() => void);
  buttonIcon?: string;
  buttonColor?: string;
  tooltipText?: string;
  dialogTitle?: string;
  dialogText?: string;
  buttonVariant?: BtnConfirmVariant;
  confirm?: boolean;
  confirmInput?: string;
  disabled?: boolean;
  keyboardShortcut?: string;
}>(), {
  dialogTitle: 'Confirm',
  buttonVariant: 'default',
  confirm: true,
  disabled: false,
  buttonIcon: undefined,
  buttonColor: undefined,
  tooltipText: undefined,
  dialogText: undefined,
  confirmInput: undefined,
  keyboardShortcut: undefined,
});

const confirmDialogVisible = ref(false);
const confirmUserInput = ref('');
const actionInProgress = ref(false);
const rules = {
  confirm: [(v: string) => (v || '').trim() === (props.confirmInput || '').trim() || 'Confirmation text does not match']
};

async function performAction() {
  if (actionInProgress.value || props.disabled) {
    return;
  }

  actionInProgress.value = true;
  try {
    await Promise.resolve(props.action());
    confirmDialogVisible.value = false;
  } catch (error) {
    requestErrorToast({ error });
  } finally {
    actionInProgress.value = false;
  }
}

if (props.keyboardShortcut) {
  function onKeyDown(event: KeyboardEvent) {
    if (props.keyboardShortcut &&
        ((props.keyboardShortcut.startsWith('ctrl+') && event.ctrlKey && event.key === props.keyboardShortcut.substring(5)) ||
         (props.keyboardShortcut === event.key))
    ) {
      event.preventDefault();
      if (props.confirm) {
        confirmDialogVisible.value = true;
      } else {
        performAction();
      }
    }
  }

  onMounted(() => {
    window.addEventListener('keydown', onKeyDown);
  });
  onBeforeUnmount(() => {
    window.removeEventListener('keydown', onKeyDown);
  });
}
</script>

<style lang="scss" scoped>
@use "@/assets/vuetify" as vuetify;

:deep(.v-list-item__prepend > .v-progress-circular ~ .v-list-item__spacer) {
  width: vuetify.$list-item-icon-margin-start;
}
</style>

<template>
  <s-dialog v-model="confirmDialogVisible" :disabled="props.disabled || !props.confirm" max-width="500">
    <template #activator="{ props: dialogProps }">
      <s-tooltip :disabled="!tooltipText" :text="tooltipText">
        <template #activator="{ props: tooltipProps }">
          <v-list-item
            v-if="buttonVariant === 'list-item'"
            :title="buttonText"
            :disabled="props.disabled"
            @click="onClick"
            link
            v-bind="{...attrs, ...tooltipProps, ...dialogProps}"
          >
            <template #prepend v-if="buttonIcon">
              <v-progress-circular v-if="actionInProgress" indeterminate size="24" />
              <v-icon v-else :icon="buttonIcon" :color="(attrs.color as string|undefined) || buttonColor" />
            </template>
          </v-list-item>
          <s-btn-icon
            v-else-if="buttonVariant === 'icon'"
            :icon="buttonIcon"
            :loading="actionInProgress"
            :disabled="disabled"
            :color="(attrs.color as string|undefined) || buttonColor || 'secondary'"
            @click="onClick"
            v-bind="{...attrs, ...tooltipProps, ...dialogProps}"
          />
          <s-btn
            v-else
            :prepend-icon="buttonIcon"
            :text="buttonText"
            :loading="actionInProgress"
            :disabled="disabled"
            :color="(attrs.color as string|undefined) || buttonColor || 'secondary'"
            @click="onClick"
            v-bind="{...attrs, ...tooltipProps, ...dialogProps}"
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
          <s-btn-icon 
            @click="copyToClipboard(props.confirmInput)" 
            size="small" 
            density="compact"
            class="ml-1"
          >
            <v-icon icon="mdi-content-copy" />
            <s-tooltip activator="parent" text="Copy to clipboard" />
          </s-btn-icon>

          <s-text-field
            v-model="confirmUserInput"
            :rules="rules.confirm"
            density="compact"
            spellcheck="false"
            class="mt-2"
            data-testid="confirm-input"
          />
        </template>
      </v-card-text>
      <v-divider />
      <v-card-actions>
        <v-spacer />
        <s-btn-other
          @click="confirmDialogVisible = false"
          text="Cancel"
        />
        <s-btn
          :disabled="props.confirmInput && props.confirmInput !== confirmUserInput"
          :loading="actionInProgress"
          :color="props.buttonColor || 'primary'"
          @click="performAction"
          :prepend-icon="props.buttonIcon"
          :text="props.buttonText"
          data-testid="confirm-button"
        />
      </v-card-actions>
    </template>
  </s-dialog>
</template>

<script setup lang="ts">
export type BtnConfirmVariant = 'default' | 'icon' | 'list-item';

defineOptions({
  inheritAttrs: false
});

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
const attrs = useAttrs();

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
  useKeyboardShortcut(props.keyboardShortcut, () => {
    if (props.confirm) {
      confirmDialogVisible.value = true;
    } else {
      performAction();
    }
  });
}

function onClick() {
  if (props.confirm) {
    confirmDialogVisible.value = true;
  } else {
    performAction();
  }
}

defineExpose({
  click: onClick,
})
</script>

<style lang="scss" scoped>
@use "@base/assets/vuetify" as vuetify;

:deep(.v-list-item__prepend > .v-progress-circular ~ .v-list-item__spacer) {
  width: vuetify.$list-item-icon-margin-start;
}
</style>

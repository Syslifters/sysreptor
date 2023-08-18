<template>
  <s-dialog v-if="confirm" v-model="confirmDialogVisible" :disabled="disabled" max-width="500">
    <template #activator="{on: dialogOn, attrs: dialogAttrs}">
      <s-tooltip :disabled="!tooltipText">
        <template #activator="{on: tooltipOn, attrs: tooltipAttrs}">
          <v-list-item 
            v-if="listItem" 
            link 
            v-bind="{ ...$attrs, ...dialogAttrs, ...tooltipAttrs}"
            v-on="{...dialogOn, ...tooltipOn}"
          >
            <v-list-item-icon v-if="buttonIcon">
              <v-progress-circular v-if="actionInProgress" indeterminate />
              <v-icon v-else :color="$attrs.color || buttonColor">{{ buttonIcon }}</v-icon>
            </v-list-item-icon>
            <v-list-item-title>{{ buttonText }}</v-list-item-title>
          </v-list-item>
          <s-btn 
            v-else
            :icon="icon" 
            :loading="actionInProgress" 
            :color="$attrs.color || buttonColor || 'secondary'" 
            class="ml-1 mr-1" 
            v-bind="{...$attrs, ...dialogAttrs, ...tooltipAttrs}" 
            v-on="{...dialogOn, ...tooltipOn}"
          >
            <v-icon v-if="buttonIcon">{{ buttonIcon }}</v-icon>
            <template v-if="!icon">{{ buttonText }}</template>
          </s-btn>
        </template>
        <template #default>{{ tooltipText }}</template>
      </s-tooltip>
    </template>

    <template #title>{{ dialogTitle }}</template>
    <template #default>
      <v-card-text>
        <template v-if="dialogText">{{ dialogText }}</template>
        <template v-if="confirmInput">
          <br><br>
          Enter the following text to confirm: <br>
          <strong>{{ confirmInput }}</strong>
          <s-text-field
            v-model="confirmUserInput"
            :rules="[v => v === confirmInput || 'Confirmation text does not match']"
            dense
            class="mt-2"
          />
        </template>
      </v-card-text>
      <v-divider />
      <v-card-actions>
        <v-spacer />
        <s-btn 
          @click="confirmDialogVisible = false" 
          color="secondary"
        >
          Cancel
        </s-btn>
        <s-btn 
          :disabled="confirmInput && confirmInput !== confirmUserInput" 
          :loading="actionInProgress" 
          :color="buttonColor || 'primary'"
          @click="performAction" 
        >
          <v-icon v-if="buttonIcon">{{ buttonIcon }}</v-icon>
          {{ buttonText }}
        </s-btn>
      </v-card-actions>
    </template>
  </s-dialog>

  <s-tooltip v-else :disabled="!tooltipText">
    <template #activator="{on: tooltipOn, attrs: tooltipAttrs}">
      <v-list-item 
        v-if="listItem" 
        @click="performAction"
        :disabled="disabled"
        link 
        v-bind="{...tooltipAttrs, ...$attrs}"
        v-on="{...tooltipOn, ...$listeners}"
      >
        <v-list-item-icon v-if="buttonIcon">
          <v-progress-circular v-if="actionInProgress" indeterminate />
          <v-icon v-else :color="$attrs.color || buttonColor">{{ buttonIcon }}</v-icon>
        </v-list-item-icon>
        <v-list-item-title>{{ buttonText }}</v-list-item-title>
      </v-list-item>
      <s-btn 
        v-else 
        :icon="icon" 
        :loading="actionInProgress" 
        :disabled="disabled"
        @click="performAction" 
        :color="$attrs.color || buttonColor || 'secondary'" 
        class="ml-1 mr-1" 
        v-bind="{...tooltipAttrs, ...$attrs}"
        v-on="{...tooltipOn, ...$listeners}"
      >
        <v-icon v-if="buttonIcon">{{ buttonIcon }}</v-icon>
        <template v-if="!icon">{{ buttonText }}</template>
      </s-btn>
    </template>

    <template #default>{{ tooltipText }}</template>
  </s-tooltip>
</template>

<script>
export default {
  props: {
    buttonText: {
      type: String,
      required: true,
    },
    buttonIcon: {
      type: String,
      default: null,
    },
    buttonColor: {
      type: String,
      default: null,
    },
    tooltipText: {
      type: String,
      default: null,
    },
    dialogTitle: {
      type: String,
      default: 'Confirm',
    },
    dialogText: {
      type: String,
      default: null,
    },
    icon: {
      type: Boolean,
      default: false,
    },
    listItem: {
      type: Boolean,
      default: false,
    },
    confirm: {
      type: Boolean,
      default: true,
    },
    confirmInput: {
      type: String,
      default: null,
    },
    action: {
      type: Function,
      required: true,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    keyboardShortcut: {
      type: String,
      default: null
    },
  },
  emits: ['click'],
  data() {
    return {
      confirmDialogVisible: false,
      confirmUserInput: '',
      actionInProgress: false,
    }
  },
  mounted() {
    if (this.keyboardShortcut) {
      window.addEventListener('keydown', this.onKeyDown);
    }
  },
  beforeDestroy() {
    window.removeEventListener('keydown', this.onKeyDown);
  },
  methods: {
    onKeyDown(event) {
      if ((this.keyboardShortcut.startsWith('ctrl+') && event.ctrlKey && event.key === this.keyboardShortcut.substring(5)) || (this.keyboardShortcut === event.key)) {
        event.preventDefault();
        if (this.confirm) {
          this.confirmDialogVisible = true;
        } else {
          this.performAction();
        }
      }
    },
    async performAction() {
      if (this.actionInProgress || this.disabled) {
        return;
      }

      this.actionInProgress = true;
      try {
        await Promise.resolve(this.action());
        this.confirmDialogVisible = false;
      } catch (error) {
        this.$toast.global.requestError({ error });
      } finally {
        this.actionInProgress = false;
      }
    }
  }
}
</script>

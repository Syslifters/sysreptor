<template>
  <s-dialog v-if="confirm" v-model="confirmDialogVisible" max-width="500">
    <template #activator="{on: dialogOn, attrs: dialogAttrs}">
      <s-tooltip :disabled="!tooltipText">
        <template #activator="{on: tooltipOn, attrs: tooltipAttrs}">
          <s-btn 
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

  <s-btn 
    v-else 
    :icon="icon" 
    :loading="actionInProgress" 
    @click="performAction" 
    :color="$attrs.color || buttonColor || 'secondary'" 
    class="ml-1 mr-1" 
    v-bind="$attrs"
  >
    <v-icon v-if="buttonIcon">{{ buttonIcon }}</v-icon>
    <template v-if="!icon">{{ buttonText }}</template>
  </s-btn>
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
  },
  emits: ['click'],
  data() {
    return {
      confirmDialogVisible: false,
      confirmUserInput: '',
      actionInProgress: false,
    }
  },
  methods: {
    async performAction() {
      if (this.actionInProgress) {
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

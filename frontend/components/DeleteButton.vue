<template>
  <v-dialog v-if="confirm" v-model="deleteConfirmDialogVisible" max-width="500">
    <template #activator="{on, attrs}">
      <s-btn v-if="icon" icon v-bind="{...$props, ...$attrs, ...attrs}" v-on="on">
        <v-icon>mdi-delete</v-icon>
      </s-btn>
      <s-btn v-else color="error" v-bind="{...$props, ...$attrs, ...attrs}" v-on="on">
        <v-icon>mdi-delete</v-icon>
        Delete
      </s-btn>
    </template>

    <s-card>
      <v-card-title>Confirm Delete?</v-card-title>
      <v-card-text>
        Do you really want to delete this item? This action is not reversible!
        <template v-if="confirmInput">
          <br><br>
          Enter the following to confirm deletion: <br>
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
        <s-btn @click="deleteConfirmDialogVisible = false">Cancel</s-btn>
        <s-btn :disabled="confirmInput && confirmInput !== confirmUserInput" color="error" @click="performDelete">
          <v-icon>mdi-delete</v-icon>
          Delete
        </s-btn>
      </v-card-actions>
    </s-card>
  </v-dialog>
  <s-btn v-else-if="!confirm && icon" icon v-bind="{...$props, ...$attrs}" @click="performDelete">
    <v-icon>mdi-delete</v-icon>
  </s-btn>
  <s-btn v-else-if="!confirm && !icon" v-bind="{...$props, ...$attrs}" @click="performDelete" color="error">
    <v-icon>mdi-delete</v-icon>
    Delete
  </s-btn>
</template>

<script>
export default {
  props: {
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
    }
  },
  emits: ['delete'],
  data() {
    return {
      deleteConfirmDialogVisible: false,
      confirmUserInput: '',
    }
  },
  methods: {
    performDelete() {
      this.deleteConfirmDialogVisible = false;
      this.$emit('delete');
    }
  }
}
</script>

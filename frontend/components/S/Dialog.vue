<template>
  <v-dialog v-bind="$attrs" v-on="$listeners" :max-width="maxWidth" :retain-focus="false">
    <template #activator="{on, attrs}"><slot name="activator" v-bind="{on, attrs}" /></template>
    <template #default>
      <s-card>
        <v-card-title>
          <v-toolbar flat>
            <v-toolbar-title><slot name="title" /></v-toolbar-title>
            <v-spacer />
            <slot name="toolbar" />
            <s-tooltip>
              <template #activator="{attrs, on}">
                <s-btn v-bind="attrs" v-on="on" @click="$emit('input', false)" icon x-large>
                  <v-icon>mdi-close-thick</v-icon>
                </s-btn>
              </template>
              <span>Cancel</span>
            </s-tooltip>
          </v-toolbar>
        </v-card-title>

        <slot name="default" />
      </s-card>
    </template>
  </v-dialog>
</template>

<script>
export default {
  props: {
    maxWidth: {
      type: String,
      default: '50%',
    },
  }
}
</script>

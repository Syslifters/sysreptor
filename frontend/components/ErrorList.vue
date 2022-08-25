<template>
  <div class="pa-4">
    <div v-for="msg, idx in messages" :key="idx" class="mb-4">
      <div class="error-header">
        <v-chip class="ma-2 mt-0" :color="{'error': 'red', 'warning': 'yellow'}[msg.level]" small label>{{ msg.level.toUpperCase() }}</v-chip>
        <p class="error-message">
          <slot name="message" :msg="msg">
            {{ msg.message }}
            <span v-if="msg.location && msg.location.name" class="error-location">
              in "{{ msg.location.name }}"
              <template v-if="msg.location.path">{{ msg.location.path }}</template>
            </span>
          </slot>
        </p>
      </div>

      <pre v-if="msg.details" class="error-details ml-4">{{ msg.details }}</pre>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    value: {
      type: Object,
      required: true,
    }
  },
  computed: {
    messages() {
      return (this.value?.error || []).concat(this.value?.warning || []);
    }
  }
}
</script>

<style lang="scss" scoped>
.error-header {
  margin-bottom: 0;
  display: flex;
}
.error-message {
  display: inline-block;
  flex-grow: 1;
  margin-bottom: 0;
}
.error-location {
  font-size: smaller;
}
.error-details {
  font-size: small;
  white-space: pre-wrap;
}
</style>

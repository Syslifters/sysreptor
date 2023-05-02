<template>
  <v-text-field
    v-bind="$attrs" v-on="$listeners" 
    persistent-hint
    hide-details="auto" 
    :error-count="100"
    outlined 
    spellcheck="false"
  />
</template>

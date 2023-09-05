<template>
  <chip-date
    :value="value" 
    icon="mdi-file-document-plus" 
    tooltip-prefix-text="Created: " 
    v-bind="$attrs" 
    v-on="$listeners"
  />
</template>

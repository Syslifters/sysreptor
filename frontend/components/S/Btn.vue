<template>
  <v-btn v-bind="$attrs" v-on="$listeners" depressed>
    <template v-for="_, name in $scopedSlots" :slot="name"><slot :name="name" /></template>
  </v-btn>
</template>

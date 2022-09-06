<template>
  <v-card v-bind="$attrs" v-on="$listeners" outlined>
    <template v-for="_, name in $scopedSlots" :slot="name"><slot :name="name" /></template>
  </v-card>
</template>

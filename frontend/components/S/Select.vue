<template>
  <v-select v-bind="$attrs" v-on="$listeners" hide-details="auto" outlined class="mt-1">
    <template v-for="_, name in $scopedSlots" :slot="name" slot-scope="data"><slot :name="name" v-bind="data" /></template>
  </v-select>
</template>

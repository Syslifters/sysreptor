<template>
  <div>
    <div v-if="['headline', 'section-create'].includes(form.form)">
      <s-text-field
        v-model="form.headline.text"
        label="Headline"
        :disabled="props.disabled"
        class="mb-4"
      />
      <s-select
        v-model.number="form.headline.tag"
        :items="['h1', 'h2', 'h3', 'h4', 'h5', 'h6']"
        label="Tag"
        :disabled="props.disabled"
      />
      <s-checkbox
        v-model="form.headline.intoc"
        label="Include in Table of Contents"
        :disabled="props.disabled"
      />
      <s-checkbox
        v-model="form.headline.numbered"
        label="Prepend chapter number"
        :disabled="props.disabled"
        class="mb-4"
      />
    </div>
    <div v-if="['markdown-create', 'section-create'].includes(form.form)">
      <s-select
        v-model="form.markdown.form"
        :items="['text', 'variable']"
        label="Markdown Type"
        :disabled="props.disabled"
        class="mb-4"
      />
    </div>
    <div v-if="form.form === 'markdown-text' || (['markdown-create', 'section-create'].includes(form.form) && form.markdown.form === 'text')">
      <markdown-field
        v-model="form.markdown.text"
        label="Markdown"
        v-bind="markdownProps"
        class="mb-4"
      />
    </div>
    <div v-if="form.form === 'markdown-variable' || (['markdown-create', 'section-create'].includes(form.form) && form.markdown.form === 'variable')">
      <!-- TODO: autocomplete report/finding variables (ComboBox - allow other values) -->
      <s-text-field
        v-model="form.markdown.variable"
        label="Markdown Variable"
        hint="Variable name of report or finding field (e.g. report.executive_summary, finding.description)"
        :disabled="props.disabled"
        class="mb-4"
      />
    </div>
    <div v-if="form.form === 'chart-create'" class="mb-4">
      <s-select
        v-model="form.chart.chartType"
        :items="['bar', 'pie', 'doughnut', 'line', 'radar', 'polarArea']"
        label="Chart Type"
        class="mb-4"
        :disabled="props.disabled"
      />
      <s-text-field
        v-model="form.chart.caption"
        label="Caption"
        :disabled="props.disabled"
        class="mb-4"
      />
    </div>
    <div v-if="form.form === 'footer-create'">
      <s-text-field
        v-model="form.footer.textLeft"
        label="Footer Text Left (optional)"
        class="mb-4"
        :disabled="props.disabled"
      />
      <s-text-field
        v-model="form.footer.textCenter"
        label="Footer Text Center (optional)"
        class="mb-4"
        :disabled="props.disabled"
      />
      <s-select
        v-model="form.footer.pageNumberStyle"
        :items="[{value: 'page', title: 'page'}, {value: 'page-of', title: 'page / pages'}, {value: 'none', title: 'no page number'}]"
        label="Page Number Style"
        :disabled="props.disabled"
        class="mb-4"
      />
    </div>
    <div v-if="form.form === 'header-create'">
      <s-select
        v-model="form.header.left"
        :items="[ {value: null, title: 'none'}, {value: 'text', title: 'Text'}, {value: 'logo', title: 'Logo'}]"
        label="Header Left"
        :hint="form.header.left === 'logo' ? 'Logo image must be uploaded in assets as logo.png' : ''"
        class="mb-4"
        :disabled="props.disabled"
      />
      <s-select
        v-model="form.header.right"
        :items="[ {value: null, title: 'none'}, {value: 'text', title: 'Text'}, {value: 'logo', title: 'Logo'}]"
        label="Header Right"
        class="mb-4"
        :disabled="props.disabled"
      />
      <s-text-field
        v-model="form.header.backgroundColor"
        label="Header background color (optional)"
        hint="CSS value: #ff0000 or rgb(255, 0, 0) or red"
        class="mb-4"
        :disabled="props.disabled"
      />
    </div>
    <div v-if="form.form === 'toc-create'">
      <s-text-field
        v-model="form.toc.headline"
        label="Headline"
        class="mb-4"
        :disabled="props.disabled"
      />
      <s-select
        v-model="form.toc.variant"
        :items="['default', 'compact']"
        label="ToC Variant"
        hint="Choose between some predefined styles"
        class="mb-4"
        :disabled="props.disabled"
      />
      <s-checkbox
        v-model="form.toc.leader"
        label="Show dot leader (line of dots) between chapter title and page number"
        :disabled="props.disabled"
        class="mb-4"
      />
    </div>
    <div v-if="form.form === 'finding-list-create'">
      <s-text-field
        v-model="form.findingList.headline"
        label="Chapter Headline"
        :disabled="props.disabled"
        class="mb-4"
      />
      <s-select
        v-model="form.findingList.headerVariant"
        :items="['default', 'table']"
        label="Finding List Variant"
        hint="Choose between some predefined styles"
        :disabled="props.disabled"
      />

      <p>
        Markdown fields from the finding field definition will be added to HTML.
        You can add and style the remaining fields afterwards in HTML.
      </p>
    </div>
    <!--<div v-if="form.form === 'page-cover-create'">
      <s-checkbox
        v-model="form.coverPage.hideHeader"
        label="Hide header on page"
        :disabled="props.disabled"
      />
      <s-checkbox
        v-model="form.coverPage.hideFooter"
        label="Hide footer on page"
        :disabled="props.disabled"
      />
    </div>-->
  </div>
</template>

<script setup lang="ts">
import pick from "lodash/pick";
import type { MarkdownProps } from "~/composables/markdown";

const props = defineProps<{
  modelValue: any;
  disabled?: boolean;
} & MarkdownProps>();
const emit = defineEmits<{
  'update:modelValue': [any];
}>();

const markdownProps = computed(() => pick(props, ['disabled', 'lang', 'uploadFile', 'rewriteFileUrl', 'rewriteReferenceLink']));

const form = ref();
watch(() => props.modelValue, () => {
  if (props.modelValue !== form.value) {
    form.value = props.modelValue;
  }
}, { immediate: true });
watch(form, () => emit('update:modelValue', form.value), { deep: true });
</script>

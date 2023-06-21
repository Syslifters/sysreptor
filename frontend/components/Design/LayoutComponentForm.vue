<template>
  <div>
    <div v-if="['headline', 'section-create'].includes(form.form)">
      <s-text-field
        v-model="form.headline.text"
        label="Headline"
        :disabled="disabled"
        class="mb-4"
      />
      <s-select
        v-model.number="form.headline.tag" 
        :items="['h1', 'h2', 'h3', 'h4', 'h5', 'h6']"
        label="Tag"
        :disabled="disabled"
      />
      <s-checkbox
        v-model="form.headline.intoc"
        label="Include in Table of Contents"
        :disabled="disabled"
      />
      <s-checkbox
        v-model="form.headline.numbered"
        label="Prepend chapter number"
        :disabled="disabled"
        class="mb-4"
      />
    </div>
    <div v-if="['markdown-create', 'section-create'].includes(form.form)">
      <s-select 
        v-model="form.markdown.form"
        :items="['text', 'variable']"
        label="Markdown Type"
        :disabled="disabled"
        class="mb-4"
      />
    </div>
    <div v-if="form.form === 'markdown-text' || (['markdown-create', 'section-create'].includes(form.form) && form.markdown.form === 'text')">
      <markdown-field 
        v-model="form.markdown.text" 
        label="Markdown"
        :lang="lang"
        :upload-file="uploadFile"
        :rewrite-file-url="rewriteFileUrl"
        :disabled="disabled"
        class="mb-4"
      />
    </div>
    <div v-if="form.form === 'markdown-variable' || (['markdown-create', 'section-create'].includes(form.form) && form.markdown.form === 'variable')">
      <!-- TODO: autocomplete report/finding variables (ComboBox - allow other values) -->
      <s-text-field
        v-model="form.markdown.variable"
        label="Markdown Variable"
        hint="Variable name of report or finding field (e.g. report.executive_summary, finding.description)"
        :disabled="disabled"
        class="mb-4"
      />
    </div>
    <div v-if="form.form === 'chart-create'" class="mb-4">
      <s-select
        v-model="form.chart.chartType"
        :items="['bar', 'pie', 'doughnut', 'line', 'radar', 'polarArea']"
        label="Chart Type"
        class="mb-4"
        :disabled="disabled"
      />
      <s-text-field
        v-model="form.chart.caption"
        label="Caption"
        :disabled="disabled"
        class="mb-4"
      />
    </div>
    <div v-if="form.form === 'footer-create'">
      <s-text-field
        v-model="form.footer.textLeft"
        label="Footer Text Left (optional)"
        class="mb-4"
        :disabled="disabled"
      />
      <s-text-field
        v-model="form.footer.textCenter"
        label="Footer Text Center (optional)"
        class="mb-4"
        :disabled="disabled"
      />
      <s-select 
        v-model="form.footer.pageNumberStyle"
        :items="[{value: 'page', text: 'page'}, {value: 'page-of', text: 'page / pages'}, {value: 'none', text: 'no page number'}]"
        label="Page Number Style"
        :disabled="disabled"
        class="mb-4"
      />
    </div>
    <div v-if="form.form === 'header-create'">
      <s-select 
        v-model="form.header.left"
        :items="[ {value: null, text: 'none'}, {value: 'text', text: 'Text'}, {value: 'logo', text: 'Logo'}]"
        label="Header Left"
        :hint="form.header.left === 'logo' ? 'Logo image must be uploaded in assets as logo.png' : ''"
        class="mb-4"
        :disabled="disabled"
      />
      <s-select 
        v-model="form.header.right"
        :items="[ {value: null, text: 'none'}, {value: 'text', text: 'Text'}, {value: 'logo', text: 'Logo'}]"
        label="Header Right"
        class="mb-4"
        :disabled="disabled"
      />
      <s-text-field
        v-model="form.header.backgroundColor"
        label="Header background color (optional)"
        hint="CSS value: #ff0000 or rgb(255, 0, 0) or red"
        class="mb-4"
        :disabled="disabled"
      />
    </div>
    <div v-if="form.form === 'toc-create'">
      <s-text-field
        v-model="form.toc.headline"
        label="Headline"
        class="mb-4"
        :disabled="disabled"
      />
      <s-select 
        v-model="form.toc.variant"
        :items="['default', 'compact']"
        label="ToC Variant"
        hint="Choose between some predefined styles"
        class="mb-4"
        :disabled="disabled"
      />
      <s-checkbox
        v-model="form.toc.leader"
        label="Show dot leader (line of dots) between chapter title and page number"
        :disabled="disabled"
        class="mb-4"
      />
    </div>
    <div v-if="form.form === 'finding-list-create'">
      <s-text-field
        v-model="form.findingList.headline"
        label="Chapter Headline"
        :disabled="disabled"
        class="mb-4"
      />
      <s-select 
        v-model="form.findingList.headerVariant"
        :items="['default', 'table']"
        label="Finding List Variant"
        hint="Choose between some predefined styles"
        :disabled="disabled"
      />

      <p>
        Markdown fields from the finding field definition will be added to HTML. 
        You can add and style the remaining fields afterwards in HTML.
      </p>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    value: {
      type: Object,
      required: true,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    lang: {
      type: String,
      default: null,
    },
    uploadFile: {
      type: Function,
      default: null,
    },
    rewriteFileUrl: {
      type: Function,
      default: null,
    },
  },
  data() {
    return {
      form: this.value,
    };
  },
  watch: {
    value() {
      this.form = this.value;
    },
    form: {
      handler() {
        this.$emit('input', this.form);
      },
      deep: true,
    }
  },
}
</script>

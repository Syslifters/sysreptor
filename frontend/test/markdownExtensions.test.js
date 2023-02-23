import { formatMarkdown, renderMarkdownToHtml } from 'reportcreator-markdown';

function codeBlock(content, language = null) {
  return `<pre class="code-block"><code class="${language ? 'language-' + language + ' ' : ''}hljs">${
    content.split('\n')
      .map((l, idx) => `<span class="code-block-line" data-line-number="${idx + 1}">${l}</span>`)
      .join('\n')
  }\n</code></pre>`;
}

describe('Markdown extensions', () => {
  for (const [md, html] of Object.entries({
    // Footnote
    'text^[footnote] text': '<p>text<footnote>footnote</footnote> text</p>',
    'text^[**foot**[note](#ref)] text': '<p>text<footnote><strong>foot</strong><a href="#ref">note</a></footnote> text</p>',
    // Figure
    '![caption _with_ **markdown** `code`](#img)': '<p></p><figure><img src="#img" alt="caption with markdown code"><figcaption>caption <em>with</em> <strong>markdown</strong> <code class="code-inline">code</code></figcaption></figure><p></p>',
    '![](#img)': '<p></p><figure><img src="#img" alt=""></figure><p></p>',
    '![caption](#img){#imgId .imgClass width="50%"}': '<p></p><figure><img src="#img" alt="caption" id="imgId" class="imgClass" style="width:50%;"><figcaption>caption</figcaption></figure><p></p>',
    // Table
    '| cell  |\n| ----- |\n| value |\n\nTable: caption': '<table><thead><tr><th>cell</th></tr></thead><tbody><tr><td>value</td></tr></tbody><caption>caption</caption></table>',
    '| cell  |\n| ----- |\n| value |': '<table><thead><tr><th>cell</th></tr></thead><tbody><tr><td>value</td></tr></tbody></table>',
    // Attrs
    '[link](#ref){#id}': '<p><a href="#ref" id="id">link</a></p>',
    '[link](#ref){.class1 .class2 .class3}': '<p><a href="#ref" class="class1 class2 class3">link</a></p>',
    '[link](#ref){width="15cm" height=10cm}': '<p><a href="#ref" style="width:15cm;height:10cm;">link</a></p>',
    '[link](#ref){style="color: red" data-attr="test"}': '<p><a href="#ref" style="color: red" data-attr="test">link</a></p>',
    '[link](#ref){width="15cm" style="color:red"}': '<p><a href="#ref" style="color:red;width:15cm;">link</a></p>',
    // Template varaibles
    '{{ var }}': '<p>{{ var }}</p>',
    'text **{{ var }}** text': '<p>text <strong>{{ var }}</strong> text</p>',
    'text {{ var **with** _code_ `code` }} text': '<p>text {{ var **with** _code_ `code` }} text</p>',
    'text {{ var with curly braces {a: "abc", b: "def"}[var] }} text': '<p>text {{ var with curly braces {a: "abc", b: "def"}[var] }} text</p>',
    'text {no var}} {{ no var } text': '<p>text {no var}} {{ no var } text</p>',
    'text <template v-if="var">{{ var }} text</template> text': '<p>text <span v-if="var">{{ var }} text</span> text</p>',
    'text <span v-for="v in var">{{ v }}</span> text': '<p>text <span v-for="v in var">{{ v }}</span> text</p>',
    // TO-DOs
    'TODO: text': '<p><span class="todo">TODO</span>: text</p>',
    'text **with _TODOs_ in** it': '<p>text <strong>with <em><span class="todo">TODO</span>s</em> in</strong> it</p>',
    'To-Do': '<p><span class="todo">To-Do</span></p>',
    'TO**DO**': '<p>TO<strong>DO</strong></p>',
    '`TODO`': '<p><code class="code-inline">TODO</code></p>',
    // Code block highlighting
    '```\nprint("hello world")\n```': codeBlock('print("hello world")'),
    '```python\nprint("hello world")\n```': codeBlock('<span class="hljs-built_in">print</span>(<span class="hljs-string">"hello world"</span>)', 'python'),
    '```python highlight-manual\npr§§int("hel§§lo world")\n```': codeBlock('<span class="hljs-built_in">pr</span><mark><span class="hljs-built_in">int</span>(<span class="hljs-string">"hel</span></mark><span class="hljs-string">lo world"</span>)', 'python'),
    '```python highlight-manual\npr§<mark><strong>BEGIN</strong><em>§int("hel§</em><strong>END</strong></mark>§lo world")\n```': codeBlock('<span class="hljs-built_in">pr</span><mark><strong>BEGIN</strong><em><span class="hljs-built_in">int</span>(<span class="hljs-string">"hel</span></em><strong>END</strong></mark><span class="hljs-string">lo world"</span>)', 'python'),
    '```\npr§§int("hel§§lo world")\n```': codeBlock('pr§§int("hel§§lo world")'),
    '```none highlight-manual="|"\npr||int("hel||lo world")\n```': codeBlock('pr<mark>int("hel</mark>lo world")', 'none'),
  })) {
    test(md, () => {
      expect(renderMarkdownToHtml(md).trim()).toBe(html);
      const formattedMd = formatMarkdown(md).trim('\n');
      expect(formattedMd).toBe(md);
    });
  }
});

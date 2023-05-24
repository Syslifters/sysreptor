import { formatMarkdown, renderMarkdownToHtml } from 'reportcreator-markdown';

function codeBlock(content, language = null) {
  return `<pre class="code-block"><code class="${language ? 'language-' + language + ' ' : ''}hljs">${
    content.split('\n')
      .map((l, idx) => `<span class="code-block-line" data-line-number="${idx + 1}">${l}</span>`)
      .join('\n')
  }\n</code></pre>`;
}

describe('Markdown extensions', () => {
  for (const [md, expected] of Object.entries({
    // Footnote
    'text^[footnote] text': '<p>text<footnote>footnote</footnote> text</p>',
    'text^[**foot**[note](https://example.com)] text': '<p>text<footnote><strong>foot</strong><a href="https://example.com" target="_blank" rel="nofollow noopener noreferrer">note</a></footnote> text</p>',
    // Figure
    '![caption _with_ **markdown** `code`](#img)': '<p></p><figure><img src="#img" alt="caption with markdown code"><figcaption>caption <em>with</em> <strong>markdown</strong> <code class="code-inline">code</code></figcaption></figure><p></p>',
    '![](#img)': '<p></p><figure><img src="#img" alt=""></figure><p></p>',
    '![caption](#img){#imgId .imgClass width="50%"}': '<p></p><figure><img src="#img" alt="caption" id="imgId" class="imgClass" style="width:50%;"><figcaption>caption</figcaption></figure><p></p>',
    // Table
    '| cell  |\n| ----- |\n| value |\n\nTable: caption': '<table><thead><tr><th>cell</th></tr></thead><tbody><tr><td>value</td></tr></tbody><caption>caption</caption></table>',
    '| cell  |\n| ----- |\n| value |': '<table><thead><tr><th>cell</th></tr></thead><tbody><tr><td>value</td></tr></tbody></table>',
    // Attrs
    '[link](https://example.com){#id}': '<p><a href="https://example.com" id="id" target="_blank" rel="nofollow noopener noreferrer">link</a></p>',
    '[link](https://example.com){.class1 .class2 .class3}': '<p><a href="https://example.com" class="class1 class2 class3" target="_blank" rel="nofollow noopener noreferrer">link</a></p>',
    '[link](https://example.com){width="15cm" height=10cm}': '<p><a href="https://example.com" style="width:15cm;height:10cm;" target="_blank" rel="nofollow noopener noreferrer">link</a></p>',
    '[link](https://example.com){style="color: red" data-attr="test"}': '<p><a href="https://example.com" style="color: red" data-attr="test" target="_blank" rel="nofollow noopener noreferrer">link</a></p>',
    '[link](https://example.com){width="15cm" style="color:red"}': '<p><a href="https://example.com" style="color:red;width:15cm;" target="_blank" rel="nofollow noopener noreferrer">link</a></p>',
    '# Heading {#id .class style="color:red"}': '<h1 id="id" class="class" style="color:red">Heading </h1>',
    '## Heading{#id}': '<h2 id="id">Heading</h2>',
    '### Heading [link](https://example.com){.class}': '<h3>Heading <a href="https://example.com" class="class" target="_blank" rel="nofollow noopener noreferrer">link</a></h3>',
    '#### Heading\n{#id}': { html: '<h4>Heading</h4>\n<p>{#id}</p>', formatted: '#### Heading\n\n{#id}' },
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
    // Nested elements
    '![caption^[footnote [link](https://example.com)]](/img.png)': '<p></p><figure><img src="/img.png" alt="captionfootnote link"><figcaption>caption<footnote>footnote <a href="https://example.com" target="_blank" rel="nofollow noopener noreferrer">link</a></footnote></figcaption></figure><p></p>',
    '![caption^[footnote [partial]](/img.png)': {
      html: '<p></p><figure><img src="/img.png" alt="captionfootnote [partial"><figcaption>caption<footnote>footnote [partial</footnote></figcaption></figure><p></p>',
      formatted: '![caption^[footnote \\[partial]](/img.png)',
    },
    // Reference links
    '[](#ref)': '<p><ref to="ref"></ref></p>',
    '[Reference](#ref)': '<p><ref to="ref">Reference</ref></p>',
    '[](#ref){.class}': '<p><ref class="class" to="ref"></ref></p>',
    // Underline
    'text <u>underline</u> text': '<p>text <u>underline</u> text</p>',
    // Self-closing tags
    'text\n\n<pagebreak />\n\ntext': '<p>text</p>\n<pagebreak></pagebreak>\n<p>text</p>',
    'text <ref to="ref" data-custom-attr="asf" /> text': '<p>text <ref to="ref" data-custom-attr="asf"></ref> text</p>',
  }).map(([md, expected]) => [md, typeof expected === 'string' ? { html: expected, formatted: md } : expected])) {
    test(md, () => {
      expect(renderMarkdownToHtml(md).trim()).toBe(expected.html);
      const formattedMd = formatMarkdown(md).trim('\n');
      expect(formattedMd).toBe(expected.formatted);
    });
  }
});

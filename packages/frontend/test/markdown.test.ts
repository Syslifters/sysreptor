import { describe, test, expect } from 'vitest'
import { renderMarkdownToHtml } from '@sysreptor/markdown';
import fs from 'fs';
import path from 'path';
import { formatHtml } from '@sysreptor/markdown/mdext';

type CommonMarkTestCase = {
  section: string;
  example: number;
  markdown: string;
  html: string;
};

function normalizeHtml(html: string): string {
  let out = html;

  // Remove attributes or rehype extensions
  for (const rm of [
    ' target="_blank"',
    ' rel="nofollow noopener noreferrer"',
    ' class="code-inline"',
    ' class="code-block"',
    ' class="contains-task-list"',
    ' class="task-list-item"',
  ]) {
    out = out.replaceAll(rm, '')
  }

  for (const [oldValue, newValue] of [
    ['<ref ', '<a '],
    [' to="', ' href="#'],
    ['</ref>', '</a>'],
    [' class="hljs"', ''],
    [' startline="3"', ''],
    [/class="([^"]*)hljs([^"]*)"/g, 'class="$1$2"'],
    [/<code([^>]*)>(.*)<\/code>/gs, (_: any, p1: string, p2: string) => `<code${p1}>${p2.replaceAll(/<span[^>]+>/g, '').replaceAll('</span>', '')}</code>`],
  ] as any) {
    out = out.replaceAll(oldValue, newValue);
  }

  out = formatHtml(out).trim();

  // Remove whitespace
  out = out.replaceAll(/>\s+</gs, '><');

  return out;
}

function markdownTestCase(testCase: CommonMarkTestCase) {
  test(`${testCase.section}: example ${testCase.example} (${testCase.markdown})`, () => {
    const renderedHtml = renderMarkdownToHtml({ text: testCase.markdown });
    const normalizedRenderedHtml = normalizeHtml(renderedHtml);
    const normalizedExpectedHtml = normalizeHtml(testCase.html);

    console.log('HTML', testCase.html);
    
    expect(normalizedRenderedHtml).toBe(normalizedExpectedHtml);
  });
}

describe('CommonMark', () => {
  const skipExamples = [
    // Raw HTML: parsed by rehype instead of passthrough, mainly affects invalid/incomplete HTML
    171, 187, 344, 476, 477, 494, 613, 614, 615, 616, 630, 631, 642, 643,
    // Indented code blocks: disabled
    107, 108, 109, 110, 111, 112,  113, 114, 115, 116, 117, 118,
    1, 2, 3, 5, 6, 7, 8, 18, 36, 48, 69, 85, 100, 134, 183, 
    184, 191, 211, 225, 231, 236, 252, 253, 254, 257, 264, 
    270, 271, 272, 273, 274, 278, 286, 287, 288, 289, 290, 309, 313, 
    // Different handling of leading whitespace, because of disabled indented code blocks
    49, 70, 87, 137, 238, 312,
    // Different handling of unicode characters: unicode whitespace is treated the same as normal whitespace
    25, 333, 353, 507, 
    // Different image handling: allow markdown in label/caption, render as <figure> with <figcaption>
    517, 520, 531, 572, 574, 575, 578, 579, 580, 581,
  ];

  const commonMarkTestCases = JSON.parse(fs.readFileSync(path.join(__dirname, 'commonmark-spec0.31.2.json'), 'utf-8')) as CommonMarkTestCase[];
  for (const testCase of commonMarkTestCases) {
    if (skipExamples.includes(testCase.example)) {
      continue;
    }

    markdownTestCase(testCase);
  }
})

describe('GFM', () => {
  const gfmTestCases = JSON.parse(fs.readFileSync(path.join(__dirname, 'gfm-spec0.29.json'), 'utf-8')) as CommonMarkTestCase[];
  for (const testCase of gfmTestCases) {
    markdownTestCase(testCase);
  }
})


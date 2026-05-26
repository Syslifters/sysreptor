import { execFileSync } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import type MarkdownIt from 'markdown-it'

const DOCS_VITE_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..')
const EXPAND_SCRIPT = path.join(DOCS_VITE_ROOT, 'scripts', 'python_autodoc.py')

const AUTODOC_PATH_RE = /python-library\/(api|dataclasses)\//

function isAutodocPage(filePath: string | undefined): boolean {
  if (!filePath) return false
  return AUTODOC_PATH_RE.test(filePath.replace(/\\/g, '/'))
}

function isEnabled(): boolean {
  const flag = process.env.VITEPRESS_PYTHON_AUTODOC
  return flag === undefined || flag === '' || !/^(0|false|no|off)$/i.test(flag)
}

function expandMarkdown(source: string): string {
  return execFileSync('python3', [EXPAND_SCRIPT, 'expand'], {
    cwd: DOCS_VITE_ROOT,
    input: source,
    encoding: 'utf-8',
    maxBuffer: 32 * 1024 * 1024,
  })
}

/**
 * Expands mkdocstrings-style `::: reptor...` blocks at build/dev time by calling
 * scripts/python_autodoc.py (requires reptor + griffe installed in the environment).
 */
export function pythonAutodocPlugin(md: MarkdownIt): void {
  md.core.ruler.before('normalize', 'python-autodoc', (state) => {
    if (!isEnabled() || !isAutodocPage(state.env.path ?? state.env.filePath)) {
      return
    }
    if (!/^::: /m.test(state.src)) {
      return
    }
    try {
      state.src = expandMarkdown(state.src)
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error)
      throw new Error(
        `Failed to expand Python autodoc blocks (is reptor installed?). ${message}`,
      )
    }
  })
}

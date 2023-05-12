export function addRemarkExtension(self, micromarkExtensions, fromMarkdownExtensions, toMarkdownExtensions) {
  const data = self.data();

  add('micromarkExtensions', micromarkExtensions);
  add('fromMarkdownExtensions', fromMarkdownExtensions);
  add('toMarkdownExtensions', toMarkdownExtensions);

  /**
  * @param {string} field
  * @param {unknown} value
  */
  function add(field, value) {
    if (!value) {
      return;
    }

    const list = /** @type {unknown[]} */ (
      // Other extensions
      /* c8 ignore next 2 */
      data[field] ? data[field] : (data[field] = [])
    )

    list.push(value)
  }
}


export function assert(bool, msg) {
  if (!bool) {
    throw new Error(msg);
  }
}
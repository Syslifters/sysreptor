export function addRemarkExtension(self, micromarkExtensions, fromMarkdownExtensions, toMarkdownExtensions) {
  const data = self.data();

  add('micromarkExtensions', micromarkExtensions);
  add('fromMarkdownExtensions', fromMarkdownExtensions);
  add('toMarkdownExtensions', toMarkdownExtensions);

  function add(field, value) {
    if (!value) {
      return;
    }

    if (!data[field]) {
      data[field] = [];
    }
    data[field].push(value)
  }
}


export function assert(bool, msg) {
  if (!bool) {
    throw new Error(msg);
  }
}
// Most micromark-* and rehype-* packages live in a monorepo with a single license at the top level, no separate license for each sub-package
// https://github.com/micromark/micromark
// https://github.com/rehypejs/rehype
const micromarkLicenseText = `(The MIT License)

Copyright (c) 2020 Titus Wormer <tituswormer@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
'Software'), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.`;

const rehypeLicenseText = `(The MIT License)

Copyright (c) 2016 Titus Wormer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.`;


export const licenseTextOverrides = {
  'micromark': micromarkLicenseText,
  'micromark-util-symbol': micromarkLicenseText,
  'micromark-util-chunked': micromarkLicenseText,
  'micromark-util-resolve-all': micromarkLicenseText,
  'micromark-util-classify-character': micromarkLicenseText,
  'micromark-util-character': micromarkLicenseText,
  'micromark-factory-space': micromarkLicenseText,
  'micromark-factory-whitespace': micromarkLicenseText,
  'micromark-util-subtokenize': micromarkLicenseText,
  'micromark-util-combine-extensions': micromarkLicenseText,
  'micromark-core-commonmark': micromarkLicenseText,
  'micromark-factory-label': micromarkLicenseText,
  'micromark-util-normalize-identifier': micromarkLicenseText,
  'micromark-factory-destination': micromarkLicenseText,
  'micromark-factory-title': micromarkLicenseText,
  'micromark-util-html-tag-name': micromarkLicenseText,
  'micromark-util-decode-string': micromarkLicenseText,
  'micromark-util-decode-numeric-character-reference': micromarkLicenseText,
  'micromark-util-sanitize-uri': micromarkLicenseText,
  'micromark-util-encode': micromarkLicenseText,

  'rehype-stringify': rehypeLicenseText,
  'rehype-parse': rehypeLicenseText,
  'hast-util-to-string': rehypeLicenseText,

  'format': `The MIT License (MIT)
Copyright © 2022 Sami Samhuri, http://samhuri.net <sami@samhuri.net>
  
Permission is hereby granted, free of charge, to any person obtaining 
a copy of this software and associated documentation files (the 
“Software”), to deal in the Software without restriction, including 
without limitation the rights to use, copy, modify, merge, publish, 
distribute, sublicense, and/or sell copies of the Software, and to 
permit persons to whom the Software is furnished to do so, subject to 
the following conditions:
  
The above copyright notice and this permission notice shall be 
included in all copies or substantial portions of the Software.
  
THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, 
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF 
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. 
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY 
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, 
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE 
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.`,
  'inline-style-parser': `MIT. See [license](https://github.com/reworkcss/css/blob/v2.2.4/LICENSE) from original project.`,
};
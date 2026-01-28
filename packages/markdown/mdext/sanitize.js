import { defaultSchema } from 'rehype-sanitize';
import { merge } from 'lodash-es';

const allClasses = ['className', /^.*$/];

const svgCommonPresentationAttrs = [
  'alignment-baseline', 'baseline-shift', 'clip', 'clip-path', 'clip-rule', 'color', 'color-interpolation', 'color-rendering', 'cursor', 
  'direction', 'display', 'fill', 'fill-opacity', 'fill-rule', 'filter', 'image-rendering', 'mask', 'opacity', 'overflow', 
  'pointer-events', 'shape-rendering', 'stroke', 'stroke-dasharray', 'stroke-dashoffset', 'stroke-linecap', 'stroke-linejoin', 
  'stroke-miterlimit', 'stroke-opacity', 'stroke-width', 'text-rendering', 'transform', 'unicode-bidi', 'visibility'];
const svgFontAttrs = ['font-family', 'font-size', 'font-size-adjust', 'font-stretch', 'font-style', 'font-variant', 'font-weight'];
const svgTextAttrs = ['kerning', 'letter-spacing', 'text-anchor', 'text-decoration', 'word-spacing', 'writing-mode'];
const svgAttributes = {
  'animate': [allClasses, 'id', 'attributeName', 'attributeType', 'begin', 'dur', 'end', 'fill', 'from', 'repeatCount', 'repeatDur', 'to', 'values'],
  'animateMotion': [allClasses, 'id', 'begin', 'dur', 'end', 'fill', 'path', 'repeatCount', 'repeatDur'],
  'animateTransform': [allClasses, 'id', 'attributeName', 'begin', 'dur', 'end', 'fill', 'from', 'repeatCount', 'repeatDur', 'to', 'type', 'values'],
  'circle': [allClasses, ...svgCommonPresentationAttrs, 'cx', 'cy', 'id', 'r', 'requiredFeatures', 'systemLanguage'],
  'clipPath': [allClasses, ...svgCommonPresentationAttrs, 'clipPathUnits', 'id'],
  'defs': [],
  'style': ['type'],
  'desc': [],
  'ellipse': [allClasses, ...svgCommonPresentationAttrs, 'cx', 'cy', 'id', 'requiredFeatures', 'rx', 'ry', 'systemLanguage'],
  'feBlend': [allClasses, 'id', 'in', 'in2', 'mode', 'result'],
  'feColorMatrix': [allClasses, 'id', 'in', 'result', 'type', 'values'],
  'feComponentTransfer': [allClasses, 'id', 'in', 'result'],
  'feComposite': [allClasses, 'id', 'in', 'in2', 'k1', 'k2', 'k3', 'k4', 'operator', 'result'],
  'feConvolveMatrix': [allClasses, 'id', 'in', 'order', 'kernelMatrix', 'divisor', 'bias', 'targetX', 'targetY', 'edgeMode', 'preserveAlpha', 'result'],
  'feDiffuseLighting': [allClasses, 'id', 'in', 'surfaceScale', 'diffuseConstant', 'result'],
  'feDisplacementMap': [allClasses, 'id', 'in', 'in2', 'scale', 'xChannelSelector', 'yChannelSelector', 'result'],
  'feDistantLight': [allClasses, 'id', 'azimuth', 'elevation'],
  'feFlood': [allClasses, 'id', 'flood-color', 'flood-opacity', 'result'],
  'feFuncA': [allClasses, 'id', 'type', 'tableValues', 'slope', 'intercept', 'amplitude', 'exponent', 'offset'],
  'feFuncB': [allClasses, 'id', 'type', 'tableValues', 'slope', 'intercept', 'amplitude', 'exponent', 'offset'],
  'feFuncG': [allClasses, 'id', 'type', 'tableValues', 'slope', 'intercept', 'amplitude', 'exponent', 'offset'],
  'feFuncR': [allClasses, 'id', 'type', 'tableValues', 'slope', 'intercept', 'amplitude', 'exponent', 'offset'],
  'feGaussianBlur': [allClasses, 'color-interpolation-filters', 'id', 'in', 'requiredFeatures', 'result', 'stdDeviation'],
  'feMerge': [allClasses, 'id', 'result'],
  'feMergeNode': [allClasses, 'id', 'in'],
  'feMorphology': [allClasses, 'id', 'in', 'operator', 'radius', 'result'],
  'feOffset': [allClasses, 'id', 'in', 'dx', 'dy', 'result'],
  'fePointLight': [allClasses, 'id', 'x', 'y', 'z'],
  'feSpecularLighting': [allClasses, 'id', 'in', 'surfaceScale', 'specularConstant', 'specularExponent', 'result'],
  'feSpotLight': [allClasses, 'id', 'x', 'y', 'z', 'pointsAtX', 'pointsAtY', 'pointsAtZ', 'specularExponent', 'limitingConeAngle'],
  'feTile': [allClasses, 'id', 'in', 'result'],
  'feTurbulence': [allClasses, 'id', 'baseFrequency', 'numOctaves', 'seed', 'stitchTiles', 'type', 'result'],
  'filter': [allClasses, 'color-interpolation-filters', 'filterRes', 'filterUnits', 'height', 'id', 'primitiveUnits', 'requiredFeatures', 'width', 'x', 'y'],
  'g': [allClasses, ...svgCommonPresentationAttrs, ...svgFontAttrs, ...svgTextAttrs, 'id', 'requiredFeatures', 'systemLanguage'],
  'line': [allClasses, ...svgCommonPresentationAttrs, 'id', 'marker-end', 'marker-mid', 'marker-start', 'requiredFeatures', 'systemLanguage', 'x1', 'x2', 'y1', 'y2'],
  'linearGradient': [allClasses, 'color', 'color-interpolation', 'color-rendering', 'gradientTransform', 'gradientUnits', 'id', 'requiredFeatures', 'spreadMethod', 'systemLanguage', 'x1', 'x2', 'y1', 'y2'],
  'marker': ['id', allClasses, ...svgCommonPresentationAttrs, 'markerHeight', 'markerUnits', 'markerWidth', 'orient', 'preserveAspectRatio', 'refX', 'refY', 'systemLanguage', 'viewBox'],
  'mask': [allClasses, ...svgCommonPresentationAttrs, 'height', 'id', 'maskContentUnits', 'maskUnits', 'width', 'x', 'y'],
  'metadata': [allClasses, 'id'],
  'path': [allClasses, ...svgCommonPresentationAttrs, 'd', 'id', 'marker-end', 'marker-mid', 'marker-start', 'pathLength', 'requiredFeatures', 'systemLanguage'],
  'pattern': [allClasses, ...svgCommonPresentationAttrs, 'height', 'id', 'patternContentUnits', 'patternTransform', 'patternUnits', 'preserveAspectRatio', 'requiredFeatures', 'systemLanguage', 'viewBox', 'width', 'x', 'y'],
  'polygon': [allClasses, ...svgCommonPresentationAttrs, 'id', 'marker-end', 'marker-mid', 'marker-start', 'points', 'requiredFeatures', 'systemLanguage'],
  'polyline': [allClasses, ...svgCommonPresentationAttrs, 'id', 'marker-end', 'marker-mid', 'marker-start', 'points', 'requiredFeatures', 'systemLanguage'],
  'radialGradient': [allClasses, 'color', 'color-interpolation', 'color-rendering', 'cx', 'cy', 'fx', 'fy', 'gradientTransform', 'gradientUnits', 'id', 'r', 'requiredFeatures', 'spreadMethod', 'systemLanguage'],
  'rect': [allClasses, ...svgCommonPresentationAttrs, 'height', 'id', 'requiredFeatures', 'rx', 'ry', 'systemLanguage', 'width', 'x', 'y'],
  'set': [allClasses, 'id', 'attributeName', 'to', 'begin', 'dur', 'end', 'fill'],
  'stop': [allClasses, 'color', 'color-interpolation', 'color-rendering', 'id', 'offset', 'opacity', 'requiredFeatures', 'stop-color', 'stop-opacity', 'systemLanguage'],
  'svg': [allClasses, ...svgCommonPresentationAttrs, 'height', 'id', 'preserveAspectRatio', 'requiredFeatures', 'systemLanguage', 'viewBox', 'width', 'x', 'xmlns', 'xmlns:se', 'y'],
  'switch': [allClasses, ...svgCommonPresentationAttrs, 'id', 'requiredFeatures', 'systemLanguage'],
  'symbol': [allClasses, ...svgCommonPresentationAttrs, ...svgFontAttrs, ...svgTextAttrs, 'id', 'preserveAspectRatio', 'requiredFeatures', 'systemLanguage', 'viewBox'],
  'text': [allClasses, ...svgCommonPresentationAttrs, ...svgFontAttrs, ...svgTextAttrs, 'dominant-baseline', 'id', 'requiredFeatures', 'systemLanguage', 'x', 'xml:space', 'y'],
  'textPath': [allClasses, ...svgCommonPresentationAttrs, ...svgFontAttrs, ...svgTextAttrs, 'dominant-baseline', 'id', 'method', 'requiredFeatures', 'spacing', 'startOffset', 'systemLanguage'],
  'title': [],
  'tspan': [allClasses, ...svgCommonPresentationAttrs, ...svgFontAttrs, ...svgTextAttrs, 'dominant-baseline', 'dx', 'dy', 'id', 'requiredFeatures', 'rotate', 'systemLanguage', 'textLength', 'x', 'xml:space', 'y'],
  'use': [allClasses, ...svgCommonPresentationAttrs, 'height', 'id', 'width', 'x', 'y'],
};

export const rehypeSanitizeSchema = merge({}, defaultSchema, {
  allowComments: true,
  clobberPrefix: null,
  tagNames: [
    // Custom components
    'footnote', 'template', 'ref', 'pagebreak', 'markdown', 'mermaid-diagram', 'math-latex', 'qrcode',
    // Regular HTML tags not included in default schema
    'figure', 'figcaption', 'caption', 'mark', 'u',
    'abbr', 'bdo', 'cite', 'dfn', 'time', 'var', 'wbr',
    // SVG tags
    ...Object.keys(svgAttributes),
  ].concat(defaultSchema.tagNames),
  attributes: {
    '*': ['className', 'style', 'data*', 'v-if', 'v-else-if', 'v-else', 'v-for', 'v-bind', 'v-on', 'v-show', 'v-pre', 'v-text'].concat(defaultSchema.attributes['*']),
    'a': ['download', 'target', 'rel', allClasses].concat(defaultSchema.attributes['a']),
    'img': ['loading'].concat(defaultSchema.attributes['img']),
    'code': [allClasses].concat(defaultSchema.attributes['code']),
    'h2': [allClasses].concat(defaultSchema.attributes['h2']),
    'ul': [allClasses].concat(defaultSchema.attributes['ul']),
    'ol': [allClasses].concat(defaultSchema.attributes['ol']),
    'li': [allClasses].concat(defaultSchema.attributes['li']),
    'section': [allClasses].concat(defaultSchema.attributes['section']),
    'input': ['checked'].concat(defaultSchema.attributes['input']),
    'ref': ['to', ':to'],
    'markdown': ['text', ':text'],
    'math-latex': ['display-mode', ':display-mode', 'text', ':text'],
    // SVG
    ...svgAttributes,
  }
});


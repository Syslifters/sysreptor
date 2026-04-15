import { clamp } from 'lodash-es';
import { Canvas, Rect, Point, util as fabricUtil } from 'fabric';

type Pixel01 = { r: number; g: number; b: number };
type ViewportRect = { left: number; top: number; width: number; height: number };
type SrcStripe =
  | { dir: 'h'; img: ImageData; left: number; y: number; width: number } // horizontal 1px stripe
  | { dir: 'v'; img: ImageData; x: number; top: number; height: number }; // vertical 1px stripe

type SrcFringeStripes = Partial<Record<'top' | 'bottom' | 'left' | 'right', SrcStripe>>;
type FringeAvailability = {
  hasTop: boolean;
  hasBottom: boolean;
  hasLeft: boolean;
  hasRight: boolean;
  topY: number;
  bottomY: number;
  leftX: number;
  rightX: number;
  rectL: number;
  rectT: number;
  rectR: number;
  rectB: number;
};

function getViewportRect(c: Canvas, obj: Rect, w: number, h: number): ViewportRect | null {
  // Compute the rect geometry in viewport pixel coordinates, so interactive scaling stays correct.
  const vpt = c.viewportTransform ?? [1, 0, 0, 1, 0, 0];
  const m = fabricUtil.multiplyTransformMatrices(vpt, obj.calcTransformMatrix());
  const tl = new Point(-w / 2, -h / 2).transform(m);
  const br = new Point(w / 2, h / 2).transform(m);
  const left = Math.min(tl.x, br.x);
  const top = Math.min(tl.y, br.y);
  const width = Math.abs(br.x - tl.x);
  const height = Math.abs(br.y - tl.y);
  if (!width || !height) {
    return null;
  }
  return { left, top, width, height };
}

function getFringes(rect: ViewportRect, srcW: number, srcH: number): FringeAvailability {
  const rectL = clamp(Math.floor(rect.left), 0, srcW - 1);
  const rectT = clamp(Math.floor(rect.top), 0, srcH - 1);
  const rectR = clamp(Math.ceil(rect.left + rect.width) - 1, 0, srcW - 1);
  const rectB = clamp(Math.ceil(rect.top + rect.height) - 1, 0, srcH - 1);

  const topY = rectT - 1;
  const bottomY = rectB + 1;
  const leftX = rectL - 1;
  const rightX = rectR + 1;

  return {
    rectL,
    rectT,
    rectR,
    rectB,
    topY,
    bottomY,
    leftX,
    rightX,
    hasTop: topY >= 0,
    hasBottom: bottomY < srcH,
    hasLeft: leftX >= 0,
    hasRight: rightX < srcW,
  };
}

function fillClippedGrey(ctx: CanvasRenderingContext2D, w: number, h: number) {
  ctx.save();
  ctx.beginPath();
  ctx.rect(-w / 2, -h / 2, w, h);
  ctx.clip();
  ctx.fillStyle = 'rgb(128,128,128)';
  ctx.fillRect(-w / 2, -h / 2, w, h);
  ctx.restore();
}

function clampInt(n: unknown, min: number, max: number) {
  const v = typeof n === 'number' ? n : Number.NaN;
  if (!Number.isFinite(v)) return null;
  return clamp(Math.round(v), min, max);
}

function mulberry32(seed: number) {
  let t = seed >>> 0;
  return () => {
    t += 0x6D2B79F5;
    let x = t;
    x = Math.imul(x ^ (x >>> 15), x | 1);
    x ^= x + Math.imul(x ^ (x >>> 7), x | 61);
    return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
  };
}

function createRng(seed: number) {
  const rand = mulberry32(seed);
  function randn(mean = 0, std = 1) {
    // Box-Muller transform
    let u = 0;
    let v = 0;
    while (u === 0) u = rand();
    while (v === 0) v = rand();
    const z = Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
    return mean + z * std;
  }
  return { randn };
}

function ensureEffectCanvasSize(
  canvas: HTMLCanvasElement,
  prev: { w: number; h: number } | null,
  w: number,
  h: number,
) {
  if (!prev || prev.w !== w || prev.h !== h) {
    canvas.width = w;
    canvas.height = h;
    return { w, h };
  }
  return prev;
}

function getStripePixel01(stripe: SrcStripe, x: number, y: number): Pixel01 {
  let i = 0;
  if (stripe.dir === 'h') {
    i = ((x - stripe.left) * 4) | 0;
  } else {
    i = ((y - stripe.top) * 4) | 0;
  }
  const d = stripe.img.data;
  return { r: (d[i] ?? 0) / 255, g: (d[i + 1] ?? 0) / 255, b: (d[i + 2] ?? 0) / 255 };
}

type FringeCandidate = 'top' | 'bottom' | 'left' | 'right';
const FRINGE_CANDIDATES: Record<FringeCandidate, readonly FringeCandidate[]> =
  {
    top: ['top', 'bottom', 'left', 'right'],
    bottom: ['bottom', 'top', 'left', 'right'],
    left: ['left', 'right', 'top', 'bottom'],
    right: ['right', 'left', 'top', 'bottom'],
  };

function isFringeAvailable(f: FringeAvailability, which: FringeCandidate) {
  switch (which) {
    case 'top':
      return f.hasTop;
    case 'bottom':
      return f.hasBottom;
    case 'left':
      return f.hasLeft;
    case 'right':
      return f.hasRight;
  }
}

function sampleFringePixel01(args: {
  fringes: FringeAvailability;
  stripes: SrcFringeStripes;
  samplingNoiseStd: number;
  randn: (mean?: number, std?: number) => number;
  preferred: 'top' | 'bottom' | 'left' | 'right';
  horizontal: number;
  vertical: number;
}) {
  const { fringes, stripes, samplingNoiseStd, randn, preferred, horizontal, vertical } = args;
  const { rectL, rectT, rectR, rectB, topY, bottomY, leftX, rightX } = fringes;

  for (const which of FRINGE_CANDIDATES[preferred]) {
    if (!isFringeAvailable(fringes, which)) continue;
    const stripe = stripes[which];
    if (!stripe) continue;

    const jitter = randn(0, samplingNoiseStd);
    if (which === 'top') {
      const x = clamp(Math.round(horizontal * (rectR - rectL + 1) + rectL + jitter), rectL, rectR);
      return getStripePixel01(stripe, x, topY);
    }
    if (which === 'bottom') {
      const x = clamp(Math.round(horizontal * (rectR - rectL + 1) + rectL + jitter), rectL, rectR);
      return getStripePixel01(stripe, x, bottomY);
    }
    if (which === 'left') {
      const y = clamp(Math.round(vertical * (rectB - rectT + 1) + rectT + jitter), rectT, rectB);
      return getStripePixel01(stripe, leftX, y);
    }
    // right
    const y = clamp(Math.round(vertical * (rectB - rectT + 1) + rectT + jitter), rectT, rectB);
    return getStripePixel01(stripe, rightX, y);
  }

  // Should not happen, but return neutral grey.
  return { r: 0.5, g: 0.5, b: 0.5 };
}

function renderPixelation(args: {
  ctx: CanvasRenderingContext2D;
  ectx: CanvasRenderingContext2D;
  effectCanvas: HTMLCanvasElement;
  effectW: number;
  effectH: number;
  w: number;
  h: number;
  noiseStd: number;
  fringes: FringeAvailability;
  stripes: SrcFringeStripes;
  samplingNoiseStd: number;
}) {
  const { ctx, ectx, effectCanvas, effectW, effectH, w, h, noiseStd, fringes, stripes, samplingNoiseStd } = args;
  const out = ectx.createImageData(effectW, effectH);

  ctx.save();
  ctx.beginPath();
  ctx.rect(-w / 2, -h / 2, w, h);
  ctx.clip();

  // Build pseudo-pixelation effect image (low-res), then scale it to cover the rect.
  // This never reads pixels inside the rect: only top/bottom/left/right fringe samples.
  const { randn } = createRng(42);
  for (let x = 0; x < effectW; x++) {
    for (let y = 0; y < effectH; y++) {
      const horizontal = effectW === 1 ? 0.5 : x / effectW;
      const vertical = effectH === 1 ? 0.5 : y / effectH;

      const top = sampleFringePixel01({ fringes, stripes, samplingNoiseStd, randn, preferred: 'top', horizontal, vertical });
      const bottom = sampleFringePixel01({ fringes, stripes, samplingNoiseStd, randn, preferred: 'bottom', horizontal, vertical });
      const left = sampleFringePixel01({ fringes, stripes, samplingNoiseStd, randn, preferred: 'left', horizontal, vertical });
      const right = sampleFringePixel01({ fringes, stripes, samplingNoiseStd, randn, preferred: 'right', horizontal, vertical });

      // Bias between horizontal vs vertical interpolation.
      const weightH = (Math.min(x, effectW - x) / effectW) - (Math.min(y, effectH - y) / effectH) + 0.5;
      const weightV = 1 - weightH;

      const n = randn(0, noiseStd);
      const rgb: [number, number, number] = [0, 0, 0];
      for (let i = 0; i < 3; i++) {
        const l = i === 0 ? left.r : i === 1 ? left.g : left.b;
        const r = i === 0 ? right.r : i === 1 ? right.g : right.b;
        const t = i === 0 ? top.r : i === 1 ? top.g : top.b;
        const b = i === 0 ? bottom.r : i === 1 ? bottom.g : bottom.b;

        const c =
          // horizontal interpolation
          weightH * ((1 - horizontal) * l + horizontal * r) +
          // vertical interpolation
          weightV * ((1 - vertical) * t + vertical * b) +
          // additional noise
          n;

        const clamped = Math.max(0, Math.min(1, c));
        rgb[i] = Math.round(255 * clamped);
      }

      const idx = (y * effectW + x) * 4;
      out.data[idx] = rgb[0];
      out.data[idx + 1] = rgb[1];
      out.data[idx + 2] = rgb[2];
      out.data[idx + 3] = 255;
    }
  }

  ectx.putImageData(out, 0, 0);
  const prevSmoothing = ctx.imageSmoothingEnabled;
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(effectCanvas, -w / 2, -h / 2, w, h);
  ctx.imageSmoothingEnabled = prevSmoothing;
  ctx.restore();
}


export class PixelateRect extends Rect {
  static override type = 'pixelate-rect';
  static override customProperties = [...(Rect.customProperties ?? []), 'pixelBlockSize'];

  declare pixelBlockSize: number;

  private _effectCanvas: HTMLCanvasElement | null = null;
  private _effectCanvasSize: { w: number; h: number } | null = null;

  static override ownDefaults = {
    ...Rect.ownDefaults,
    fill: 'transparent',
    stroke: '#000000',
    strokeWidth: 0,
    objectCaching: false,
    lockRotation: true,
    hasRotatingPoint: false,
    pixelBlockSize: 18,
  };

  constructor(options: ConstructorParameters<typeof Rect>[0]) {
    super(options);
    Object.assign(this, PixelateRect.ownDefaults);
    this.setOptions(options);
  }

  override _render(ctx: CanvasRenderingContext2D) {
    const srcCtx = ctx;
    const c = this.canvas;
    if (!srcCtx || !c) {
      return;
    }

    const w = Math.max(0, this.width ?? 0);
    const h = Math.max(0, this.height ?? 0);
    if (!w || !h) {
      return;
    }

    const rect = getViewportRect(c, this, w, h);
    if (!rect) {
      return;
    }

    const rectScaling = c.getRetinaScaling();
    const rectPx = {
      left: rect.left * rectScaling,
      top: rect.top * rectScaling,
      width: rect.width * rectScaling,
      height: rect.height * rectScaling,
    };

    const srcCanvas = srcCtx.canvas;
    const srcW = Math.floor(srcCanvas.width);
    const srcH = Math.floor(srcCanvas.height);
    if (!srcW || !srcH) {
      return;
    }

    // Secure pseudo-pixelation: synthesize pixels using only fringe pixels outside the rect.
    // Parameters (in viewport pixel space). Deterministic PRNG seed = 42.
    const blockSize = clamp(this.pixelBlockSize, 2, 256);
    const effectW = Math.max(1, Math.floor(rect.width / blockSize));
    const effectH = Math.max(1, Math.floor(rect.height / blockSize));
    const strength = Math.max(1, Math.round(blockSize / 6));
    const samplingNoiseStd = 5 * strength + 1;
    const noiseStd = 0.1;

    const fringes = getFringes(rectPx, srcW, srcH);
    // If there are no outside pixels at all (rect covers whole canvas), fail closed.
    if (!fringes.hasTop && !fringes.hasBottom && !fringes.hasLeft && !fringes.hasRight) {
      fillClippedGrey(ctx, w, h);
      return;
    }

    // Only read 1px fringe stripes. Never read any pixel inside the rect into JS memory.
    const stripes: SrcFringeStripes = {};
    try {
      if (fringes.hasTop) {
        const left = fringes.rectL;
        const width = fringes.rectR - fringes.rectL + 1;
        stripes.top = { dir: 'h', img: srcCtx.getImageData(left, fringes.topY, width, 1), left, y: fringes.topY, width };
      }
      if (fringes.hasBottom) {
        const left = fringes.rectL;
        const width = fringes.rectR - fringes.rectL + 1;
        stripes.bottom = { dir: 'h', img: srcCtx.getImageData(left, fringes.bottomY, width, 1), left, y: fringes.bottomY, width };
      }
      if (fringes.hasLeft) {
        const top = fringes.rectT;
        const height = fringes.rectB - fringes.rectT + 1;
        stripes.left = { dir: 'v', img: srcCtx.getImageData(fringes.leftX, top, 1, height), x: fringes.leftX, top, height };
      }
      if (fringes.hasRight) {
        const top = fringes.rectT;
        const height = fringes.rectB - fringes.rectT + 1;
        stripes.right = { dir: 'v', img: srcCtx.getImageData(fringes.rightX, top, 1, height), x: fringes.rightX, top, height };
      }
    } catch {
      // If getImageData fails (e.g. tainted canvas), fail closed by doing nothing.
      return;
    }

    this._effectCanvas ??= document.createElement('canvas');
    this._effectCanvasSize = ensureEffectCanvasSize(this._effectCanvas, this._effectCanvasSize, effectW, effectH);
    const ectx = this._effectCanvas.getContext('2d', { willReadFrequently: true });
    if (!ectx) {
      return;
    }
    renderPixelation({
      ctx,
      ectx,
      effectCanvas: this._effectCanvas,
      effectW,
      effectH,
      w,
      h,
      noiseStd,
      fringes,
      stripes,
      samplingNoiseStd,
    });
  }
}

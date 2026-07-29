import { describe, test, expect } from 'vitest'
import { decryptDownloadStream } from '@base/utils/download';

const FORMAT_VERSION = 1;
const NONCE_SIZE = 12;
const CHUNK_SIZE = 512 * 1024;

const METADATA = {
  version: FORMAT_VERSION,
  cipher: 'AES-GCM',
  filename: 'file.pdf',
  content_type: 'application/octet-stream',
};

async function generateKey() {
  return await crypto.subtle.generateKey({ name: 'AES-GCM', length: 256 }, true, ['encrypt', 'decrypt']);
}

/**
 * Encrypt a frame the same way the API does.
 */
async function encryptFrame(key: CryptoKey, index: number, data: BufferSource, final = false) {
  const iv = crypto.getRandomValues(new Uint8Array(NONCE_SIZE));
  const additionalData = new TextEncoder().encode(`${FORMAT_VERSION}:${index}:${final ? 'final' : 'data'}`);
  const ciphertext = await crypto.subtle.encrypt({ name: 'AES-GCM', iv, additionalData }, key, data);

  const frame = new Uint8Array(iv.byteLength + ciphertext.byteLength);
  frame.set(iv);
  frame.set(new Uint8Array(ciphertext), iv.byteLength);
  return btoa(String.fromCharCode(...frame));
}

async function encryptDownload(key: CryptoKey, content: Uint8Array, options?: { metadata?: any; chunkSize?: number }) {
  const chunkSize = options?.chunkSize ?? CHUNK_SIZE;
  const frames = [await encryptFrame(key, 0, new TextEncoder().encode(JSON.stringify(options?.metadata ?? METADATA)))];
  for (let offset = 0; offset < content.length; offset += chunkSize) {
    frames.push(await encryptFrame(key, frames.length, content.slice(offset, offset + chunkSize)));
  }
  frames.push(await encryptFrame(key, frames.length, new Uint8Array(0), true));
  return frames;
}

/**
 * Send the encrypted frames as a stream, split into parts of the given size.
 * The API sends frames in chunks of arbitrary size, therefore frames may be split across multiple parts.
 */
function toStream(frames: string[], partSize?: number) {
  const data = new TextEncoder().encode(frames.join('\n'));
  const size = partSize ?? data.length;
  return new ReadableStream<Uint8Array>({
    start(controller) {
      for (let offset = 0; offset < data.length; offset += size) {
        controller.enqueue(data.slice(offset, offset + size));
      }
      controller.close();
    },
  });
}

async function blobBytes(blob: Blob) {
  return new Uint8Array(await blob.arrayBuffer());
}

describe('Encrypted download decryption', () => {
  test('decrypts a single-chunk file', async () => {
    const key = await generateKey();
    const content = new TextEncoder().encode('file content');
    const res = await decryptDownloadStream(toStream(await encryptDownload(key, content)), key);

    expect(res.filename).toBe('file.pdf');
    expect(res.blob.type).toBe('application/octet-stream');
    expect(await blobBytes(res.blob)).toEqual(content);
  });

  test('decrypts a multi-chunk file', async () => {
    const key = await generateKey();
    const content = crypto.getRandomValues(new Uint8Array(50_000));
    const frames = await encryptDownload(key, content, { chunkSize: 1024 });
    expect(frames.length).toBe(1 + 49 + 1);

    const res = await decryptDownloadStream(toStream(frames), key);
    expect(await blobBytes(res.blob)).toEqual(content);
  });

  test('decrypts an empty file', async () => {
    const key = await generateKey();
    const res = await decryptDownloadStream(toStream(await encryptDownload(key, new Uint8Array(0))), key);
    expect(res.blob.size).toBe(0);
    expect(res.filename).toBe('file.pdf');
  });

  test.each([1, 7, 64, 1024])('reassembles frames split across stream parts of %i bytes', async (partSize) => {
    const key = await generateKey();
    const content = crypto.getRandomValues(new Uint8Array(5_000));
    const frames = await encryptDownload(key, content, { chunkSize: 512 });

    const res = await decryptDownloadStream(toStream(frames, partSize), key);
    expect(await blobBytes(res.blob)).toEqual(content);
  });

  test('rejects a truncated stream', async () => {
    const key = await generateKey();
    const frames = await encryptDownload(key, crypto.getRandomValues(new Uint8Array(5_000)), { chunkSize: 512 });

    // Drop the final frame, as a proxy cutting the connection would
    await expect(decryptDownloadStream(toStream(frames.slice(0, -1)), key)).rejects.toThrow();
    // Drop content frames and the final frame
    await expect(decryptDownloadStream(toStream(frames.slice(0, 3)), key)).rejects.toThrow();
  });

  test('rejects an empty stream', async () => {
    const key = await generateKey();
    await expect(decryptDownloadStream(toStream([]), key)).rejects.toThrow();
  });

  test('rejects reordered frames', async () => {
    const key = await generateKey();
    const frames = await encryptDownload(key, crypto.getRandomValues(new Uint8Array(2_000)), { chunkSize: 512 });
    const reordered = [frames[0]!, frames[2]!, frames[1]!, ...frames.slice(3)];

    await expect(decryptDownloadStream(toStream(reordered), key)).rejects.toThrow();
  });

  test('rejects modified content', async () => {
    const key = await generateKey();
    const frames = await encryptDownload(key, new TextEncoder().encode('file content'));
    const modified = atob(frames[1]!).split('');
    modified[modified.length - 1] = String.fromCharCode(modified[modified.length - 1]!.charCodeAt(0) ^ 0xFF);
    frames[1] = btoa(modified.join(''));

    await expect(decryptDownloadStream(toStream(frames), key)).rejects.toThrow();
  });

  test('rejects a different key', async () => {
    const frames = await encryptDownload(await generateKey(), new TextEncoder().encode('file content'));
    await expect(decryptDownloadStream(toStream(frames), await generateKey())).rejects.toThrow();
  });

  test('rejects an unsupported format version', async () => {
    const key = await generateKey();
    const frames = await encryptDownload(key, new TextEncoder().encode('file content'), {
      metadata: { ...METADATA, version: FORMAT_VERSION + 1 },
    });

    await expect(decryptDownloadStream(toStream(frames), key)).rejects.toThrow(/Unsupported download format version/);
  });
});

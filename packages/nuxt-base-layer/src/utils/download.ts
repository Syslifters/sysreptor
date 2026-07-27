import { base64decode, base64encode, fileDownload } from "@base/utils/helpers";

// Header used to opt in to encrypted downloads. Has to match the API.
export const ENCRYPTION_KEY_HEADER = 'X-Sysreptor-Encryption-Key';

// Format version of the encrypted stream. Has to match the API.
const FORMAT_VERSION = 1;
const NONCE_SIZE = 12;

// Decrypted chunks are moved into Blobs regularly, such that large files are not kept in memory.
const BLOB_FLUSH_SIZE = 32 * 1024 * 1024;

export type DecryptedDownload = {
  blob: Blob;
  filename: string;
};

async function decryptFrame(key: CryptoKey, index: number, frame: string, final: boolean) {
  const data = base64decode(frame);
  const additionalData = new TextEncoder().encode(`${FORMAT_VERSION}:${index}:${final ? 'final' : 'data'}`);
  return await crypto.subtle.decrypt({
    name: 'AES-GCM',
    iv: data.slice(0, NONCE_SIZE),
    additionalData,
  }, key, data.slice(NONCE_SIZE));
}

/**
 * Decrypt a file downloaded as encrypted text stream.
 * The stream consists of newline-separated base64 frames: metadata, file chunks and a final empty frame.
 * Decryption fails if frames were modified, reordered or dropped by a proxy.
 *
 * Frames are decrypted while they are received and are moved into Blobs regularly.
 * Therefore even very large files never have to be held in memory as a whole.
 */
export async function decryptDownloadStream(stream: ReadableStream<Uint8Array>, key: CryptoKey): Promise<DecryptedDownload> {
  const reader = stream.getReader();
  const textDecoder = new TextDecoder();

  let metadata: any = null;
  let index = 0;
  let buffer = '';
  const blobParts = [] as Blob[];
  let pending = [] as ArrayBuffer[];
  let pendingSize = 0;

  async function handleFrame(frame: string) {
    if (index === 0) {
      metadata = JSON.parse(new TextDecoder().decode(await decryptFrame(key, index, frame, false)));
      if (metadata?.version !== FORMAT_VERSION) {
        throw new Error(`Unsupported download format version: ${metadata?.version}`);
      }
    } else {
      const chunk = await decryptFrame(key, index, frame, false);
      pending.push(chunk);
      pendingSize += chunk.byteLength;
      if (pendingSize >= BLOB_FLUSH_SIZE) {
        blobParts.push(new Blob(pending));
        pending = [];
        pendingSize = 0;
      }
    }
    index += 1;
  }

  for (;;) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    buffer += textDecoder.decode(value, { stream: true });

    // The last segment might be an incomplete frame. Keep it buffered until the next newline.
    const frames = buffer.split('\n');
    buffer = frames.pop() ?? '';
    for (const frame of frames) {
      await handleFrame(frame);
    }
  }
  buffer += textDecoder.decode();

  // The remaining buffer holds the final frame. Its absence means the download was truncated.
  if (index === 0 || !buffer) {
    throw new Error('Download is incomplete');
  }
  if ((await decryptFrame(key, index, buffer, true)).byteLength !== 0) {
    throw new Error('Download is incomplete');
  }

  blobParts.push(new Blob(pending));
  return {
    blob: new Blob(blobParts, { type: metadata.content_type }),
    filename: metadata.filename,
  };
}

/**
 * Download a file via an encrypted channel and save it locally.
 * The file is transferred as an encrypted text stream, therefore proxies and firewalls
 * cannot inspect the file content, the content type or the filename.
 */
export async function downloadFileEncrypted(url: string, options?: { filename?: string|null }) {
  const key = await crypto.subtle.generateKey({ name: 'AES-GCM', length: 256 }, true, ['decrypt']);
  const res = await fetch(url, {
    method: 'GET',
    headers: {
      [ENCRYPTION_KEY_HEADER]: base64encode(await crypto.subtle.exportKey('raw', key)),
    },
  });
  if (!res.ok || !res.body) {
    throw new Error(`Download failed with status code ${res.status}`);
  }

  const decrypted = await decryptDownloadStream(res.body, key);
  fileDownload(decrypted.blob, options?.filename || decrypted.filename);
}

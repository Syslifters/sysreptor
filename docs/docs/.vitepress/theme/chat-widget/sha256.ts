import { sha256 as sha256Lib } from 'js-sha256'

/** SHA-256 bytes. Works without a secure context (no crypto.subtle). */
export function sha256(data: Uint8Array): Uint8Array {
  return new Uint8Array(sha256Lib.array(data))
}

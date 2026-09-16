import { fetchWith429Retry, type Fetch429RetryOptions } from './api'
import { chatConfig } from './config'
import { sha256 } from './sha256'

export type PowSolution = { token: string; nonce: string }

export type PowChallengeResponse = {
  enabled: boolean
  token?: string
  challenge?: string
  difficulty?: number
  expires_at?: number
}

const YIELD_INTERVAL = 500

export async function solvePow(challenge: string, difficulty: number): Promise<string> {
  let nonce = 0
  while (true) {
    const data = new TextEncoder().encode(`${challenge}:${nonce}`)
    const hash = sha256(data)
    let bits = 0
    done: for (const byte of hash) {
      if (byte === 0) {
        bits += 8
        continue
      }
      for (let b = 7; b >= 0; b--) {
        if (byte & (1 << b)) break done
        bits++
      }
      break
    }
    if (bits >= difficulty) return String(nonce)
    nonce++
    if (nonce % YIELD_INTERVAL === 0) {
      await new Promise((r) => window.setTimeout(r, 0))
    }
  }
}

export async function fetchPowChallenge(
  opts: Fetch429RetryOptions = {},
): Promise<PowChallengeResponse> {
  const res = await fetchWith429Retry(`${chatConfig.apiBase}/v1/pow/challenge`, undefined, opts)
  if (!res.ok) {
    const err = new Error(`PoW challenge failed: HTTP ${res.status}`) as Error & { status?: number }
    err.status = res.status
    throw err
  }
  return (await res.json()) as PowChallengeResponse
}

export class PowManager {
  enabled = true
  private ready: PowSolution | null = null
  private inflight: Promise<PowSolution | null> | null = null
  private checked = false

  prepare(): void {
    if (this.checked && !this.enabled) return
    if (this.ready || this.inflight) return
    this.inflight = this.fetchAndSolveInternal()
      .then((solution) => {
        if (solution) this.ready = solution
        return solution
      })
      .catch(() => null)
      .finally(() => {
        this.inflight = null
      })
  }

  async consumeReady(opts: Fetch429RetryOptions = {}): Promise<PowSolution | null> {
    if (this.inflight) {
      await this.inflight
    }
    if (!this.enabled) return null
    const solution = this.ready
    this.ready = null
    if (!solution) {
      return await this.fetchAndSolve(opts)
    }
    return solution
  }

  async fetchAndSolve(opts: Fetch429RetryOptions = {}): Promise<PowSolution | null> {
    if (this.inflight) {
      await this.inflight
    }
    return await this.fetchAndSolveInternal(opts)
  }

  private async fetchAndSolveInternal(
    opts: Fetch429RetryOptions = {},
  ): Promise<PowSolution | null> {
    const body = await fetchPowChallenge(opts)
    this.checked = true
    if (!body.enabled) {
      this.enabled = false
      return null
    }
    this.enabled = true
    if (!body.token || !body.challenge || body.difficulty == null) {
      throw new Error('Invalid PoW challenge response')
    }
    const nonce = await solvePow(body.challenge, body.difficulty)
    return { token: body.token, nonce }
  }
}

export const powManager = new PowManager()

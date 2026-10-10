/**
 * Admin service for the ElevenLabs primary/alternate account failover
 */
import { httpClient } from '../client.js'
import { ENDPOINTS } from '../config.js'

export interface ElevenLabsAccountStatus {
  label: 'primary' | 'alt'
  configured: boolean
  active: boolean
  tier: string | null
  status: string | null
  character_count: number | null
  character_limit: number | null
  characters_remaining: number | null
  percent_used: number | null
  next_reset_at: string | null
  billing_period: string | null
  error: string | null
}

export interface ElevenLabsStatus {
  failover_enabled: boolean
  active_account: 'primary' | 'alt'
  failover_until: string | null
  accounts: ElevenLabsAccountStatus[]
}

export const elevenLabsAdminService = {
  /** Active account, failover window and live usage for each account (Admin only) */
  getStatus: (): Promise<ElevenLabsStatus> => {
    return httpClient.get<ElevenLabsStatus>(ENDPOINTS.adminElevenLabs.status)
  },

  /** Return to the primary account immediately (Admin only) */
  reset: (): Promise<ElevenLabsStatus> => {
    return httpClient.post<ElevenLabsStatus>(ENDPOINTS.adminElevenLabs.reset, {})
  },
}

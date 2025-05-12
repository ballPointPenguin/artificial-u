/**
 * Service for voice-related API calls
 */
import { httpClient } from '../client'
import { ENDPOINTS } from '../config'
import type { ManualVoiceAssignmentPayload, PaginatedVoices, Voice, VoiceListParams } from '../types'

/**
 * Manually assign a voice to a professor.
 *
 * @param professorId - ID of the professor to assign voice to.
 * @param payload - ManualVoiceAssignmentPayload containing the el_voice_id.
 * @returns Promise<void> as the API returns 204 No Content.
 */
export const manualAssignVoice = async (
  professorId: string,
  payload: ManualVoiceAssignmentPayload
): Promise<void> => {
  await httpClient.post<Record<string, never>>(
    ENDPOINTS.voices.manualAssignVoice(professorId),
    payload
  )
  return;
}

/**
 * List available voices with optional filtering and pagination.
 *
 * @param params - VoiceListParams for filtering and pagination.
 * @returns Promise<PaginatedVoices> containing the list of voices and pagination details.
 */
export const listVoices = async (params: VoiceListParams = {}): Promise<PaginatedVoices> => {
  const queryParams = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null) {
      queryParams.append(key, String(value))
    }
  }
  const endpoint = `${ENDPOINTS.voices.listVoices}${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  return httpClient.get<PaginatedVoices>(endpoint)
}

/**
 * Get a specific voice by its database ID.
 *
 * @param voiceId - Database ID of the voice to retrieve.
 * @returns Promise<Voice> containing the voice details.
 */
export const getVoice = async (voiceId: number): Promise<Voice> => {
  return httpClient.get<Voice>(ENDPOINTS.voices.getVoice(voiceId))
}
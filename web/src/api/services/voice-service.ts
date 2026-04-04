/**
 * Service for voice-related API calls
 */
import { httpClient } from '../client'
import { ENDPOINTS } from '../config'
import type {
  ManualVoiceAssignmentPayload,
  PaginatedVoices,
  Voice,
  VoiceListParams,
} from '../types'

/**
 * Manually assign a voice to a professor.
 *
 * Sends external_id + tts_backend to the API. For backward compatibility,
 * el_voice_id is also accepted (the API will treat it as an ElevenLabs external_id).
 *
 * @param professorId - ID of the professor to assign voice to.
 * @param payload - ManualVoiceAssignmentPayload containing external_id and optional tts_backend.
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
  return
}

/**
 * List available voices with optional filtering and pagination.
 *
 * @param params - VoiceListParams for filtering and pagination.
 * @returns Promise<PaginatedVoices> containing the list of voices and pagination details.
 */
export const listVoices = async (params: VoiceListParams = {}): Promise<PaginatedVoices> => {
  const queryParams = new URLSearchParams()

  // Explicitly add known parameters if they exist (are not undefined)
  if (params.gender !== undefined) queryParams.set('gender', params.gender)
  if (params.accent !== undefined) queryParams.set('accent', params.accent)
  if (params.age !== undefined) queryParams.set('age', params.age)
  if (params.language !== undefined) queryParams.set('language', params.language)
  if (params.use_case !== undefined) queryParams.set('use_case', params.use_case)
  if (params.category !== undefined) queryParams.set('category', params.category)

  // Pagination parameters, usually included if provided and not undefined
  if (params.limit !== undefined) queryParams.set('limit', String(params.limit))
  if (params.offset !== undefined) queryParams.set('offset', String(params.offset))

  // Construct the endpoint URL. URLSearchParams.toString() handles empty cases.
  const endpoint = `${ENDPOINTS.voices.listVoices}?${queryParams.toString()}`

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

/**
 * Get a voice by its TTS backend and external identifier.
 *
 * @param backend - TTS backend name (e.g., "elevenlabs", "mistral")
 * @param externalId - Provider-specific voice identifier
 * @returns Promise<Voice> containing the voice details.
 */
export const getVoiceByExternalId = async (
  backend: string,
  externalId: string
): Promise<Voice> => {
  return httpClient.get<Voice>(ENDPOINTS.voices.getVoiceByExternalId(backend, externalId))
}

/**
 * Get a specific voice by its ElevenLabs voice_id.
 * Legacy convenience wrapper — prefer getVoiceByExternalId("elevenlabs", id).
 */
export const getVoiceByElId = async (elVoiceId: string): Promise<Voice> => {
  return httpClient.get<Voice>(ENDPOINTS.voices.getVoiceByElId(elVoiceId))
}

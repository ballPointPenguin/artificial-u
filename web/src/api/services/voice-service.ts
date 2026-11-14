/**
 * Service for voice-related API calls
 */
import { httpClient } from '../client'
import { ENDPOINTS } from '../config'
import type {
  ManualVoiceAssignmentPayload,
  MistralVoiceCatalog,
  QwenVoiceCatalog,
  Voice,
  VoiceCloneToMistralRequest,
  VoiceDesignPreviewsResponse,
  VoiceDesignSaveRequest,
  VoicePreviewRequest,
  VoicePreviewResponse,
  XaiVoiceCatalog,
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
 * Get a specific voice by its database ID.
 *
 * @param voiceId - Database ID of the voice to retrieve.
 * @returns Promise<Voice> containing the voice details.
 */
export const getVoice = async (voiceId: number): Promise<Voice> => {
  return httpClient.get<Voice>(ENDPOINTS.voices.getVoice(voiceId))
}

/**
 * List Mistral voices on-demand from the Mistral API (not stored in DB).
 *
 * @param language - Optional language prefix filter (e.g. "en").
 * @param gender - Optional gender filter.
 * @returns Promise<MistralVoiceCatalog>
 */
export const listMistralCatalog = async (
  language?: string,
  gender?: string
): Promise<MistralVoiceCatalog> => {
  const params = new URLSearchParams()
  if (language) params.set('language', language)
  if (gender) params.set('gender', gender)
  const qs = params.toString()
  const url = qs ? `${ENDPOINTS.voices.mistralCatalog}?${qs}` : ENDPOINTS.voices.mistralCatalog
  return httpClient.get<MistralVoiceCatalog>(url)
}

/**
 * List xAI voices on-demand from the xAI API (not stored in DB).
 *
 * The catalog is read fresh each time, so newly added xAI voices appear
 * automatically.
 *
 * @param language - Optional language prefix filter (e.g. "fr").
 * @param gender - Optional gender filter.
 * @returns Promise<XaiVoiceCatalog>
 */
export const listXaiCatalog = async (
  language?: string,
  gender?: string
): Promise<XaiVoiceCatalog> => {
  const params = new URLSearchParams()
  if (language) params.set('language', language)
  if (gender) params.set('gender', gender)
  const qs = params.toString()
  const url = qs ? `${ENDPOINTS.voices.xaiCatalog}?${qs}` : ENDPOINTS.voices.xaiCatalog
  return httpClient.get<XaiVoiceCatalog>(url)
}

/**
 * List Qwen (Alibaba) voices.
 *
 * Alibaba exposes no voice-list API for qwen-audio-3.1-tts-flash, so the backend
 * serves a static catalog.
 *
 * @param language - Optional language prefix filter (e.g. "en").
 * @param gender - Optional gender filter.
 * @returns Promise<QwenVoiceCatalog>
 */
export const listQwenCatalog = async (
  language?: string,
  gender?: string
): Promise<QwenVoiceCatalog> => {
  const params = new URLSearchParams()
  if (language) params.set('language', language)
  if (gender) params.set('gender', gender)
  const qs = params.toString()
  const url = qs ? `${ENDPOINTS.voices.qwenCatalog}?${qs}` : ENDPOINTS.voices.qwenCatalog
  return httpClient.get<QwenVoiceCatalog>(url)
}

/**
 * Generate a short TTS audio preview for a voice.
 *
 * @param request - VoicePreviewRequest with voice_id, tts_backend, and optional text.
 * @returns Promise<VoicePreviewResponse> containing a base64 audio data URI.
 */
export const previewVoice = async (request: VoicePreviewRequest): Promise<VoicePreviewResponse> => {
  return httpClient.post<VoicePreviewResponse>(ENDPOINTS.voices.preview, request)
}

/**
 * Generate Voice Design previews for a professor.
 *
 * The backend builds a voice prompt from the professor's attributes and calls
 * the ElevenLabs Voice Design API.  Returns up to 3 short audio previews
 * (base64 MP3) along with their temporary generated_voice_id values.
 */
export const generateVoiceDesignPreviews = async (
  professorId: number,
  language?: string
): Promise<VoiceDesignPreviewsResponse> => {
  return httpClient.post<VoiceDesignPreviewsResponse>(ENDPOINTS.voices.designPreviews, {
    professor_id: professorId,
    language,
  })
}

/**
 * Save a selected Voice Design preview to the ElevenLabs library.
 *
 * Permanently saves the chosen preview as a named voice, creates a DB record,
 * and assigns it to the professor.  Returns the saved Voice.
 */
export const saveDesignedVoice = async (request: VoiceDesignSaveRequest): Promise<Voice> => {
  return httpClient.post<Voice>(ENDPOINTS.voices.designSave, request)
}

/**
 * Clone a professor's current ElevenLabs voice into the Mistral voice library.
 *
 * Downloads the ElevenLabs preview audio and submits it to Mistral as a clone
 * sample.  The professor is re-associated with the new Mistral voice.
 */
export const cloneVoiceToMistral = async (request: VoiceCloneToMistralRequest): Promise<Voice> => {
  return httpClient.post<Voice>(ENDPOINTS.voices.cloneToMistral, request)
}

/**
 * Quickstart service for the wizard-based course creation flow
 */
import { httpClient } from '../client.js'
import { ENDPOINTS } from '../config.js'
import type {
  IntroAudioRequest,
  IntroAudioResponse,
  QuickstartFinalizeRequest,
  QuickstartFinalizeResponse,
  QuickstartMatchRequest,
  QuickstartMatchResponse,
  QuickstartProfessorActionRequest,
  QuickstartProfessorResponse,
  QuickstartRegenerateProfessorRequest,
  QuickstartStartRequest,
  QuickstartStartResponse,
} from '../types.js'

export const quickstartService = {
  /**
   * Match user's learning goal against existing published courses.
   * Returns matching courses or signals that a new course should be generated.
   */
  matchCourses: (data: QuickstartMatchRequest): Promise<QuickstartMatchResponse> => {
    return httpClient.post<QuickstartMatchResponse>(ENDPOINTS.quickstart.matchCourses, data)
  },

  /**
   * Start the quickstart course creation flow (synchronous).
   * Creates a new course with smart department/professor selection.
   * WARNING: This can timeout behind CloudFront. Use enqueueStart for production.
   */
  start: (data: QuickstartStartRequest): Promise<QuickstartStartResponse> => {
    return httpClient.post<QuickstartStartResponse>(ENDPOINTS.quickstart.start, data)
  },

  /**
   * Enqueue quickstart course creation as a background job.
   * This is the recommended approach for production to avoid CloudFront timeouts.
   * Poll the returned job ID via jobs service to get the result.
   */
  enqueueStart: (
    data: QuickstartStartRequest
  ): Promise<{
    id: number
    kind: string
    status: string
    attempts: number
    max_attempts: number
    priority?: number
    run_after?: string
  }> => {
    return httpClient.post(ENDPOINTS.quickstart.enqueueStart, data)
  },

  /**
   * Get professor details for the review step.
   */
  getProfessor: (professorId: number, courseId: number): Promise<QuickstartProfessorResponse> => {
    return httpClient.get<QuickstartProfessorResponse>(
      ENDPOINTS.quickstart.professor(professorId, courseId)
    )
  },

  /**
   * Generate an ephemeral intro audio clip for the professor.
   * Returns a base64 data URI that can be played directly.
   */
  generateIntroAudio: (data: IntroAudioRequest): Promise<IntroAudioResponse> => {
    return httpClient.post<IntroAudioResponse>(ENDPOINTS.quickstart.generateIntroAudio, data)
  },

  /**
   * Regenerate the professor's image.
   * Enqueues a background job and returns updated professor details.
   */
  regenerateProfessorImage: (
    data: QuickstartProfessorActionRequest
  ): Promise<QuickstartProfessorResponse> => {
    return httpClient.post<QuickstartProfessorResponse>(
      ENDPOINTS.quickstart.regenerateProfessorImage,
      data
    )
  },

  /**
   * Reassign a voice to the professor using the voice mapping algorithm.
   */
  reassignProfessorVoice: (
    data: QuickstartProfessorActionRequest
  ): Promise<QuickstartProfessorResponse> => {
    return httpClient.post<QuickstartProfessorResponse>(
      ENDPOINTS.quickstart.reassignProfessorVoice,
      data
    )
  },

  /**
   * Regenerate the professor entirely with optional freeform guidance.
   * Note: This can timeout behind CloudFront for complex generations.
   * Consider implementing an enqueue pattern if timeouts occur frequently.
   */
  regenerateProfessor: (
    data: QuickstartRegenerateProfessorRequest
  ): Promise<QuickstartProfessorResponse> => {
    return httpClient.post<QuickstartProfessorResponse>(
      ENDPOINTS.quickstart.regenerateProfessor,
      data
    )
  },

  /**
   * Finalize the quickstart flow and kick off content generation.
   * Starts topic generation and first lecture creation.
   */
  finalize: (data: QuickstartFinalizeRequest): Promise<QuickstartFinalizeResponse> => {
    return httpClient.post<QuickstartFinalizeResponse>(ENDPOINTS.quickstart.finalize, data)
  },
}

/**
 * Featured items service
 */
import { httpClient } from '../client.js'
import { ENDPOINTS } from '../config.js'
import type { FeaturedItem, FeaturedItemCreate, PlatformStats } from '../types.js'

interface ListFeaturedParams {
  language?: string
  item_type?: string
}

export const featuredService = {
  listFeatured: (params: ListFeaturedParams = {}): Promise<FeaturedItem[]> => {
    const queryParams = new URLSearchParams()
    if (params.language) queryParams.set('language', params.language)
    if (params.item_type) queryParams.set('item_type', params.item_type)
    const qs = queryParams.toString()
    return httpClient.get<FeaturedItem[]>(`${ENDPOINTS.featured.list}${qs ? `?${qs}` : ''}`)
  },

  addFeatured: (data: FeaturedItemCreate): Promise<FeaturedItem> => {
    return httpClient.post<FeaturedItem>(ENDPOINTS.featured.list, data)
  },

  updateOrder: (id: number, display_order: number): Promise<FeaturedItem> => {
    return httpClient.patch<FeaturedItem>(ENDPOINTS.featured.order(id), { display_order })
  },

  removeFeatured: (id: number): Promise<null> => {
    return httpClient.delete<null>(ENDPOINTS.featured.detail(id))
  },

  getStats: (): Promise<PlatformStats> => {
    return httpClient.get<PlatformStats>(ENDPOINTS.stats)
  },
}

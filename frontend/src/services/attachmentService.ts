import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || '/api'

export interface Attachment {
  id: string
  space_id: string
  page_id: string | null
  url: string
  filename: string
  mime_type: string
  size_bytes: number
  sha256_hash: string | null
  created_by: string
  created_at: string
}

export const attachmentService = {
  /** URL that serves the file bytes (works in <img src> and links, cookies are sent same-origin) */
  fileUrl: (attachmentId: string): string => `${API_URL}/attachments/${attachmentId}/file`,

  isImage: (a: Pick<Attachment, 'mime_type'>): boolean =>
    ['image/png', 'image/jpeg', 'image/gif', 'image/webp'].includes(a.mime_type),

  listForPage: async (pageId: string): Promise<Attachment[]> => {
    const response = await axios.get(`${API_URL}/attachments/page/${pageId}/list`, {
      withCredentials: true
    })
    return response.data
  },

  upload: async (
    spaceId: string,
    pageId: string | null,
    file: File,
    onProgress?: (percent: number) => void
  ): Promise<Attachment> => {
    const form = new FormData()
    form.append('file', file)
    const response = await axios.post(`${API_URL}/attachments/upload`, form, {
      params: { space_id: spaceId, page_id: pageId || undefined },
      withCredentials: true,
      onUploadProgress: (e) => {
        if (onProgress && e.total) onProgress(Math.round((e.loaded / e.total) * 100))
      }
    })
    return response.data
  },

  remove: async (attachmentId: string): Promise<void> => {
    await axios.delete(`${API_URL}/attachments/${attachmentId}`, { withCredentials: true })
  }
}

export const formatBytes = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

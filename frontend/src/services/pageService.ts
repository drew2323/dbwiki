import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || '/api'

// Types
export interface Page {
  id: string
  space_id: string
  title: string
  slug: string
  created_by: string
  created_at: string
  updated_at: string
  is_archived: boolean
  draft_etag: string | null
}

export interface PageDetail extends Page {
  draft_json: any | null
  draft_text: string | null
}

export interface PageVersion {
  id: string
  page_id: string
  version_number: number
  title: string
  content_json: any
  content_text: string
  author_id: string
  created_at: string
  notes: string | null
}

export interface TreeNode {
  id: string
  space_id: string
  page_id: string | null
  parent_id: string | null
  position: number
  title: string | null
  slug: string | null
  is_archived: boolean
  has_children: boolean
}

export interface Backlink {
  id: string
  src_page_id: string
  src_page_title: string
  src_page_slug: string
  created_at: string
}

export const pageService = {
  // ============================================================================
  // Page CRUD
  // ============================================================================

  /**
   * Create a new page
   */
  createPage: async (
    spaceId: string,
    title: string,
    parentId?: string,
    slug?: string
  ): Promise<Page> => {
    const response = await axios.post(
      `${API_URL}/pages`,
      {
        space_id: spaceId,
        title,
        slug,
        parent_id: parentId
      },
      { withCredentials: true }
    )
    return response.data
  },

  /**
   * Get page by ID
   */
  getPageById: async (pageId: string): Promise<PageDetail> => {
    const response = await axios.get(`${API_URL}/pages/${pageId}`, {
      withCredentials: true
    })
    return response.data
  },

  /**
   * Get page by slug within a space
   */
  getPageBySlug: async (spaceId: string, slug: string): Promise<PageDetail> => {
    const response = await axios.get(`${API_URL}/pages/slug/${spaceId}/${slug}`)
    return response.data
  },

  /**
   * List all pages in a space
   */
  listPagesInSpace: async (
    spaceId: string,
    skip: number = 0,
    limit: number = 100,
    includeArchived: boolean = false
  ): Promise<Page[]> => {
    const response = await axios.get(`${API_URL}/pages/space/${spaceId}/list`, {
      params: { skip, limit, include_archived: includeArchived },
      withCredentials: true
    })
    return response.data
  },

  /**
   * Update page metadata
   */
  updatePage: async (
    pageId: string,
    data: { title?: string; slug?: string; is_archived?: boolean }
  ): Promise<Page> => {
    const response = await axios.patch(
      `${API_URL}/pages/${pageId}`,
      data,
      { withCredentials: true }
    )
    return response.data
  },

  /**
   * Delete page
   */
  deletePage: async (pageId: string, hardDelete: boolean = false): Promise<void> => {
    await axios.delete(`${API_URL}/pages/${pageId}`, {
      params: { hard_delete: hardDelete },
      withCredentials: true
    })
  },

  // ============================================================================
  // Draft Management
  // ============================================================================

  /**
   * Get draft content with ETag
   */
  getDraft: async (pageId: string): Promise<{ draft_json: any; draft_text: string; draft_etag: string; updated_at: string }> => {
    const response = await axios.get(`${API_URL}/pages/${pageId}/draft`, {
      withCredentials: true
    })
    return response.data
  },

  /**
   * Update draft content (autosave)
   */
  updateDraft: async (
    pageId: string,
    draftJson: any,
    draftText: string,
    ifMatch?: string
  ): Promise<{ draft_json: any; draft_text: string; draft_etag: string; updated_at: string }> => {
    const response = await axios.put(
      `${API_URL}/pages/${pageId}/draft`,
      {
        draft_json: draftJson,
        draft_text: draftText,
        if_match: ifMatch
      },
      {
        withCredentials: true,
        headers: ifMatch ? { 'If-Match': ifMatch } : {}
      }
    )
    return response.data
  },

  // ============================================================================
  // Version Management
  // ============================================================================

  /**
   * Publish current draft as new version
   */
  publishPage: async (pageId: string, notes?: string): Promise<PageVersion> => {
    const response = await axios.post(
      `${API_URL}/pages/${pageId}/publish`,
      { notes },
      { withCredentials: true }
    )
    return response.data
  },

  /**
   * List all versions for a page
   */
  listVersions: async (
    pageId: string,
    skip: number = 0,
    limit: number = 50
  ): Promise<PageVersion[]> => {
    const response = await axios.get(`${API_URL}/pages/${pageId}/versions`, {
      params: { skip, limit },
      withCredentials: true
    })
    return response.data
  },

  /**
   * Get specific version
   */
  getVersion: async (pageId: string, versionId: string): Promise<PageVersion> => {
    const response = await axios.get(
      `${API_URL}/pages/${pageId}/versions/${versionId}`,
      { withCredentials: true }
    )
    return response.data
  },

  /**
   * Restore version to draft
   */
  restoreVersion: async (
    pageId: string,
    versionId: string
  ): Promise<{ draft_json: any; draft_text: string; draft_etag: string; updated_at: string }> => {
    const response = await axios.post(
      `${API_URL}/pages/${pageId}/restore`,
      { version_id: versionId },
      { withCredentials: true }
    )
    return response.data
  },

  // ============================================================================
  // Backlinks
  // ============================================================================

  /**
   * Get backlinks to a page
   */
  getBacklinks: async (pageId: string): Promise<Backlink[]> => {
    const response = await axios.get(`${API_URL}/pages/${pageId}/backlinks`, {
      withCredentials: true
    })
    return response.data
  },

  // ============================================================================
  // Search
  // ============================================================================

  /**
   * Full-text search
   */
  searchPages: async (
    query: string,
    spaceId?: string,
    limit: number = 20,
    offset: number = 0
  ): Promise<{ results: any[]; total: number; query: string; took_ms: number }> => {
    const response = await axios.post(
      `${API_URL}/pages/search`,
      {
        query,
        space_id: spaceId,
        limit,
        offset
      },
      { withCredentials: true }
    )
    return response.data
  },

  // ============================================================================
  // Tree Operations
  // ============================================================================

  /**
   * Get tree structure for a space
   */
  getSpaceTree: async (spaceId: string, parentId?: string): Promise<TreeNode[]> => {
    const response = await axios.get(`${API_URL}/tree/space/${spaceId}`, {
      params: { parent_id: parentId },
      withCredentials: true
    })
    return response.data
  },

  /**
   * Get breadcrumb trail for a page
   */
  getBreadcrumb: async (pageId: string): Promise<{ id: string; title: string; slug: string }[]> => {
    const response = await axios.get(`${API_URL}/tree/page/${pageId}/breadcrumb`, {
      withCredentials: true
    })
    return response.data
  },

  /**
   * Move tree node
   */
  moveNode: async (
    nodeId: string,
    parentId: string | null,
    position: number
  ): Promise<TreeNode> => {
    const response = await axios.post(
      `${API_URL}/tree/node/${nodeId}/move`,
      {
        parent_id: parentId,
        position
      },
      { withCredentials: true }
    )
    return response.data
  },

  /**
   * Batch reorder nodes
   */
  reorderNodes: async (updates: { id: string; position: number }[]): Promise<void> => {
    await axios.post(
      `${API_URL}/tree/node/reorder`,
      { updates },
      { withCredentials: true }
    )
  }
}

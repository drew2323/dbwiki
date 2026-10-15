import { ref } from 'vue'

export interface RecentPage {
  id: string
  title: string
  slug: string
  spaceKey: string
  spaceName?: string | null
}

const STORAGE_KEY = 'dbwiki.recentPages'
const MAX_RECENT = 8

const read = (): RecentPage[] => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    const parsed = raw ? JSON.parse(raw) : []
    return Array.isArray(parsed) ? parsed.filter((p) => p && p.id && p.spaceKey) : []
  } catch {
    return []
  }
}

// Shared across components so the palette sees pages visited elsewhere immediately
const recent = ref<RecentPage[]>(read())

export function useRecentPages() {
  const add = (page: RecentPage) => {
    recent.value = [page, ...recent.value.filter((p) => p.id !== page.id)].slice(0, MAX_RECENT)
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(recent.value))
    } catch {
      // storage unavailable (private mode) - keep in memory only
    }
  }

  const remove = (id: string) => {
    recent.value = recent.value.filter((p) => p.id !== id)
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(recent.value))
    } catch {
      // ignore
    }
  }

  return { recent, add, remove }
}

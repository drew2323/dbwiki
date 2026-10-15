import { ref, computed } from 'vue'
import { pageService, type FavoritePage } from '@/services/pageService'

// Shared state: the star in the page header and the search palette stay in sync
const favorites = ref<FavoritePage[]>([])
const loaded = ref(false)
let loading: Promise<void> | null = null

export function useFavorites() {
  /** Load the current user's favorites (once; pass force to refresh). Call only when logged in. */
  const load = async (force = false) => {
    if (loaded.value && !force) return
    if (!loading) {
      loading = pageService
        .listFavorites()
        .then((list) => {
          favorites.value = list
          loaded.value = true
        })
        .catch((err) => {
          console.error('Failed to load favorites:', err)
        })
        .finally(() => {
          loading = null
        })
    }
    await loading
  }

  const ids = computed(() => new Set(favorites.value.map((f) => f.page_id)))
  const isFavorite = (pageId: string | null | undefined) => !!pageId && ids.value.has(pageId)

  /** Optimistically star/unstar; rolls back and rethrows when the request fails. */
  const toggle = async (page: { id: string; title: string; slug: string }, space: { id: string; key: string; name: string }) => {
    const before = favorites.value
    if (isFavorite(page.id)) {
      favorites.value = before.filter((f) => f.page_id !== page.id)
      try {
        await pageService.removeFavorite(page.id)
      } catch (err) {
        favorites.value = before
        throw err
      }
    } else {
      favorites.value = [
        { page_id: page.id, title: page.title, slug: page.slug, space_id: space.id, space_key: space.key, space_name: space.name },
        ...before
      ]
      try {
        await pageService.addFavorite(page.id)
      } catch (err) {
        favorites.value = before
        throw err
      }
    }
  }

  /** Keep titles fresh after a rename */
  const updateTitle = (pageId: string, title: string, slug: string) => {
    favorites.value = favorites.value.map((f) => (f.page_id === pageId ? { ...f, title, slug } : f))
  }

  const reset = () => {
    favorites.value = []
    loaded.value = false
  }

  return { favorites, load, isFavorite, toggle, updateTitle, reset }
}

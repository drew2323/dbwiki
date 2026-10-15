import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * Lightweight cross-component signals for the CMS views, so that e.g. renaming
 * a page in the tree refreshes the open page and vice versa.
 */
export const useCmsStore = defineStore('cms', () => {
  /** Bumped whenever the page tree should be reloaded */
  const treeRevision = ref(0)
  /** Bumped whenever the currently open page should be reloaded */
  const pageRevision = ref(0)
  /** Bumped to open the search palette (e.g. from a toolbar button) */
  const searchRequest = ref(0)

  const refreshTree = () => { treeRevision.value++ }
  const refreshPage = () => { pageRevision.value++ }
  const openSearch = () => { searchRequest.value++ }

  return { treeRevision, pageRevision, searchRequest, refreshTree, refreshPage, openSearch }
})

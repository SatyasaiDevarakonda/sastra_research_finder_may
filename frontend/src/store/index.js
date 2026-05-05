import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const emptyRagState = {
  projectTitle: '',
  skills: '',
  searchOnline: true,
  analysisResult: null,
}

const emptyTeamBuilderState = {
  selectedThemes: [],
  themeSearch: '',
  expandedDomains: {},
  generatedTeams: null,
}

const emptyThematicState = {
  search: '',
  selectedTheme: null,
  expandedDomains: {},
}

const emptySearchPageState = {
  query: '',
  submittedQuery: '',
  activeTab: 'keyword',
}

// Main app store
export const useAppStore = create(
  persist(
    (set, get) => ({
      // Search state (legacy)
      searchQuery: '',
      searchResults: null,
      searchFilters: {
        year: null,
        school: null,
        documentType: null,
        thematicArea: null,
        isInternational: null,
      },

      // UI state
      sidebarOpen: true,
      activeTab: 'dashboard',

      // Cache
      filterOptions: null,
      stats: null,

      // Per-page state (survives tab/route switches so users don't lose work)
      ragState: { ...emptyRagState },
      teamBuilderState: { ...emptyTeamBuilderState },
      thematicState: { ...emptyThematicState },
      searchPageState: { ...emptySearchPageState },
      facultyEvalTabById: {},

      // Actions
      setSearchQuery: (query) => set({ searchQuery: query }),
      setSearchResults: (results) => set({ searchResults: results }),
      setSearchFilters: (filters) => set({
        searchFilters: { ...get().searchFilters, ...filters }
      }),
      clearSearchFilters: () => set({
        searchFilters: {
          year: null,
          school: null,
          documentType: null,
          thematicArea: null,
          isInternational: null,
        }
      }),

      toggleSidebar: () => set({ sidebarOpen: !get().sidebarOpen }),
      setActiveTab: (tab) => set({ activeTab: tab }),

      setFilterOptions: (options) => set({ filterOptions: options }),
      setStats: (stats) => set({ stats }),

      // Per-page state setters (merge so callers can update one field at a time)
      updateRagState: (patch) => set({ ragState: { ...get().ragState, ...patch } }),
      resetRagState: () => set({ ragState: { ...emptyRagState } }),

      updateTeamBuilderState: (patch) => set({ teamBuilderState: { ...get().teamBuilderState, ...patch } }),
      resetTeamBuilderState: () => set({ teamBuilderState: { ...emptyTeamBuilderState } }),

      updateThematicState: (patch) => set({ thematicState: { ...get().thematicState, ...patch } }),
      resetThematicState: () => set({ thematicState: { ...emptyThematicState } }),

      updateSearchPageState: (patch) => set({ searchPageState: { ...get().searchPageState, ...patch } }),

      setFacultyEvalTab: (authorId, tab) => set({
        facultyEvalTabById: { ...get().facultyEvalTabById, [authorId]: tab }
      }),

      // Reset
      reset: () => set({
        searchQuery: '',
        searchResults: null,
        searchFilters: {
          year: null,
          school: null,
          documentType: null,
          thematicArea: null,
          isInternational: null,
        },
      }),
    }),
    {
      name: 'sastra-research-finder',
      version: 2,
      partialize: (state) => ({
        sidebarOpen: state.sidebarOpen,
        searchFilters: state.searchFilters,
        // Persist per-page state including result payloads so a full page refresh
        // still restores the user's work. Payloads are small (few KB each).
        ragState: state.ragState,
        teamBuilderState: state.teamBuilderState,
        thematicState: state.thematicState,
        searchPageState: state.searchPageState,
        facultyEvalTabById: state.facultyEvalTabById,
      }),
      // Shallow merge (Zustand default) loses nested default keys when the
      // persisted slice is missing them. Deep-merge per-page slices so any
      // default field (e.g. `analysisResult: null`) is always present.
      merge: (persisted, current) => {
        const p = persisted || {}
        return {
          ...current,
          ...p,
          ragState: { ...current.ragState, ...(p.ragState || {}) },
          teamBuilderState: { ...current.teamBuilderState, ...(p.teamBuilderState || {}) },
          thematicState: { ...current.thematicState, ...(p.thematicState || {}) },
          searchPageState: { ...current.searchPageState, ...(p.searchPageState || {}) },
          facultyEvalTabById: { ...current.facultyEvalTabById, ...(p.facultyEvalTabById || {}) },
          searchFilters: { ...current.searchFilters, ...(p.searchFilters || {}) },
        }
      },
    }
  )
)

// Thematic areas store
export const useThematicStore = create((set) => ({
  selectedThemes: [],
  teams: null,
  rankings: {},

  addTheme: (theme) => set((state) => ({
    selectedThemes: state.selectedThemes.includes(theme)
      ? state.selectedThemes
      : [...state.selectedThemes, theme]
  })),

  removeTheme: (theme) => set((state) => ({
    selectedThemes: state.selectedThemes.filter(t => t !== theme)
  })),

  clearThemes: () => set({ selectedThemes: [] }),

  setTeams: (teams) => set({ teams }),

  setRankings: (theme, data) => set((state) => ({
    rankings: { ...state.rankings, [theme]: data }
  })),
}))

// Author store for profile viewing
export const useAuthorStore = create((set) => ({
  currentAuthor: null,
  recentlyViewed: [],
  favorites: [],

  setCurrentAuthor: (author) => set({ currentAuthor: author }),

  addToRecentlyViewed: (author) => set((state) => {
    const filtered = state.recentlyViewed.filter(a => a.author_id !== author.author_id)
    return {
      recentlyViewed: [author, ...filtered].slice(0, 10)
    }
  }),

  toggleFavorite: (author) => set((state) => {
    const isFavorite = state.favorites.some(a => a.author_id === author.author_id)
    return {
      favorites: isFavorite
        ? state.favorites.filter(a => a.author_id !== author.author_id)
        : [...state.favorites, author]
    }
  }),

  isFavorite: (authorId) => {
    const state = useAuthorStore.getState()
    return state.favorites.some(a => a.author_id === authorId)
  },
}))

export default useAppStore

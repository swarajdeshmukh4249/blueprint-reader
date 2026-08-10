import { create } from 'zustand'

export interface AnalysisContext {
  fileId?: string
  projectId?: string
  fileName?: string
  analysisId?: string
  fromPage?: string
  originPath?: string // The path user came from (e.g., '/upload', '/results')
}

interface NavigationStore {
  currentAnalysis: AnalysisContext | null
  setCurrentAnalysis: (context: AnalysisContext | null) => void
  clearCurrentAnalysis: () => void
  navigationHistory: string[]
  addToHistory: (path: string) => void
  lastUploadedFileId?: string
  setLastUploadedFileId: (id: string) => void
}

export const useNavigationStore = create<NavigationStore>((set) => ({
  currentAnalysis: null,
  setCurrentAnalysis: (context) => set({ currentAnalysis: context }),
  clearCurrentAnalysis: () => set({ currentAnalysis: null }),
  navigationHistory: [],
  addToHistory: (path) => set((state) => ({
    navigationHistory: [...state.navigationHistory, path].slice(-10) // Keep last 10
  })),
  lastUploadedFileId: undefined,
  setLastUploadedFileId: (id) => set({ lastUploadedFileId: id }),
}))
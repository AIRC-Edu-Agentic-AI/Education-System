import { create } from 'zustand'
import type { StudentProfile } from '../../types/domain'

interface ContextState {
  selectedModule: string
  selectedPresentation: string
  currentWeek: number
  numWeeks: number
  activeStudent: StudentProfile | null
  chatPanelOpen: boolean

  setModule: (m: string) => void
  setPresentation: (p: string) => void
  setCurrentWeek: (w: number) => void
  setNumWeeks: (n: number) => void
  setActiveStudent: (s: StudentProfile | null) => void
  setChatPanelOpen: (open: boolean) => void
}

export const useContextStore = create<ContextState>((set) => ({
  selectedModule: '',
  selectedPresentation: '',
  currentWeek: 15,
  numWeeks: 39,
  activeStudent: null,
  chatPanelOpen: false,

  setModule: (selectedModule) => set({ selectedModule }),
  setPresentation: (selectedPresentation) => set({ selectedPresentation }),
  setCurrentWeek: (currentWeek) => set({ currentWeek }),
  setNumWeeks: (numWeeks) => set({ numWeeks }),
  setActiveStudent: (activeStudent) => set({ activeStudent }),
  setChatPanelOpen: (chatPanelOpen) => set({ chatPanelOpen }),
}))

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type AssessmentFilter = 'all' | 'submitted' | 'late' | 'missing'
export type AssessmentSort  = 'date' | 'score' | 'weight'

interface StudentStore {
  // Assessment panel UI — persists as teacher preference across students
  assessmentFilter: AssessmentFilter
  assessmentSort:   AssessmentSort
  setAssessmentFilter: (f: AssessmentFilter) => void
  setAssessmentSort:   (s: AssessmentSort)   => void

  // Per-student teacher notes, keyed by id_student — persisted to localStorage
  notes: Record<number, string>
  setNote: (studentId: number, text: string) => void
}

export const useStudentStore = create<StudentStore>()(
  persist(
    (set) => ({
      assessmentFilter: 'all',
      assessmentSort:   'date',
      setAssessmentFilter: (f) => set({ assessmentFilter: f }),
      setAssessmentSort:   (s) => set({ assessmentSort:   s }),

      notes:   {},
      setNote: (studentId, text) =>
        set((state) => ({ notes: { ...state.notes, [studentId]: text } })),
    }),
    {
      name: 'teacher-dashboard:student',
      // Only persist teacher-authored data; UI preferences are intentionally also
      // kept so filter/sort survive full page reloads without rehydration cost.
      partialize: (s) => ({ notes: s.notes, assessmentFilter: s.assessmentFilter, assessmentSort: s.assessmentSort }),
    },
  ),
)

import type { DataService } from '../ports/DataService'
import type { OuladIndex, ProcessedCourse, ScheduleItem, StudentProfile } from '../types/domain'

// In-memory cache so we only fetch each file once per session
const cache = new Map<string, ProcessedCourse>()
let indexCache: OuladIndex | null = null

export class ProcessedDataAdapter implements DataService {
  async getIndex(): Promise<OuladIndex> {
    if (indexCache) return indexCache
    const res = await fetch('/processed/index.json')
    if (!res.ok) {
      throw new Error(
        'Preprocessed data not found. Run `npm run preprocess` first.'
      )
    }
    indexCache = await res.json() as OuladIndex
    return indexCache
  }

  async getCourse(module: string, presentation: string): Promise<ProcessedCourse> {
    const key = `${module}_${presentation}`
    if (cache.has(key)) return cache.get(key)!
    const res = await fetch(`/processed/${key}.json`)
    if (!res.ok) throw new Error(`No preprocessed data for ${module} ${presentation}`)
    const data = await res.json() as ProcessedCourse
    cache.set(key, data)
    return data
  }

  async getStudent(
    module: string,
    presentation: string,
    studentId: number
  ): Promise<StudentProfile | null> {
    const course = await this.getCourse(module, presentation)
    return course.students.find((s) => s.id_student === studentId) ?? null
  }

<<<<<<< HEAD
  async getSchedules(module: string, presentation: string) {
=======
  async getSchedules(module: string, presentation: string): Promise<ScheduleItem[]> {
>>>>>>> f2e6904 (Feature Update: Implement schedule persistence adapters.)
    const key = `schedules_${module}_${presentation}`
    try {
      const raw = localStorage.getItem(key)
      if (!raw) return []
<<<<<<< HEAD
      return JSON.parse(raw) as import('../types/domain').ScheduleItem[]
    } catch (e) {
      console.warn('Failed to load schedules from localStorage', e)
=======
      return JSON.parse(raw) as ScheduleItem[]
    } catch (error) {
      console.warn('Failed to load schedules from localStorage', error)
>>>>>>> f2e6904 (Feature Update: Implement schedule persistence adapters.)
      return []
    }
  }

<<<<<<< HEAD
  async saveSchedules(module: string, presentation: string, schedules: import('../types/domain').ScheduleItem[]) {
=======
  async saveSchedules(module: string, presentation: string, schedules: ScheduleItem[]): Promise<void> {
>>>>>>> f2e6904 (Feature Update: Implement schedule persistence adapters.)
    const key = `schedules_${module}_${presentation}`
    localStorage.setItem(key, JSON.stringify(schedules))
  }
}

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

  
  async getSchedules(module?: string, presentation?: string): Promise<ScheduleItem[]> {
    try {
      if (module && presentation) {
        const data = localStorage.getItem(`schedules_${module}_${presentation}`)
        return data ? JSON.parse(data) : []
      }

      const schedules: ScheduleItem[] = []
      for (let i = 0; i < localStorage.length; i += 1) {
        const key = localStorage.key(i)
        if (!key || !key.startsWith('schedules_')) continue
        const data = localStorage.getItem(key)
        if (!data) continue
        try {
          const parsed = JSON.parse(data) as ScheduleItem[]
          schedules.push(...parsed.map((item) => ({
            ...item,
            module: (item as ScheduleItem & { module?: string }).module || key.split('_')[1],
            presentation: (item as ScheduleItem & { presentation?: string }).presentation || key.split('_')[2],
          })))
        } catch {
          continue
        }
      }
      return schedules
    } catch (e) {
      console.error('Error loading schedules from localStorage', e)
      return []
    }
  }

  async saveSchedules(schedules: ScheduleItem[], module?: string, presentation?: string, newSchedule?: ScheduleItem): Promise<void> {
    try {
      if (module && presentation) {
        localStorage.setItem(`schedules_${module}_${presentation}`, JSON.stringify(schedules))
        return
      }
      localStorage.setItem('schedules_all', JSON.stringify(schedules))
    } catch (e) {
      console.error('Error saving schedules to localStorage', e)
      throw new Error('Failed to save schedules')
    }
  }
}

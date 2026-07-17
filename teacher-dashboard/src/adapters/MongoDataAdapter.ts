import type { DataService } from '../ports/DataService'
import type { OuladIndex, ProcessedCourse, ScheduleItem, StudentProfile } from '../types/domain'

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000/api'

export class MongoDataAdapter implements DataService {
  async getIndex(): Promise<OuladIndex> {
    const res = await fetch(`${API_BASE}/index`)
    if (!res.ok) throw new Error('Cannot reach MongoDB API')
    return await res.json() as OuladIndex
  }

  async getCourse(module: string, presentation: string): Promise<ProcessedCourse> {
    const res = await fetch(`${API_BASE}/course/${module}/${presentation}`)
    if (!res.ok) throw new Error(`Course ${module} ${presentation} not found`)
    return await res.json() as ProcessedCourse
  }

  async getStudent(module: string, presentation: string, studentId: number): Promise<StudentProfile | null> {
    const res = await fetch(`${API_BASE}/student/${module}/${presentation}/${studentId}`)
    if (!res.ok) return null
    return await res.json() as StudentProfile
  }

  async getSchedules(module?: string, presentation?: string): Promise<ScheduleItem[]> {
    const endpoint = module && presentation
      ? `${API_BASE}/schedules/${module}/${presentation}`
      : `${API_BASE}/schedules`
    const res = await fetch(endpoint)
    if (!res.ok) throw new Error('Cannot reach schedules API')
    const body = await res.json()

    if (Array.isArray(body)) {
      return body as ScheduleItem[]
    }

    if (Array.isArray(body?.schedules)) {
      return body.schedules as ScheduleItem[]
    }

    if (Array.isArray(body?.data)) {
      return body.data as ScheduleItem[]
    }

    return [] as ScheduleItem[]
  }

  async saveSchedules(schedules: ScheduleItem[], module?: string, presentation?: string): Promise<void> {
    const endpoint = module && presentation
      ? `${API_BASE}/schedules/${module}/${presentation}`
      : `${API_BASE}/schedules`
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ schedules }),
    })
    if (!res.ok) throw new Error('Failed to save schedules')
  }
}

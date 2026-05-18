import type { DataService } from '../ports/DataService'
import type { OuladIndex, ProcessedCourse, StudentProfile } from '../types/domain'

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
}
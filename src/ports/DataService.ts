import type { OuladIndex, ProcessedCourse, StudentProfile } from '../types/domain'

export interface DataService {
  /** Returns the index of available modules and presentations. */
  getIndex(): Promise<OuladIndex>

  /** Returns full student profiles for a module + presentation. */
  getCourse(module: string, presentation: string): Promise<ProcessedCourse>

  /** Convenience: returns a single student profile from the loaded course. */
  getStudent(
    module: string,
    presentation: string,
    studentId: number
  ): Promise<StudentProfile | null>

  /** Scheduling APIs: get and save teaching schedules for a course */
  getSchedules(module: string, presentation: string): Promise<import('../types/domain').ScheduleItem[]>
  saveSchedules(module: string, presentation: string, schedules: import('../types/domain').ScheduleItem[]): Promise<void>
}

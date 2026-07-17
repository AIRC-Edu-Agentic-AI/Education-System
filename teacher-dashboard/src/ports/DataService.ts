import type { OuladIndex, ProcessedCourse, ScheduleItem, StudentProfile } from '../types/domain'

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

  /** Scheduling APIs: get and save teaching schedules for a course or for all teacher schedules. */
  getSchedules(module?: string, presentation?: string): Promise<ScheduleItem[]>
  saveSchedules(schedules: ScheduleItem[], module?: string, presentation?: string): Promise<void>
}

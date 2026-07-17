import type { AssessmentRecord, ConceptGraph } from '../types/domain'

export interface MasteryService {
  /**
   * Returns the concept mastery graph for a student.
   * In pilot: derives mastery from assessment performance.
   * In deployment: queries Neo4j G_course.
   */
  getConceptGraph(studentId: number, module: string, assessments?: AssessmentRecord[]): Promise<ConceptGraph>
}

// ─── OULAD raw shapes (mirrors CSV columns) ──────────────────────────────────

export interface RawStudentInfo {
  code_module: string
  code_presentation: string
  id_student: number
  gender: string
  region: string
  highest_education: string
  imd_band: string
  age_band: string
  num_of_prev_attempts: number
  studied_credits: number
  disability: string
  final_result: string
}

export interface RawStudentRegistration {
  code_module: string
  code_presentation: string
  id_student: number
  date_registration: number
  date_unregistration: number | null
}

export interface RawStudentAssessment {
  id_assessment: number
  id_student: number
  date_submitted: number
  is_banked: number
  score: number | null
}

export interface RawAssessment {
  code_module: string
  code_presentation: string
  id_assessment: number
  assessment_type: string
  date: number
  weight: number
}

export interface RawVleInteraction {
  code_module: string
  code_presentation: string
  id_student: number
  id_site: number
  date: number
  sum_click: number
}

export interface RawCourse {
  code_module: string
  code_presentation: string
  module_presentation_length: number
}

// ─── Preprocessed / domain objects ───────────────────────────────────────────

export type Tier = 1 | 2 | 3

export interface AssessmentRecord {
  id_assessment: number
  assessment_type: string
  date_due: number | null
  weight: number | null
  score: number | null
  date_submitted: number | null
}

export interface StudentProfile {
  id_student: number
  gender: string
  region: string
  highest_education: string
  imd_band: string
  age_band: string
  num_of_prev_attempts: number
  studied_credits: number
  disability: boolean
  final_result: string
  date_registration: number
  date_unregistration: number | null
  // Time-series arrays indexed 0 = week 1
  weekly_clicks: number[]
  decayed_engagement: number[]
  assessments: AssessmentRecord[]
  risk_by_week: (number | null)[]
  tier_by_week: (Tier | null)[]
  lstm_trajectories: {
    w05: (number | null)[]
    w10: (number | null)[]
    w15: (number | null)[]
    w20: (number | null)[]
    w25: (number | null)[]
  } | null
}

export interface CourseIndex {
  module: string
  presentation: string
  num_weeks: number
  student_count: number
}

export interface OuladIndex {
  courses: CourseIndex[]
}

export interface ProcessedCourse {
  module: string
  presentation: string
  num_weeks: number
  students: StudentProfile[]
  cohort_p75_decayed: number[]
}

// ─── Chat / Agent ─────────────────────────────────────────────────────────────

export type MessageRole = 'user' | 'assistant'

export interface ChatMessage {
  id: string
  role: MessageRole
  content: string
  timestamp: Date
}

export interface AgentContext {
  module: string
  presentation: string
  currentWeek: number
  numWeeks: number
  activeStudent: StudentProfile | null
  tierCounts: { tier1: number; tier2: number; tier3: number }
}

// ─── Concept Mastery Graph ────────────────────────────────────────────────────

export interface ConceptNode {
  id: string
  label: string
  mastery: number       // [0, 1]
  confidence: number    // [0, 1]
  evidence_count: number
  topic_group: number
}

export interface ConceptEdge {
  source: string        // concept_id
  target: string        // concept_id (target depends on source)
}

export interface ConceptGraph {
  nodes: ConceptNode[]
  edges: ConceptEdge[]
  subject_domain: string
}

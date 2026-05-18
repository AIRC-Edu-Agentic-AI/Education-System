import type { MasteryService } from '../ports/MasteryService'
import type { AssessmentRecord, ConceptGraph, ConceptNode, ConceptEdge } from '../types/domain'

// Domain templates keyed by first letter of module code
const DOMAINS: Record<string, { name: string; nodes: Omit<ConceptNode, 'mastery' | 'confidence' | 'evidence_count'>[] ; edges: ConceptEdge[] }> = {
  STEM: {
    name: 'Computer Science',
    nodes: [
      { id: 'prog', label: 'Programming basics', topic_group: 1 },
      { id: 'vars', label: 'Variables & types', topic_group: 1 },
      { id: 'flow', label: 'Control flow', topic_group: 1 },
      { id: 'funcs', label: 'Functions', topic_group: 1 },
      { id: 'ds', label: 'Data structures', topic_group: 2 },
      { id: 'arr', label: 'Arrays & lists', topic_group: 2 },
      { id: 'maps', label: 'Hash maps', topic_group: 2 },
      { id: 'trees', label: 'Trees & graphs', topic_group: 2 },
      { id: 'algo', label: 'Algorithms', topic_group: 3 },
      { id: 'sort', label: 'Sorting', topic_group: 3 },
      { id: 'srch', label: 'Search', topic_group: 3 },
      { id: 'cmplx', label: 'Complexity', topic_group: 3 },
    ],
    edges: [
      { source: 'prog', target: 'vars' }, { source: 'prog', target: 'flow' },
      { source: 'vars', target: 'flow' }, { source: 'flow', target: 'funcs' },
      { source: 'funcs', target: 'ds' }, { source: 'ds', target: 'arr' },
      { source: 'ds', target: 'maps' }, { source: 'ds', target: 'trees' },
      { source: 'arr', target: 'trees' }, { source: 'funcs', target: 'algo' },
      { source: 'ds', target: 'algo' }, { source: 'algo', target: 'sort' },
      { source: 'algo', target: 'srch' }, { source: 'sort', target: 'cmplx' },
      { source: 'srch', target: 'cmplx' },
    ],
  },
  SOCIAL: {
    name: 'Social Sciences',
    nodes: [
      { id: 'theory', label: 'Social theory', topic_group: 1 },
      { id: 'research', label: 'Research methods', topic_group: 1 },
      { id: 'quant', label: 'Quantitative analysis', topic_group: 1 },
      { id: 'qual', label: 'Qualitative methods', topic_group: 2 },
      { id: 'policy', label: 'Policy analysis', topic_group: 2 },
      { id: 'ethics', label: 'Research ethics', topic_group: 2 },
      { id: 'writing', label: 'Academic writing', topic_group: 3 },
      { id: 'critique', label: 'Critical analysis', topic_group: 3 },
      { id: 'synthesis', label: 'Literature synthesis', topic_group: 3 },
    ],
    edges: [
      { source: 'theory', target: 'research' }, { source: 'research', target: 'quant' },
      { source: 'research', target: 'qual' }, { source: 'quant', target: 'policy' },
      { source: 'qual', target: 'policy' }, { source: 'ethics', target: 'research' },
      { source: 'policy', target: 'writing' }, { source: 'theory', target: 'critique' },
      { source: 'writing', target: 'synthesis' }, { source: 'critique', target: 'synthesis' },
    ],
  },
  GENERIC: {
    name: 'General Studies',
    nodes: [
      { id: 'intro', label: 'Introduction', topic_group: 1 },
      { id: 'core1', label: 'Core concepts I', topic_group: 1 },
      { id: 'core2', label: 'Core concepts II', topic_group: 1 },
      { id: 'apply1', label: 'Application I', topic_group: 2 },
      { id: 'apply2', label: 'Application II', topic_group: 2 },
      { id: 'adv', label: 'Advanced topics', topic_group: 3 },
      { id: 'synthesis', label: 'Synthesis', topic_group: 3 },
    ],
    edges: [
      { source: 'intro', target: 'core1' }, { source: 'intro', target: 'core2' },
      { source: 'core1', target: 'apply1' }, { source: 'core2', target: 'apply2' },
      { source: 'apply1', target: 'adv' }, { source: 'apply2', target: 'adv' },
      { source: 'adv', target: 'synthesis' },
    ],
  },
}

function domainFor(module: string): typeof DOMAINS['STEM'] {
  const m = module.toUpperCase()
  // OULAD: CCC, DDD, EEE, FFF = STEM-ish; BBB, GGG = Social; else Generic
  if (['C', 'D', 'E', 'F'].includes(m[0])) return DOMAINS.STEM
  if (['B', 'G'].includes(m[0])) return DOMAINS.SOCIAL
  return DOMAINS.GENERIC
}

// Small seeded noise for per-concept variation within the same group
function seededNoise(seed: number): number {
  const x = Math.sin(seed) * 10000
  return (x - Math.floor(x)) * 0.14 - 0.07
}

// Weighted average score for a subset of assessments, normalised to [0, 1]
function weightedAvg(rows: AssessmentRecord[]): number | null {
  const scored = rows.filter((a) => a.score !== null)
  if (scored.length === 0) return null
  const totalW = scored.reduce((s, a) => s + (a.weight ?? 1), 0)
  if (totalW === 0) return null
  return scored.reduce((s, a) => s + (a.score ?? 0) * (a.weight ?? 1), 0) / totalW / 100
}

export class MockMasteryAdapter implements MasteryService {
  async getConceptGraph(studentId: number, module: string, assessments: AssessmentRecord[] = []): Promise<ConceptGraph> {
    const domain = domainFor(module)

    // Exclude phantom exams (weight 100, no result)
    const real = assessments.filter((a) => !(a.weight === 100 && a.score === null))

    // Per-type performance: CMA = formative, TMA = coursework, Exam = summative
    const byType = (type: string) =>
      real.filter((a) => a.assessment_type.toUpperCase() === type)

    const cmaPerf  = weightedAvg(byType('CMA'))
    const tmaPerf  = weightedAvg(byType('TMA'))
    const examPerf = weightedAvg(byType('EXAM'))
    const overall  = weightedAvg(real) ?? 0.5

    // topic_group 1 (foundations) → CMA, group 2 (applied) → TMA, group 3 (advanced) → Exam
    const groupBase = (group: number) => {
      if (group === 1) return cmaPerf  ?? overall
      if (group === 2) return tmaPerf  ?? overall
      return               examPerf ?? overall
    }

    const evidence_count = real.filter((a) => a.score !== null).length

    const nodes: ConceptNode[] = domain.nodes.map((n, i) => {
      const noise = seededNoise(studentId * 31 + i * 7)
      const mastery = Math.max(0.05, Math.min(0.98, groupBase(n.topic_group) + noise))
      return {
        ...n,
        mastery: Math.round(mastery * 100) / 100,
        evidence_count,
        confidence: Math.min(1, evidence_count / 8),
      }
    })

    return {
      nodes,
      edges: domain.edges,
      subject_domain: domain.name,
    }
  }
}

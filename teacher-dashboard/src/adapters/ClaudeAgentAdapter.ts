import type { AgentService } from '../ports/AgentService'
import type { ChatMessage, AgentContext } from '../types/domain'

const MODEL = 'claude-sonnet-4-20250514'
const API_URL = '/api/claude/v1/messages'

function buildSystemPrompt(ctx: AgentContext): string {
  const studentBlock = ctx.activeStudent
    ? `Active student: #${ctx.activeStudent.id_student} | ` +
      `Tier ${ctx.activeStudent.tier_by_week[ctx.currentWeek - 1]} | ` +
      `Risk ${((ctx.activeStudent.risk_by_week[ctx.currentWeek - 1] ?? 0) * 100).toFixed(0)}% | ` +
      `IMD band: ${ctx.activeStudent.imd_band} | ` +
      `Prior attempts: ${ctx.activeStudent.num_of_prev_attempts}`
    : 'No student selected (discussing class-level data)'

  return `You are a pedagogical advisor integrated into an RTI/MTSS teacher dashboard for higher education.

CURRENT CONTEXT
- Module: ${ctx.module} | Presentation: ${ctx.presentation}
- Week: ${ctx.currentWeek} of ${ctx.numWeeks}
- ${studentBlock}
- Cohort tier distribution — Tier 1 (low risk): ${ctx.tierCounts.tier1} | Tier 2: ${ctx.tierCounts.tier2} | Tier 3 (high risk): ${ctx.tierCounts.tier3}

RISK MODEL (OULAD-derived heuristic)
Risk score = 1 − (0.45 × assessment performance + 0.35 × VLE engagement + 0.20 × submission rate)
Tier thresholds: Tier 1 < 0.33 · Tier 2 [0.33–0.66) · Tier 3 ≥ 0.66

GUIDANCE
When asked about interventions, use the RTI/MTSS framework:
- Tier 1: Universal support — quality teaching, peer learning, structured check-ins
- Tier 2: Targeted — small group tutoring, formative assessment, study skills coaching
- Tier 3: Intensive — 1-on-1 mentoring, withdrawal risk protocol, pastoral referral

Be specific, evidence-based, and actionable. Cite the student's actual risk score and engagement patterns when relevant. Keep responses concise and practical for a busy instructor.`
}

export class ClaudeAgentAdapter implements AgentService {
  async *stream(messages: ChatMessage[], context: AgentContext): AsyncIterable<string> {
    const body = JSON.stringify({
      model: MODEL,
      max_tokens: 1024,
      system: buildSystemPrompt(context),
      stream: true,
      messages: messages.map((m) => ({ role: m.role, content: m.content })),
    })

    const res = await fetch(API_URL, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body,
    })

    if (!res.ok) {
      const err = await res.text()
      throw new Error(`Claude API error ${res.status}: ${err}`)
    }

    if (!res.body) throw new Error('No response body')

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const data = line.slice(6).trim()
        if (data === '[DONE]') return

        try {
          const event = JSON.parse(data)
          if (event.type === 'content_block_delta' && event.delta?.type === 'text_delta') {
            yield event.delta.text as string
          }
        } catch {
          // Ignore malformed SSE lines
        }
      }
    }
  }
}

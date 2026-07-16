import { Box, Card, Typography, Chip } from '@mui/material'
import { TIER_COLORS, type TierNumber } from '../../../shared/constants/tiers'
import type { StudentProfile } from '../../../types/domain'

interface Props {
  students: StudentProfile[]
  currentWeek: number
}

const TIER_LABELS: Record<TierNumber, { heading: string; description: string }> = {
  1: { heading: 'Tier 1 — Low risk',   description: 'Universal support' },
  2: { heading: 'Tier 2 — Moderate',   description: 'Targeted intervention' },
  3: { heading: 'Tier 3 — High risk',  description: 'Intensive support' },
}

export function RiskTilesRow({ students, currentWeek }: Props) {
  const weekIdx = Math.max(0, currentWeek - 1)
  const counts = { 1: 0, 2: 0, 3: 0 } as Record<TierNumber, number>
  let totalRisk = 0

  for (const s of students) {
    const tier = (s.tier_by_week[weekIdx] ?? 1) as TierNumber
    counts[tier]++
    totalRisk += s.risk_by_week[weekIdx] ?? 0
  }

  const avgRisk = students.length > 0 ? totalRisk / students.length : 0

  return (
    <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 2, mb: 3 }}>
      {([1, 2, 3] as TierNumber[]).map((tier) => {
        const tc  = TIER_COLORS[tier]
        const lbl = TIER_LABELS[tier]
        const pct = students.length > 0 ? Math.round((counts[tier] / students.length) * 100) : 0
        return (
          <Card key={tier} sx={{ p: 2.5, bgcolor: tc.subtle, border: `1px solid ${tc.solid}22`, position: 'relative', overflow: 'hidden' }}>
            <Box sx={{ position: 'absolute', top: 0, left: 0, width: `${pct}%`, height: 3, bgcolor: tc.solid, borderRadius: '2px 0 0 0' }} />
            <Typography sx={{ fontSize: 11, color: tc.text, fontFamily: 'inherit', fontWeight: 500, mb: 1 }}>
              {lbl.heading}
            </Typography>
            <Typography sx={{ fontSize: 36, fontWeight: 600, color: 'text.primary', lineHeight: 1 }}>
              {counts[tier]}
            </Typography>
            <Typography sx={{ fontSize: 12, color: 'text.secondary', mt: 0.5 }}>
              {pct}% of cohort
            </Typography>
            <Typography sx={{ fontSize: 11, color: tc.text, mt: 1 }}>
              {lbl.description}
            </Typography>
          </Card>
        )
      })}

      <Card sx={{ p: 2.5 }}>
        <Typography sx={{ fontSize: 11, color: 'text.secondary', fontWeight: 500, mb: 1 }}>
          Cohort avg. risk
        </Typography>
        <Typography sx={{ fontSize: 36, fontWeight: 600, color: 'text.primary', lineHeight: 1 }}>
          {(avgRisk * 100).toFixed(0)}%
        </Typography>
        <Typography sx={{ fontSize: 12, color: 'text.secondary', mt: 0.5 }}>
          {students.length} students total
        </Typography>
        <Chip
          label={avgRisk < 0.33 ? 'Low' : avgRisk < 0.66 ? 'Moderate' : 'High'}
          size="small"
          sx={{
            mt: 1, fontSize: 11, height: 20,
            bgcolor: avgRisk < 0.33 ? TIER_COLORS[1].subtle : avgRisk < 0.66 ? TIER_COLORS[2].subtle : TIER_COLORS[3].subtle,
            color:   avgRisk < 0.33 ? TIER_COLORS[1].text   : avgRisk < 0.66 ? TIER_COLORS[2].text   : TIER_COLORS[3].text,
          }}
        />
      </Card>
    </Box>
  )
}

import { Card, CardContent, Typography, Box } from '@mui/material'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { TIER_COLORS } from '../../../shared/constants/tiers'
import { tokens } from '../../../theme'
import type { StudentProfile } from '../../../types/domain'

interface Props {
  students: StudentProfile[]
  currentWeek: number
}

const BINS = [
  { label: '0–10',   min: 0,   max: 10  },
  { label: '10–20',  min: 10,  max: 20  },
  { label: '20–30',  min: 20,  max: 30  },
  { label: '30–40',  min: 30,  max: 40  },
  { label: '40–50',  min: 40,  max: 50  },
  { label: '50–60',  min: 50,  max: 60  },
  { label: '60–70',  min: 60,  max: 70  },
  { label: '70–80',  min: 70,  max: 80  },
  { label: '80–90',  min: 80,  max: 90  },
  { label: '90–100', min: 90,  max: 101 },
]

function binColor(label: string) {
  if (label === 'N/A') return tokens.text.muted
  const lower = parseInt(label)
  return lower >= 50 ? TIER_COLORS[1].solid : TIER_COLORS[3].solid
}

export function MarkDistributionChart({ students, currentWeek }: Props) {
  const weekDay = currentWeek * 7
  const mono = tokens.font.mono

  let notSubmitted = 0
  const scores: number[] = []

  for (const student of students) {
    const due = (student.assessments ?? []).filter(
      (a) => a.date_due != null && a.date_due <= weekDay,
    )
    if (due.length === 0) continue

    const scored = due.filter((a) => a.score != null)
    if (scored.length === 0) { notSubmitted++; continue }

    const totalWeight = scored.reduce((s, a) => s + (a.weight ?? 1), 0)
    const weightedSum = scored.reduce((s, a) => s + a.score! * (a.weight ?? 1), 0)
    scores.push(totalWeight > 0 ? weightedSum / totalWeight : 0)
  }

  const data = [
    ...BINS.map((b) => ({ label: b.label, count: scores.filter((s) => s >= b.min && s < b.max).length })),
    { label: 'N/A', count: notSubmitted },
  ]

  const hasData = scores.length > 0 || notSubmitted > 0

  return (
    <Card>
      <CardContent>
        <Typography sx={{ fontSize: 13, fontWeight: 500, color: 'text.primary', mb: 0.5 }}>
          Mark distribution — Week {currentWeek}
        </Typography>
        <Typography sx={{ fontSize: 11, color: 'text.secondary', fontFamily: mono, mb: 2 }}>
          Weighted avg score per student across assessments due so far
        </Typography>

        {!hasData ? (
          <Box sx={{ height: 140, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Typography sx={{ fontSize: 12, color: 'text.muted', fontFamily: mono }}>
              No assessments due by week {currentWeek}
            </Typography>
          </Box>
        ) : (
          <ResponsiveContainer width="100%" height={140}>
            <BarChart data={data} margin={{ top: 4, right: 8, left: -20, bottom: 0 }} barCategoryGap="10%">
              <CartesianGrid strokeDasharray="3 3" stroke={tokens.surface.subtle} vertical={false} />
              <XAxis dataKey="label" tick={{ fontSize: 9, fontFamily: mono }} interval={0} />
              <YAxis allowDecimals={false} tick={{ fontSize: 10, fontFamily: mono }} />
              <Tooltip
                contentStyle={{ fontSize: 12, fontFamily: mono, borderRadius: 8, border: `1px solid ${tokens.border.default}` }}
                formatter={(v: number) => [`${v} students`, 'Count']}
              />
              <Bar dataKey="count" radius={[2, 2, 0, 0]}>
                {data.map((d) => <Cell key={d.label} fill={binColor(d.label)} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}

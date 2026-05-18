import { Card, CardContent, Typography, Box, Chip } from '@mui/material'
import {
  ComposedChart, Line, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, ReferenceLine,
} from 'recharts'
import type { StudentProfile, Tier } from '../../../types/domain'

interface Props {
  student: StudentProfile
  currentWeek: number
}

const TIER_COLORS: Record<Tier, { bg: string; text: string }> = {
  1: { bg: '#E1F5EE', text: '#0F6E56' },
  2: { bg: '#FAEEDA', text: '#854F0B' },
  3: { bg: '#FCEBEB', text: '#A32D2D' },
}

// Pick the freshest LSTM horizon whose training cutoff ≤ currentWeek.
// Horizons: w05 activates at week 5, w10 at 10, etc.
function pickHorizon(currentWeek: number): 'w05' | 'w10' | 'w15' | 'w20' | 'w25' {
  if (currentWeek >= 25) return 'w25'
  if (currentWeek >= 20) return 'w20'
  if (currentWeek >= 15) return 'w15'
  if (currentWeek >= 10) return 'w10'
  return 'w05'
}

function riskToTier(risk: number): Tier {
  if (risk < 0.33) return 1
  if (risk < 0.66) return 2
  return 3
}

export function RiskTrajectoryChart({ student, currentWeek }: Props) {
  const weekIdx = Math.max(0, currentWeek - 1)

  // Select the appropriate LSTM trajectory column
  const traj = student.lstm_trajectories
  const horizon = pickHorizon(currentWeek)
  const trajectory: (number | null)[] = traj?.[horizon] ?? student.risk_by_week

  const risk = trajectory[weekIdx] ?? 0
  const tier = riskToTier(risk)
  const tc   = TIER_COLORS[tier]

  // CWS(w) = Σ(score × weight, on-time by w) / Σ(weight, due by w) × 100
  const data = trajectory.map((r, i) => {
    const week    = i + 1
    const isPast  = week <= currentWeek
    const currentDay = week * 7
    const due = (student.assessments ?? []).filter(
      (a) => a.date_due != null && a.date_due <= currentDay
        && !(a.weight === 100 && a.score === null),
    )
    let cws: number | null = null
    if (isPast && due.length > 0) {
      const totalWeight = due.reduce((s, a) => s + (a.weight ?? 0), 0)
      if (totalWeight > 0) {
        const weightedScore = due
          .filter((a) => a.date_submitted != null && a.date_submitted <= currentDay)
          .reduce((s, a) => s + (a.score ?? 0) * (a.weight ?? 0), 0)
        cws = Math.round((weightedScore / totalWeight) * 10) / 10
      }
    }
    return {
      week,
      riskSolid:  isPast ? r : null,
      riskDotted: !isPast || week === currentWeek ? r : null,
      cws,
    }
  })

  return (
    <Card elevation={0} sx={{ borderRadius: 2, border: '1px solid #E5E3DC' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <Box>
            <Typography sx={{ fontSize: 11, color: '#6B7280', fontFamily: '"IBM Plex Mono", monospace' }}>
              Risk score — Week {currentWeek}
            </Typography>
            <Typography sx={{ fontSize: 32, fontWeight: 600, fontFamily: '"IBM Plex Mono", monospace', color: '#0A1628', lineHeight: 1.2 }}>
              {(risk * 100).toFixed(0)}%
            </Typography>
          </Box>
          <Chip label={`Tier ${tier}`} sx={{ bgcolor: tc.bg, color: tc.text, fontFamily: '"IBM Plex Mono", monospace', fontWeight: 500, fontSize: 13 }} />
          <Chip
            label={`LSTM ${horizon.replace('w', 'W')}`}
            sx={{ bgcolor: '#F3F4F6', color: '#6B7280', fontFamily: '"IBM Plex Mono", monospace', fontSize: 11 }}
          />
          {student.final_result === 'Withdrawn' && (
            <Chip label="Withdrawn" sx={{ bgcolor: '#F3F4F6', color: '#6B7280', fontFamily: '"IBM Plex Mono", monospace', fontWeight: 500, fontSize: 13 }} />
          )}
        </Box>

        <Typography sx={{ fontSize: 12, fontWeight: 500, color: '#0A1628', mb: 1 }}>
          Risk trajectory &amp; weighted score
        </Typography>

        <ResponsiveContainer width="100%" height={180}>
          <ComposedChart data={data} margin={{ top: 4, right: 36, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#F0EFE9" />
            <XAxis dataKey="week" tick={{ fontSize: 10, fontFamily: '"IBM Plex Mono"' }} />
            <YAxis yAxisId="left"  domain={[0, 1]}   tick={{ fontSize: 10, fontFamily: '"IBM Plex Mono"' }} />
            <YAxis yAxisId="right" orientation="right" domain={[0, 100]} tick={{ fontSize: 10, fontFamily: '"IBM Plex Mono"' }} tickFormatter={(v) => `${v}%`} />
            <Tooltip
              contentStyle={{ fontSize: 12, fontFamily: '"IBM Plex Mono"', borderRadius: 8 }}
              labelFormatter={(v) => `Week ${v}`}
              formatter={(value: number, name: string) => {
                if (name === 'riskSolid' || name === 'Risk') return [`${(value * 100).toFixed(0)}%`, 'Risk']
                return [`${value.toFixed(1)}%`, 'Weighted score']
              }}
            />
            <Legend iconType="plainline" wrapperStyle={{ fontSize: 11, fontFamily: '"IBM Plex Mono", monospace' }}
              formatter={(v) => v === 'Risk' ? 'Risk (LSTM)' : 'Weighted score'} />
            <ReferenceLine yAxisId="left" y={0.33} stroke="#1D9E75" strokeDasharray="3 3" />
            <ReferenceLine yAxisId="left" y={0.66} stroke="#EF9F27" strokeDasharray="3 3" />
            <ReferenceLine yAxisId="left" x={currentWeek} stroke="#0A1628" strokeDasharray="4 3" strokeWidth={1.5} />
            <Bar yAxisId="right" dataKey="cws" name="Weighted score" fill="#6366F1" fillOpacity={0.25} radius={[2, 2, 0, 0]} />
            <Line yAxisId="left" type="monotone" dataKey="riskSolid"  name="riskSolid" stroke="#0A1628" strokeWidth={2} dot={false} connectNulls={false} legendType="none" />
            <Line yAxisId="left" type="monotone" dataKey="riskDotted" name="Risk"       stroke="#0A1628" strokeWidth={2} dot={false} connectNulls={false} strokeDasharray="5 3" />
          </ComposedChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

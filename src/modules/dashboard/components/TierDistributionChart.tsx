import { Card, CardContent, Typography } from '@mui/material'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { TIER_COLORS } from '../../../shared/constants/tiers'
import { tokens } from '../../../theme'
import type { StudentProfile } from '../../../types/domain'

interface Props {
  students: StudentProfile[]
  numWeeks: number
  currentWeek: number
}

export function TierDistributionChart({ students, numWeeks, currentWeek }: Props) {
  const data = Array.from({ length: numWeeks }, (_, wi) => {
    let t1 = 0, t2 = 0, t3 = 0
    for (const s of students) {
      const tier = s.tier_by_week[wi] ?? 1
      if (tier === 1) t1++
      else if (tier === 2) t2++
      else t3++
    }
    return { week: wi + 1, 'Tier 1': t1, 'Tier 2': t2, 'Tier 3': t3 }
  })

  const mono = tokens.font.mono

  return (
    <Card>
      <CardContent>
        <Typography sx={{ fontSize: 13, fontWeight: 500, color: 'text.primary', mb: 2 }}>
          Tier distribution over time
        </Typography>
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={data} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="t1" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor={TIER_COLORS[1].solid} stopOpacity={0.5} />
                <stop offset="95%" stopColor={TIER_COLORS[1].solid} stopOpacity={0.05} />
              </linearGradient>
              <linearGradient id="t2" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor={tokens.brand.secondary} stopOpacity={0.5} />
                <stop offset="95%" stopColor={tokens.brand.secondary} stopOpacity={0.05} />
              </linearGradient>
              <linearGradient id="t3" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor={TIER_COLORS[3].solid} stopOpacity={0.5} />
                <stop offset="95%" stopColor={TIER_COLORS[3].solid} stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={tokens.surface.subtle} />
            <XAxis dataKey="week" tick={{ fontSize: 11, fontFamily: mono }} label={{ value: 'Week', position: 'insideBottom', offset: -2, fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11, fontFamily: mono }} />
            <Tooltip
              contentStyle={{ fontSize: 12, fontFamily: mono, borderRadius: 8, border: `1px solid ${tokens.border.default}` }}
              labelFormatter={(v) => `Week ${v}`}
            />
            <ReferenceLine x={currentWeek} stroke={tokens.text.primary} strokeDasharray="4 3" strokeWidth={1.5} label={{ value: 'now', position: 'top', fontSize: 10, fontFamily: mono }} />
            <Area type="monotone" dataKey="Tier 1" stackId="1" stroke={TIER_COLORS[1].solid} fill="url(#t1)" strokeWidth={1.5} />
            <Area type="monotone" dataKey="Tier 2" stackId="1" stroke={tokens.brand.secondary} fill="url(#t2)" strokeWidth={1.5} />
            <Area type="monotone" dataKey="Tier 3" stackId="1" stroke={TIER_COLORS[3].solid} fill="url(#t3)" strokeWidth={1.5} />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

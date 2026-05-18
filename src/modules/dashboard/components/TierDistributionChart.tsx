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

  return (
    <Card elevation={0} sx={{ borderRadius: 2, border: '1px solid #E5E3DC', bgcolor: '#fff' }}>
      <CardContent>
        <Typography sx={{ fontSize: 13, fontWeight: 500, color: '#0A1628', fontFamily: '"IBM Plex Sans", sans-serif', mb: 2 }}>
          Tier distribution over time
        </Typography>
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={data} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="t1" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#1D9E75" stopOpacity={0.5} />
                <stop offset="95%" stopColor="#1D9E75" stopOpacity={0.05} />
              </linearGradient>
              <linearGradient id="t2" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={tokens.brand.secondary} stopOpacity={0.5} />
                <stop offset="95%" stopColor={tokens.brand.secondary} stopOpacity={0.05} />
              </linearGradient>
              <linearGradient id="t3" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#E24B4A" stopOpacity={0.5} />
                <stop offset="95%" stopColor="#E24B4A" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#F0EFE9" />
            <XAxis dataKey="week" tick={{ fontSize: 11, fontFamily: '"IBM Plex Mono"' }} label={{ value: 'Week', position: 'insideBottom', offset: -2, fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11, fontFamily: '"IBM Plex Mono"' }} />
            <Tooltip
              contentStyle={{ fontSize: 12, fontFamily: '"IBM Plex Mono"', borderRadius: 8, border: '1px solid #E5E3DC' }}
              labelFormatter={(v) => `Week ${v}`}
            />
            <ReferenceLine x={currentWeek} stroke="#0A1628" strokeDasharray="4 3" strokeWidth={1.5} label={{ value: 'now', position: 'top', fontSize: 10, fontFamily: '"IBM Plex Mono"' }} />
            <Area type="monotone" dataKey="Tier 1" stackId="1" stroke="#1D9E75" fill="url(#t1)" strokeWidth={1.5} />
            <Area type="monotone" dataKey="Tier 2" stackId="1" stroke={tokens.brand.secondary} fill="url(#t2)" strokeWidth={1.5} />
            <Area type="monotone" dataKey="Tier 3" stackId="1" stroke="#E24B4A" fill="url(#t3)" strokeWidth={1.5} />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

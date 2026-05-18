import { Card, CardContent, Typography } from '@mui/material'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import type { StudentProfile } from '../../../types/domain'

interface Props {
  student: StudentProfile
  currentWeek: number
}

export function VleActivityChart({ student, currentWeek }: Props) {
  const data = student.weekly_clicks.map((c, i) => ({ week: i + 1, clicks: c }))

  return (
    <Card elevation={0} sx={{ borderRadius: 2, border: '1px solid #E5E3DC' }}>
      <CardContent>
        <Typography sx={{ fontSize: 12, fontWeight: 500, color: '#0A1628', mb: 1 }}>
          Weekly VLE activity (clicks)
        </Typography>
        <ResponsiveContainer width="100%" height={120}>
          <BarChart data={data} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#F0EFE9" />
            <XAxis dataKey="week" tick={{ fontSize: 10, fontFamily: '"IBM Plex Mono"' }} />
            <YAxis tick={{ fontSize: 10, fontFamily: '"IBM Plex Mono"' }} />
            <Tooltip
              contentStyle={{ fontSize: 12, fontFamily: '"IBM Plex Mono"', borderRadius: 8 }}
              labelFormatter={(v) => `Week ${v}`}
            />
            <ReferenceLine x={currentWeek} stroke="#0A1628" strokeDasharray="4 3" strokeWidth={1.5} />
            <Bar dataKey="clicks" fill="#5DCAA5" radius={[2, 2, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

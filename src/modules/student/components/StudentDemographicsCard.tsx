import { Card, CardContent, Typography, Box } from '@mui/material'
import type { StudentProfile } from '../../../types/domain'

interface Props {
  student: StudentProfile
}

const ROW_SX = {
  display: 'flex', justifyContent: 'space-between',
  py: 0.5, borderBottom: '1px solid #F0EFE9',
}

export function StudentDemographicsCard({ student }: Props) {
  const rows: [string, string][] = [
    ['Student ID',     `#${student.id_student}`],
    ['Gender',         student.gender],
    ['Age band',       student.age_band],
    ['IMD band',       student.imd_band ?? '—'],
    ['Education',      student.highest_education],
    ['Region',         student.region],
    ['Prior attempts', String(student.num_of_prev_attempts)],
    ['Credits',        String(student.studied_credits)],
    ['Disability',     student.disability ? 'Yes' : 'No'],
    ['Final result',   student.final_result],
  ]

  return (
    <Card elevation={0} sx={{ borderRadius: 2, border: '1px solid #E5E3DC', height: '100%' }}>
      <CardContent>
        <Typography sx={{ fontSize: 11, color: '#6B7280', fontFamily: '"IBM Plex Mono", monospace', mb: 1.5, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          Demographics
        </Typography>
        {rows.map(([k, v]) => (
          <Box key={k} sx={ROW_SX}>
            <Typography sx={{ fontSize: 12, color: '#6B7280' }}>{k}</Typography>
            <Typography sx={{ fontSize: 12, fontWeight: 500, color: '#0A1628', fontFamily: '"IBM Plex Mono", monospace' }}>{v}</Typography>
          </Box>
        ))}
      </CardContent>
    </Card>
  )
}

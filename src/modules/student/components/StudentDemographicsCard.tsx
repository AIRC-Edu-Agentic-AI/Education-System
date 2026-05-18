import { Card, CardContent, Typography, Box } from '@mui/material'
import type { StudentProfile } from '../../../types/domain'

interface Props { student: StudentProfile }

const ROWS: [string, (s: StudentProfile) => string][] = [
  ['Student ID',    (s) => `#${s.id_student}`],
  ['Gender',        (s) => s.gender],
  ['Age band',      (s) => s.age_band],
  ['IMD band',      (s) => s.imd_band ?? '—'],
  ['Education',     (s) => s.highest_education],
  ['Region',        (s) => s.region],
  ['Prior attempts',(s) => String(s.num_of_prev_attempts)],
  ['Credits',       (s) => String(s.studied_credits)],
  ['Disability',    (s) => s.disability ? 'Yes' : 'No'],
  ['Final result',  (s) => s.final_result],
]

export function StudentDemographicsCard({ student }: Props) {
  return (
    <Card elevation={0} sx={{ borderRadius: 2, border: '1px solid #E5E3DC', height: '100%' }}>
      <CardContent>
        <Typography sx={{ fontSize: 11, color: '#6B7280', fontFamily: '"IBM Plex Mono", monospace', mb: 1.5, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          Demographics
        </Typography>
        {ROWS.map(([label, value]) => (
          <Box key={label} sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5, borderBottom: '1px solid #F0EFE9' }}>
            <Typography sx={{ fontSize: 12, color: '#6B7280' }}>{label}</Typography>
            <Typography sx={{ fontSize: 12, fontWeight: 500, color: '#0A1628', fontFamily: '"IBM Plex Mono", monospace' }}>
              {value(student)}
            </Typography>
          </Box>
        ))}
      </CardContent>
    </Card>
  )
}

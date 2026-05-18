import { Card, CardContent, Typography, Table, TableBody, TableCell, TableHead, TableRow, Chip } from '@mui/material'
import type { StudentProfile } from '../../../types/domain'

interface Props {
  student: StudentProfile
  currentWeek: number
}

export function AssessmentPanel({ student, currentWeek }: Props) {
  const currentDay = currentWeek * 7

  const assessments = [...(student.assessments ?? [])]
    .filter((a) => !(a.weight === 100 && a.score === null))
    .sort((a, b) => (a.date_due ?? 0) - (b.date_due ?? 0))

  function status(a: typeof assessments[0]) {
    if (a.date_due == null || a.date_due > currentDay) return 'upcoming'
    if (a.date_submitted == null) return 'missing'
    if (a.date_submitted > a.date_due) return 'late'
    return 'on-time'
  }

  const STATUS_CHIP = {
    'on-time':  { bg: '#E1F5EE', text: '#0F6E56' },
    'late':     { bg: '#FAEEDA', text: '#854F0B' },
    'missing':  { bg: '#FCEBEB', text: '#A32D2D' },
    'upcoming': { bg: '#F3F4F6', text: '#6B7280' },
  }

  return (
    <Card elevation={0} sx={{ borderRadius: 2, border: '1px solid #E5E3DC' }}>
      <CardContent>
        <Typography sx={{ fontSize: 12, fontWeight: 500, color: '#0A1628', mb: 1.5 }}>
          Assessments
        </Typography>
        <Table size="small">
          <TableHead>
            <TableRow>
              {['Type', 'Due (day)', 'Weight', 'Score', 'Status', 'Submitted'].map((h) => (
                <TableCell key={h} sx={{ fontFamily: '"IBM Plex Mono", monospace', fontSize: 11, color: '#6B7280', bgcolor: '#F8F7F4' }}>
                  {h}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {assessments.map((a) => {
              const s  = status(a)
              const sc = STATUS_CHIP[s]
              return (
                <TableRow key={a.id_assessment}>
                  <TableCell sx={{ fontFamily: '"IBM Plex Mono", monospace', fontSize: 11 }}>{a.assessment_type}</TableCell>
                  <TableCell sx={{ fontFamily: '"IBM Plex Mono", monospace', fontSize: 11 }}>{a.date_due ?? '—'}</TableCell>
                  <TableCell sx={{ fontFamily: '"IBM Plex Mono", monospace', fontSize: 11 }}>{a.weight != null ? `${a.weight}%` : '—'}</TableCell>
                  <TableCell sx={{ fontFamily: '"IBM Plex Mono", monospace', fontSize: 11 }}>
                    {a.score != null
                      ? <Chip label={`${a.score}%`} size="small" sx={{ fontSize: 11, height: 20, bgcolor: a.score >= 50 ? '#E1F5EE' : '#FCEBEB', color: a.score >= 50 ? '#0F6E56' : '#A32D2D' }} />
                      : <Typography sx={{ fontSize: 11, color: '#9CA3AF' }}>—</Typography>
                    }
                  </TableCell>
                  <TableCell>
                    <Chip label={s} size="small" sx={{ fontSize: 10, height: 18, bgcolor: sc.bg, color: sc.text, fontFamily: '"IBM Plex Mono", monospace', '& .MuiChip-label': { px: 0.75 } }} />
                  </TableCell>
                  <TableCell sx={{ fontFamily: '"IBM Plex Mono", monospace', fontSize: 11, color: a.date_submitted ? '#0F6E56' : '#9CA3AF' }}>
                    {a.date_submitted != null ? `Day ${a.date_submitted}` : '—'}
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}

import { Card, CardContent, Typography, TextField } from '@mui/material'
import { useStudentStore } from '../stores/studentStore'

interface Props {
  studentId: number
}

export function StudentNotesCard({ studentId }: Props) {
  const { notes, setNote } = useStudentStore()
  const value = notes[studentId] ?? ''

  return (
    <Card elevation={0} sx={{ borderRadius: 2, border: '1px solid #E5E3DC' }}>
      <CardContent>
        <Typography sx={{ fontSize: 12, fontWeight: 500, color: '#0A1628', mb: 1 }}>
          Teacher notes
        </Typography>
        <TextField
          multiline
          minRows={3}
          fullWidth
          placeholder="Add notes about this student…"
          value={value}
          onChange={(e) => setNote(studentId, e.target.value)}
          InputProps={{
            sx: {
              fontSize: 12,
              fontFamily: '"IBM Plex Mono", monospace',
              color: '#0A1628',
              '& textarea': { resize: 'vertical' },
            },
          }}
          sx={{
            '& .MuiOutlinedInput-root': {
              borderRadius: 1.5,
              '& fieldset': { borderColor: '#E5E3DC' },
              '&:hover fieldset': { borderColor: '#D1D5DB' },
              '&.Mui-focused fieldset': { borderColor: '#1D9E75' },
            },
          }}
        />
        {value.length > 0 && (
          <Typography sx={{ fontSize: 10, color: '#9CA3AF', mt: 0.5, fontFamily: '"IBM Plex Mono", monospace', textAlign: 'right' }}>
            Saved locally · {value.length} chars
          </Typography>
        )}
      </CardContent>
    </Card>
  )
}

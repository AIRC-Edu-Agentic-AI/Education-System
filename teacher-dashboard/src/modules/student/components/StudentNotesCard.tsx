import { Card, CardContent, Typography, TextField } from '@mui/material'
import { tokens } from '../../../theme'
import { useStudentStore } from '../stores/studentStore'

interface Props {
  studentId: number
}

export function StudentNotesCard({ studentId }: Props) {
  const { notes, setNote } = useStudentStore()
  const value = notes[studentId] ?? ''

  return (
    <Card elevation={0} sx={{ borderRadius: 2 }}>
      <CardContent>
        <Typography sx={{ fontSize: 12, fontWeight: 500, color: tokens.text.primary, mb: 1 }}>
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
              fontFamily: tokens.font.mono,
              color: tokens.text.primary,
              '& textarea': { resize: 'vertical' },
            },
          }}
          sx={{
            '& .MuiOutlinedInput-root': {
              borderRadius: 1.5,
              '& fieldset': { borderColor: tokens.border.default },
              '&:hover fieldset': { borderColor: tokens.border.hover },
              '&.Mui-focused fieldset': { borderColor: tokens.brand.primaryLight },
            },
          }}
        />
        {value.length > 0 && (
          <Typography sx={{ fontSize: 10, color: tokens.text.muted, mt: 0.5, fontFamily: tokens.font.mono, textAlign: 'right' }}>
            Saved locally · {value.length} chars
          </Typography>
        )}
      </CardContent>
    </Card>
  )
}

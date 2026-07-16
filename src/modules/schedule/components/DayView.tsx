import { Box, Divider, Paper, Stack, Typography } from '@mui/material'
import type { ScheduleItem } from '../../../types/domain'
import { CalendarEventCard } from './CalendarEventCard'

interface Props {
  date: string
  events: ScheduleItem[]
  onSelect: (event: ScheduleItem) => void
}

export function DayView({ date, events, onSelect }: Props) {
  return (
    <Paper sx={{ p: 2, minHeight: 420, borderRadius: 2, border: '1px solid rgba(0,0,0,0.08)' }}>
      <Typography sx={{ fontWeight: 700, mb: 1 }}>Day view — {date}</Typography>
      <Divider sx={{ mb: 2 }} />
      {events.length === 0 ? (
        <Typography sx={{ color: 'text.secondary', mt: 3 }}>No sessions scheduled for this day.</Typography>
      ) : (
        <Stack spacing={2}>
          {events.map((event) => (
            <CalendarEventCard key={event.id} event={event} onClick={() => onSelect(event)} />
          ))}
        </Stack>
      )}
    </Paper>
  )
}

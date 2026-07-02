import { Box, Divider, Paper, Stack, Typography } from '@mui/material'
import type { ScheduleItem } from '../../../types/domain'
import { CalendarEventCard } from './CalendarEventCard'

interface Props {
  dates: string[]
  events: ScheduleItem[]
  onSelect: (event: ScheduleItem) => void
}

export function WeekView({ dates, events, onSelect }: Props) {
  return (
    <Paper sx={{ p: 2, borderRadius: 2, border: '1px solid rgba(0,0,0,0.08)' }}>
      <Typography sx={{ fontWeight: 700, mb: 2 }}>Week overview</Typography>
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(7, minmax(0, 1fr))', gap: 1 }}>
        {dates.map((date) => {
          const dayEvents = events.filter((item) => item.date === date)
          return (
            <Paper key={date} sx={{ p: 1, minHeight: 220, bgcolor: 'background.paper', border: '1px solid rgba(0,0,0,0.06)' }}>
              <Typography sx={{ fontWeight: 700, mb: 1, fontSize: 13 }}>{date}</Typography>
              <Divider sx={{ mb: 1 }} />
              <Stack spacing={1}>
                {dayEvents.length === 0 ? (
                  <Typography sx={{ fontSize: 12, color: 'text.secondary' }}>No sessions</Typography>
                ) : (
                  dayEvents.map((event) => (
                    <CalendarEventCard key={event.id} event={event} compact onClick={() => onSelect(event)} />
                  ))
                )}
              </Stack>
            </Paper>
          )
        })}
      </Box>
    </Paper>
  )
}

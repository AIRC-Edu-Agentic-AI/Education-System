import { Box, Divider, Paper, Stack, Typography } from '@mui/material'
import type { ScheduleItem } from '../../../types/domain'
import { CalendarEventCard } from './CalendarEventCard'

interface Props {
  dates: string[]
  events: ScheduleItem[]
  onSelect: (event: ScheduleItem) => void
  onAddForDate: (date: string) => void
}

export function WeekView({ dates, events, onSelect, onAddForDate }: Props) {
  return (
    <Paper sx={{ p: 2, borderRadius: 2, border: '1px solid rgba(0,0,0,0.08)' }}>
      <Typography sx={{ fontWeight: 700, mb: 2 }}>Week overview</Typography>
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(7, minmax(0, 1fr))', gap: 1 }}>
        {dates.map((date) => {
          const dayEvents = events.filter((item) => item.date === date)
          const dayName = new Date(date).toLocaleString('en-US', { weekday: 'short' })
          return (
            <Box
              key={date}
              component="button"
              type="button"
              onClick={() => onAddForDate(date)}
              sx={{
                p: 1,
                minHeight: 220,
                bgcolor: 'background.paper',
                border: '1px solid rgba(0,0,0,0.06)',
                borderRadius: 2,
                textAlign: 'left',
                cursor: 'pointer',
                '&:hover': { borderColor: 'primary.main', boxShadow: 1 },
              }}
            >
              <Stack spacing={0.5} sx={{ mb: 1 }}>
                <Typography sx={{ fontWeight: 700, fontSize: 13 }}>{dayName}</Typography>
                <Typography sx={{ fontSize: 12, color: 'text.secondary' }}>{date}</Typography>
              </Stack>
              <Divider sx={{ mb: 1 }} />
              <Stack spacing={1}>
                {dayEvents.length === 0 ? (
                  <Typography sx={{ fontSize: 12, color: 'text.secondary' }}>Click to add a session</Typography>
                ) : (
                  dayEvents.map((event) => (
                    <Box key={event.id} onClick={(e) => { e.stopPropagation(); onSelect(event) }}>
                      <CalendarEventCard event={event} compact />
                    </Box>
                  ))
                )}
              </Stack>
            </Box>
          )
        })}
      </Box>
    </Paper>
  )
}

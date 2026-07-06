import { Box, Divider, Paper, Stack, Typography } from '@mui/material'
import type { ScheduleItem } from '../../../types/domain'
import { CalendarEventCard } from './CalendarEventCard'

interface Props {
  events: ScheduleItem[]
  onSelect: (event: ScheduleItem) => void
}

function groupByWeek(events: ScheduleItem[]) {
  const groups: Record<string, ScheduleItem[]> = {}
  events.forEach((item) => {
    if (!item.date) return
    const week = item.date.slice(0, 8)
    groups[week] = groups[week] || []
    groups[week].push(item)
  })
  return groups
}

export function MonthView({ events, onSelect }: Props) {
  const groups = groupByWeek(events)
  return (
    <Paper sx={{ p: 2, borderRadius: 2, border: '1px solid rgba(0,0,0,0.08)' }}>
      <Typography sx={{ fontWeight: 700, mb: 2 }}>Month view</Typography>
      <Stack spacing={2}>
        {Object.entries(groups).sort(([a], [b]) => a.localeCompare(b)).map(([week, weekEvents]) => (
          <Box key={week}>
            <Typography sx={{ fontSize: 13, fontWeight: 700, mb: 1 }}>Week starting {week}</Typography>
            <Divider sx={{ mb: 1 }} />
            <Stack spacing={1}>
              {weekEvents.map((event) => (
                <CalendarEventCard key={event.id} event={event} compact onClick={() => onSelect(event)} />
              ))}
            </Stack>
          </Box>
        ))}
        {events.length === 0 && (
          <Typography sx={{ color: 'text.secondary' }}>No sessions scheduled in this month.</Typography>
        )}
      </Stack>
    </Paper>
  )
}

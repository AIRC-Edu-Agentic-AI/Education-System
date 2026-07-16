import { Box, Paper, Stack, Typography } from '@mui/material'
import type { ScheduleItem } from '../../../types/domain'
import { CalendarEventCard } from './CalendarEventCard'

interface Props {
  anchorDate: string
  events: ScheduleItem[]
  onSelect: (event: ScheduleItem) => void
  onAddForDate: (date: string) => void
}

function getMonthDates(anchorDate: string) {
  const date = new Date(anchorDate)
  const year = date.getFullYear()
  const month = date.getMonth()
  const firstDay = new Date(year, month, 1)
  const firstDayIndex = firstDay.getDay() === 0 ? 6 : firstDay.getDay() - 1
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const startDate = new Date(firstDay)
  startDate.setDate(firstDay.getDate() - firstDayIndex)

  return Array.from({ length: 42 }, (_, index) => {
    const current = new Date(startDate)
    current.setDate(startDate.getDate() + index)
    return current.toISOString().slice(0, 10)
  }).slice(0, 42)
}

function isSameMonth(dateIso: string, anchorIso: string) {
  return dateIso.slice(0, 7) === anchorIso.slice(0, 7)
}

export function MonthView({ anchorDate, events, onSelect, onAddForDate }: Props) {
  const monthDates = getMonthDates(anchorDate)
  const dayEvents = new Map<string, ScheduleItem[]>()

  events.forEach((event) => {
    if (!event.date) return
    const existing = dayEvents.get(event.date) ?? []
    dayEvents.set(event.date, [...existing, event])
  })

  const monthYear = new Date(anchorDate).toLocaleString('en-US', { month: 'long', year: 'numeric' })

  return (
    <Paper sx={{ p: 2, borderRadius: 2, border: '1px solid rgba(0,0,0,0.08)' }}>
      <Typography sx={{ fontWeight: 700, mb: 2 }}>Month view • {monthYear}</Typography>
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(7, minmax(0, 1fr))', gap: 1 }}>
        {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((label) => (
          <Typography key={label} sx={{ fontSize: 12, fontWeight: 700, color: 'text.secondary', px: 0.5 }}>{label}</Typography>
        ))}
        {monthDates.map((date) => {
          const dateEvents = dayEvents.get(date) ?? []
          const isCurrentMonth = isSameMonth(date, anchorDate)
          return (
            <Box
              key={date}
              component="button"
              type="button"
              onClick={() => onAddForDate(date)}
              sx={{
                minHeight: 116,
                p: 1,
                bgcolor: isCurrentMonth ? 'background.paper' : 'grey.50',
                border: '1px solid rgba(0,0,0,0.06)',
                borderRadius: 2,
                textAlign: 'left',
                cursor: 'pointer',
                '&:hover': { borderColor: 'primary.main', boxShadow: 1 },
              }}
            >
              <Typography sx={{ fontSize: 12, fontWeight: 700, mb: 0.5 }}>{date.slice(8, 10)}</Typography>
              <Stack spacing={0.5}>
                {dateEvents.length === 0 ? (
                  <Typography sx={{ fontSize: 11, color: 'text.secondary' }}>Click to add</Typography>
                ) : (
                  dateEvents.slice(0, 2).map((event) => (
                    <Box key={event.id} onClick={(e) => { e.stopPropagation(); onSelect(event) }}>
                      <CalendarEventCard event={event} compact />
                    </Box>
                  ))
                )}
                {dateEvents.length > 2 && (
                  <Typography sx={{ fontSize: 11, color: 'text.secondary' }}>+{dateEvents.length - 2} more</Typography>
                )}
              </Stack>
            </Box>
          )
        })}
      </Box>
    </Paper>
  )
}

import { Box, Chip, Link, Stack, Typography } from '@mui/material'
import LaunchIcon from '@mui/icons-material/LaunchRounded'
import type { ScheduleItem } from '../../../types/domain'

interface Props {
  event: ScheduleItem
  compact?: boolean
  onClick?: () => void
}

const statusLabels: Record<string, string> = {
  scheduled: 'Scheduled',
  completed: 'Completed',
  cancelled: 'Cancelled',
  rescheduled: 'Rescheduled',
}

export function CalendarEventCard({ event, compact = false, onClick }: Props) {
  return (
    <Box
      onClick={onClick}
      sx={{
        p: compact ? 0.75 : 1.25,
        borderRadius: 2,
        bgcolor: compact ? 'background.paper' : 'background.default',
        border: compact ? '1px solid rgba(0,0,0,0.06)' : '1px solid rgba(0,0,0,0.08)',
        boxShadow: compact ? 'none' : '0 1px 6px rgba(0,0,0,0.08)',
        cursor: onClick ? 'pointer' : 'default',
        '&:hover': onClick ? { transform: 'translateY(-1px)', boxShadow: compact ? '0 1px 4px rgba(0,0,0,0.08)' : '0 3px 10px rgba(0,0,0,0.12)' } : undefined,
        transition: 'transform 120ms ease, box-shadow 120ms ease',
      }}
    >
      <Stack spacing={0.5}>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start" spacing={1}>
          <Typography variant={compact ? 'body2' : 'body1'} sx={{ fontWeight: 700 }}>
            {event.subject || 'Teaching session'}
          </Typography>
          <Chip label={statusLabels[event.status ?? 'scheduled']} size="small" color={event.status === 'completed' ? 'success' : event.status === 'cancelled' ? 'error' : event.status === 'rescheduled' ? 'warning' : 'default'} />
        </Stack>

        <Typography variant={compact ? 'caption' : 'body2'} color="text.secondary">
          {event.className || 'No class'} · {event.teacher || 'No teacher'}
        </Typography>

        <Typography variant={compact ? 'caption' : 'body2'}>
          {event.date || 'No date'} · {event.startTime || '--'} – {event.endTime || '--'}
        </Typography>

        {event.room && (
          <Typography variant={compact ? 'caption' : 'body2'} color="text.secondary">
            Room: {event.room}
          </Typography>
        )}

        {event.locationUrl && (
          <Link href={event.locationUrl} target="_blank" rel="noreferrer" underline="hover" sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5, fontSize: compact ? 11 : 13 }}>
            Join session <LaunchIcon fontSize="inherit" />
          </Link>
        )}
      </Stack>
    </Box>
  )
}

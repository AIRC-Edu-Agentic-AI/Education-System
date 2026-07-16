import { Box, Button, FormControl, IconButton, MenuItem, Select, Stack, Typography } from '@mui/material'
import ArrowBackIosNewIcon from '@mui/icons-material/ArrowBackIosNew'
import ArrowForwardIosIcon from '@mui/icons-material/ArrowForwardIos'
import TodayIcon from '@mui/icons-material/Today'
import CalendarMonthIcon from '@mui/icons-material/CalendarMonth'
import CalendarViewWeekIcon from '@mui/icons-material/CalendarViewWeek'
import CalendarViewDayIcon from '@mui/icons-material/CalendarViewDay'
import type { ScheduleStatus } from '../../../types/domain'

type ViewMode = 'day' | 'week' | 'month'
export type DeliveryMode = 'online' | 'offline' | 'hybrid'

interface Props {
  viewMode: ViewMode
  label: string
  teacherOptions?: string[]
  selectedTeacher: string
  showTeacherFilter: boolean
  onTeacherChange: (teacher: string) => void
  statusFilter: 'all' | ScheduleStatus
  deliveryFilter: 'all' | DeliveryMode
  onStatusFilterChange: (value: 'all' | ScheduleStatus) => void
  onDeliveryFilterChange: (value: 'all' | DeliveryMode) => void
  onViewChange: (mode: ViewMode) => void
  onToday: () => void
  onPrev: () => void
  onNext: () => void
}

export function CalendarToolbar({
  viewMode,
  label,
  teacherOptions = [],
  selectedTeacher,
  showTeacherFilter,
  onTeacherChange,
  statusFilter,
  deliveryFilter,
  onStatusFilterChange,
  onDeliveryFilterChange,
  onViewChange,
  onToday,
  onPrev,
  onNext,
}: Props) {
  return (
    <Box sx={{ p: 2, display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 2, alignItems: 'center' }}>
      <Stack direction="row" alignItems="center" spacing={1} sx={{ flexGrow: 1, flexWrap: 'wrap' }}>
        <Typography sx={{ fontSize: 14, fontWeight: 700 }}>{label}</Typography>
        <Button size="small" startIcon={<TodayIcon />} onClick={onToday}>
          Today
        </Button>
        <IconButton size="small" onClick={onPrev}>
          <ArrowBackIosNewIcon fontSize="small" />
        </IconButton>
        <IconButton size="small" onClick={onNext}>
          <ArrowForwardIosIcon fontSize="small" />
        </IconButton>
        <Button
          size="small"
          variant={viewMode === 'day' ? 'contained' : 'outlined'}
          startIcon={<CalendarViewDayIcon fontSize="small" />}
          onClick={() => onViewChange('day')}
        >
          Day
        </Button>
        <Button
          size="small"
          variant={viewMode === 'week' ? 'contained' : 'outlined'}
          startIcon={<CalendarViewWeekIcon fontSize="small" />}
          onClick={() => onViewChange('week')}
        >
          Week
        </Button>
        <Button
          size="small"
          variant={viewMode === 'month' ? 'contained' : 'outlined'}
          startIcon={<CalendarMonthIcon fontSize="small" />}
          onClick={() => onViewChange('month')}
        >
          Month
        </Button>
      </Stack>

      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} sx={{ minWidth: 260, alignItems: 'center' }}>
        {showTeacherFilter && (
          <FormControl size="small" sx={{ minWidth: 160 }}>
            <Select value={selectedTeacher} onChange={(e) => onTeacherChange(e.target.value)}>
              <MenuItem value="all">All teachers</MenuItem>
              {teacherOptions.map((teacher) => (
                <MenuItem key={teacher} value={teacher}>{teacher}</MenuItem>
              ))}
            </Select>
          </FormControl>
        )}
        <FormControl size="small" sx={{ minWidth: 140 }}>
          <Select value={statusFilter} onChange={(e) => onStatusFilterChange(e.target.value as 'all' | ScheduleStatus)}>
            <MenuItem value="all">All statuses</MenuItem>
            <MenuItem value="scheduled">Scheduled</MenuItem>
            <MenuItem value="completed">Completed</MenuItem>
            <MenuItem value="cancelled">Cancelled</MenuItem>
            <MenuItem value="rescheduled">Rescheduled</MenuItem>
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 140 }}>
          <Select value={deliveryFilter} onChange={(e) => onDeliveryFilterChange(e.target.value as 'all' | DeliveryMode)}>
            <MenuItem value="all">All modes</MenuItem>
            <MenuItem value="offline">Offline</MenuItem>
            <MenuItem value="online">Online</MenuItem>
            <MenuItem value="hybrid">Hybrid</MenuItem>
          </Select>
        </FormControl>
      </Stack>
    </Box>
  )
}

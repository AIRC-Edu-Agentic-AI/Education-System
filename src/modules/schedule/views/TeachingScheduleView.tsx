import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Grid,
  Paper,
  Stack,
  TextField,
  Toolbar,
  Typography,
} from '@mui/material'
import AddIcon from '@mui/icons-material/AddRounded'
import SaveIcon from '@mui/icons-material/SaveRounded'
import { tokens } from '../../../theme'
import { container } from '../../../di/container'
import { useAuthStore } from '../../../shared/stores/authStore'
import type { ScheduleChangeLog, ScheduleItem, ScheduleStatus } from '../../../types/domain'
import { CalendarToolbar } from '../components/CalendarToolbar'
import { DayView } from '../components/DayView'
import { WeekView } from '../components/WeekView'
import { MonthView } from '../components/MonthView'
import { ScheduleDetailsPanel } from '../components/ScheduleDetailsPanel'

type ViewMode = 'day' | 'week' | 'month'
type DeliveryMode = 'online' | 'offline' | 'hybrid'

const editableRoles = new Set(['admin', 'academic_advisor', 'teacher'])

function todayIso() {
  return new Date().toISOString().slice(0, 10)
}

function minutes(time?: string) {
  if (!time) return NaN
  const [hours, mins] = time.split(':').map(Number)
  return hours * 60 + mins
}

function overlaps(a: ScheduleItem, b: ScheduleItem) {
  return minutes(a.startTime) < minutes(b.endTime) && minutes(b.startTime) < minutes(a.endTime)
}

function normalizeSchedule(item: ScheduleItem, index: number, actor: string): ScheduleItem {
  const id = item.id || `schedule_${Date.now()}_${index}`
  const status = item.status ?? 'scheduled'
  const activity = item.activity || item.subject || 'Teaching session'
  const subject = item.subject || item.activity || 'Teaching session'
  const startTime = item.startTime || (item.time?.includes('-') ? item.time.split('-')[0].trim() : '')
  const endTime = item.endTime || (item.time?.includes('-') ? item.time.split('-')[1]?.trim() : '')

  return {
    ...item,
    id,
    week: item.week ?? 1,
    activity,
    subject,
    date: item.date || todayIso(),
    startTime,
    endTime,
    time: startTime && endTime ? `${startTime}-${endTime}` : item.time || '',
    teacher: item.teacher || actor,
    className: item.className || '',
    room: item.room || '',
    locationUrl: item.locationUrl || '',
    status,
    note: item.note ?? '',
    deliveryMode: item.deliveryMode || 'offline',
    teacherId: item.teacherId || undefined,
    changeLog: item.changeLog ?? [],
  }
}

function hasCoreChanges(a?: ScheduleItem, b?: ScheduleItem) {
  if (!a || !b) return true
  const fields: Array<keyof ScheduleItem> = [
    'week',
    'date',
    'startTime',
    'endTime',
    'teacher',
    'className',
    'subject',
    'room',
    'locationUrl',
    'status',
    'is_makeup',
    'note',
    'deliveryMode',
  ]
  return fields.some((field) => a[field] !== b[field])
}

function makeLog(
  scheduleId: string,
  action: ScheduleChangeLog['action'],
  actor: string,
  reason: string,
  before?: ScheduleItem,
  after?: ScheduleItem
): ScheduleChangeLog {
  return {
    id: `log_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    scheduleId,
    changedAt: new Date().toISOString(),
    changedBy: actor,
    action,
    reason: reason.trim() || 'Schedule updated',
    before,
    after,
  }
}

function validateSchedules(items: ScheduleItem[], numWeeks: number) {
  const errors: string[] = []
  const activeItems = items.filter((item) => item.status !== 'cancelled')

  items.forEach((item) => {
    const label = item.subject || item.activity || item.id
    if (item.week && (item.week < 1 || item.week > numWeeks)) errors.push(`${label}: week must be between 1 and ${numWeeks}.`)
    if (!item.date) errors.push(`${label}: date is required.`)
    if (!item.startTime || !item.endTime) errors.push(`${label}: start and end time are required.`)
    if (item.startTime && item.endTime && minutes(item.startTime) >= minutes(item.endTime)) {
      errors.push(`${label}: start time must be before end time.`)
    }
    if (!item.teacher?.trim()) errors.push(`${label}: teacher is required.`)
    if (!item.className?.trim()) errors.push(`${label}: class is required.`)
    if (!item.subject?.trim()) errors.push(`${label}: subject is required.`)
  })

  activeItems.forEach((item, index) => {
    activeItems.slice(index + 1).forEach((other) => {
      if (!item.date || item.date !== other.date || !overlaps(item, other)) return
      if (item.teacher && item.teacher === other.teacher) errors.push(`Teacher conflict: ${item.teacher} has overlapping sessions on ${item.date}.`)
      if (item.className && item.className === other.className) errors.push(`Class conflict: ${item.className} has overlapping sessions on ${item.date}.`)
      if (item.room && item.room === other.room) errors.push(`Room conflict: ${item.room} is double-booked on ${item.date}.`)
    })
  })

  return [...new Set(errors)]
}

function addDays(dateIso: string, amount: number) {
  const date = new Date(dateIso)
  date.setDate(date.getDate() + amount)
  return date.toISOString().slice(0, 10)
}

function startOfWeek(dateIso: string) {
  const date = new Date(dateIso)
  const day = date.getDay()
  const diff = date.getDate() - day + (day === 0 ? -6 : 1)
  date.setDate(diff)
  return date.toISOString().slice(0, 10)
}

function getWeekDates(weekStartIso: string) {
  return Array.from({ length: 7 }, (_, index) => addDays(weekStartIso, index))
}

function isSameMonth(dateIso: string, anchorIso: string) {
  return dateIso.slice(0, 7) === anchorIso.slice(0, 7)
}

export function TeachingScheduleView() {
  const { user } = useAuthStore()
  const actor = user?.name || user?.email || 'Teacher'
  const isAdmin = user?.role === 'admin' || user?.role === 'academic_advisor'
  const canEdit = editableRoles.has(user?.role ?? '')

  const [schedules, setSchedules] = useState<ScheduleItem[]>([])
  const [savedSnapshot, setSavedSnapshot] = useState<ScheduleItem[]>([])
  const [selectedId, setSelectedId] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [viewMode, setViewMode] = useState<ViewMode>('week')
  const [anchorDate, setAnchorDate] = useState(todayIso())
  const [teacherFilter, setTeacherFilter] = useState<string>(isAdmin ? 'all' : actor)
  const [statusFilter, setStatusFilter] = useState<'all' | ScheduleStatus>('all')
  const [deliveryFilter, setDeliveryFilter] = useState<'all' | DeliveryMode>('all')
  const [changeReason, setChangeReason] = useState('')
  const [message, setMessage] = useState('')

  useEffect(() => {
    let mounted = true
    setLoading(true)
    container.dataService.getSchedules()
      .then((items) => {
        if (!mounted) return
        const normalized = items.map((item, index) => normalizeSchedule(item, index, actor))
        setSchedules(normalized)
        setSavedSnapshot(normalized)
        setSelectedId(normalized[0]?.id ?? '')
      })
      .catch(() => setMessage('Could not load schedules.'))
      .finally(() => setLoading(false))

    return () => {
      mounted = false
    }
  }, [actor])

  const teachers = useMemo(() => {
    return [...new Set(schedules.map((item) => item.teacher).filter(Boolean))] as string[]
  }, [schedules])

  useEffect(() => {
    if (!isAdmin) {
      setTeacherFilter(actor)
    }
  }, [actor, isAdmin])

  const weekStart = useMemo(() => startOfWeek(anchorDate), [anchorDate])
  const weekDates = useMemo(() => getWeekDates(weekStart), [weekStart])
  const today = todayIso()

  const validationErrors = useMemo(() => validateSchedules(schedules, 39), [schedules])

  const visibleSchedules = useMemo(() => {
    return schedules
      .filter((item) => teacherFilter === 'all' || item.teacher === teacherFilter)
      .filter((item) => statusFilter === 'all' || item.status === statusFilter)
      .filter((item) => deliveryFilter === 'all' || item.deliveryMode === deliveryFilter)
      .filter((item) => {
        if (!item.date) return false
        if (viewMode === 'day') return item.date === anchorDate
        if (viewMode === 'week') return weekDates.includes(item.date)
        return isSameMonth(item.date, anchorDate)
      })
      .sort((a, b) => `${a.date} ${a.startTime}`.localeCompare(`${b.date} ${b.startTime}`))
  }, [schedules, teacherFilter, statusFilter, deliveryFilter, viewMode, anchorDate, weekDates])

  const selected = schedules.find((item) => item.id === selectedId) ?? visibleSchedules[0] ?? schedules[0]

  const updateSelected = (patch: Partial<ScheduleItem>) => {
    if (!selected) return
    setSchedules((items) => items.map((item) => item.id === selected.id ? {
      ...item,
      ...patch,
      activity: patch.subject ?? item.activity,
      time: (patch.startTime ?? item.startTime) && (patch.endTime ?? item.endTime)
        ? `${patch.startTime ?? item.startTime}-${patch.endTime ?? item.endTime}`
        : item.time,
      updatedBy: actor,
      updatedAt: new Date().toISOString(),
    } : item))
  }

  const changeAnchor = (amount: number) => {
    if (viewMode === 'day') {
      return setAnchorDate(addDays(anchorDate, amount))
    }
    if (viewMode === 'week') {
      return setAnchorDate(addDays(weekStart, amount * 7))
    }
    const date = new Date(anchorDate)
    date.setMonth(date.getMonth() + amount)
    setAnchorDate(date.toISOString().slice(0, 10))
  }

  const addSchedule = () => {
    const now = new Date().toISOString()
    const id = `schedule_${Date.now()}`
    const item: ScheduleItem = {
      id,
      week: 1,
      activity: 'New teaching session',
      subject: 'New teaching session',
      teacher: actor,
      teacherId: user?.email,
      className: '',
      room: '',
      date: anchorDate,
      startTime: '09:00',
      endTime: '10:30',
      time: '09:00-10:30',
      status: 'scheduled',
      deliveryMode: 'offline',
      is_makeup: false,
      note: '',
      createdBy: actor,
      updatedBy: actor,
      createdAt: now,
      updatedAt: now,
      changeLog: [makeLog(id, 'created', actor, changeReason || 'Created schedule')],
    }
    setSchedules((items) => [...items, item])
    setSelectedId(id)
  }

  const removeSchedule = (id: string) => {
    setSchedules((items) => items.filter((item) => item.id !== id))
    if (selectedId === id) setSelectedId('')
  }

  const saveSchedules = async () => {
    if (validationErrors.length > 0) {
      setMessage('Please fix schedule conflicts before saving.')
      return
    }

    const snapshotById = new Map(savedSnapshot.map((item) => [item.id, item]))
    const now = new Date().toISOString()
    const schedulesWithLogs = schedules.map((item) => {
      const before = snapshotById.get(item.id)
      if (!hasCoreChanges(before, item)) return item
      const action: ScheduleChangeLog['action'] = before ? 'updated' : 'created'
      return {
        ...item,
        updatedAt: now,
        updatedBy: actor,
        changeLog: [...(item.changeLog ?? []), makeLog(item.id, action, actor, changeReason, before, item)],
      }
    })

    setLoading(true)
    try {
      await container.dataService.saveSchedules(schedulesWithLogs)
      setSchedules(schedulesWithLogs)
      setSavedSnapshot(schedulesWithLogs)
      setChangeReason('')
      setMessage('Schedule saved successfully.')
    } catch {
      setMessage('Could not save schedules.')
    } finally {
      setLoading(false)
    }
  }

  const stats = {
    today: schedules.filter((item) => item.date === today && item.status !== 'cancelled').length,
    upcoming: schedules.filter((item) => item.date && item.date >= today && item.status !== 'cancelled').length,
    week: schedules.filter((item) => item.date && weekDates.includes(item.date) && item.status !== 'cancelled').length,
    conflicts: validationErrors.length,
  }

  const label = isAdmin ? 'Teacher calendar' : 'My teaching calendar'

  return (
    <Box sx={{ minHeight: '100%', bgcolor: tokens.surface.default }}>
      <Toolbar sx={{ px: 3, bgcolor: tokens.surface.paper, borderBottom: `1px solid ${tokens.border.default}` }}>
        <Box sx={{ flexGrow: 1 }}>
          <Typography sx={{ fontWeight: 700, color: tokens.text.primary }}>Teaching Calendar</Typography>
          <Typography sx={{ fontSize: 12, color: tokens.text.secondary }}>View your schedule by day, week, or month.</Typography>
        </Box>
        <Button startIcon={<AddIcon />} variant="contained" onClick={addSchedule} disabled={!canEdit}>
          Add session
        </Button>
        <Button startIcon={<SaveIcon />} sx={{ ml: 1 }} variant="outlined" onClick={saveSchedules} disabled={!canEdit || loading}>
          Save changes
        </Button>
      </Toolbar>

      <Box sx={{ p: 3 }}>
        {message && <Alert sx={{ mb: 2 }} severity={message.includes('success') ? 'success' : 'warning'} onClose={() => setMessage('')}>{message}</Alert>}
        {!canEdit && <Alert sx={{ mb: 2 }} severity="info">Your role can view schedules but cannot update them.</Alert>}

        <Grid container spacing={2} sx={{ mb: 2 }}>
          {[
            ['Today sessions', stats.today],
            ['Upcoming sessions', stats.upcoming],
            ['This week', stats.week],
            ['Conflicts', stats.conflicts],
          ].map(([title, value]) => (
            <Grid item xs={6} md={3} key={title}>
              <Paper sx={{ p: 2, border: `1px solid ${tokens.border.default}`, borderRadius: 2 }}>
                <Typography sx={{ fontSize: 11, color: tokens.text.secondary, textTransform: 'uppercase' }}>{title}</Typography>
                <Typography sx={{ mt: 0.5, fontSize: 24, fontWeight: 700 }}>{value}</Typography>
              </Paper>
            </Grid>
          ))}
        </Grid>

        <Paper sx={{ mb: 2, border: `1px solid ${tokens.border.default}`, borderRadius: 2, overflow: 'hidden' }}>
          <CalendarToolbar
            viewMode={viewMode}
            label={label}
            teacherOptions={teachers}
            selectedTeacher={teacherFilter}
            showTeacherFilter={isAdmin}
            onTeacherChange={setTeacherFilter}
            statusFilter={statusFilter}
            deliveryFilter={deliveryFilter}
            onStatusFilterChange={setStatusFilter}
            onDeliveryFilterChange={setDeliveryFilter}
            onViewChange={setViewMode}
            onToday={() => setAnchorDate(today)}
            onPrev={() => changeAnchor(-1)}
            onNext={() => changeAnchor(1)}
          />
        </Paper>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 12 }}>
            <Typography>Loading schedule...</Typography>
          </Box>
        ) : (
          <Grid container spacing={2}>
            <Grid item xs={12} lg={8}>
              {viewMode === 'day' && <DayView date={anchorDate} events={visibleSchedules} onSelect={(event) => setSelectedId(event.id)} />}
              {viewMode === 'week' && <WeekView dates={weekDates} events={visibleSchedules} onSelect={(event) => setSelectedId(event.id)} />}
              {viewMode === 'month' && <MonthView events={visibleSchedules} onSelect={(event) => setSelectedId(event.id)} />}
            </Grid>
            <Grid item xs={12} lg={4}>
              <ScheduleDetailsPanel
                schedule={selected}
                canEdit={canEdit}
                onChange={updateSelected}
                onClose={() => setSelectedId('')}
                onDelete={() => selected && removeSchedule(selected.id)}
                onSave={saveSchedules}
              />
            </Grid>
          </Grid>
        )}
      </Box>
    </Box>
  )
}

import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogContent,
  Grid,
  Paper,
  Stack,
  TextField,
  Toolbar,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material'

import { tokens } from '../../../theme'
import { container } from '../../../di/container'
import { useAuthStore } from '../../../shared/stores/authStore'
import type { OuladIndex, ScheduleChangeLog, ScheduleItem, ScheduleStatus } from '../../../types/domain'
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

function isPlaceholderSchedule(item: ScheduleItem) {
  return item.subject === 'New teaching session' && item.activity === 'New teaching session'
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
  const [dialogOpen, setDialogOpen] = useState(false)
  const [draftSchedule, setDraftSchedule] = useState<Partial<ScheduleItem> | null>(null)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [index, setIndex] = useState<OuladIndex | null>(null)
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
        const normalized = items
          .map((item, index) => normalizeSchedule(item, index, actor))
          .filter((item) => !isPlaceholderSchedule(item))
        setSchedules(normalized)
      })
      .catch(() => setMessage('Could not load schedules.'))
      .finally(() => setLoading(false))

    container.dataService.getIndex()
      .then((data) => {
        if (mounted) setIndex(data)
      })
      .catch(console.error)

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

  const openAddDialog = (dateIso: string) => {
    setEditingId(null)
    setDraftSchedule({
      date: dateIso,
      startTime: '09:00',
      endTime: '10:30',
      status: 'scheduled',
      deliveryMode: 'offline',
      teacher: actor,
      teacherId: user?.email,
      module: index?.courses[0]?.module ?? '',
      presentation: index?.courses.find(c => c.module === index?.courses[0]?.module)?.presentation ?? '',
      className: '',
      subject: '',
      room: '',
      locationUrl: '',
      note: '',
      is_makeup: false,
    })
    setDialogOpen(true)
  }

  const openEditDialog = (scheduleId: string) => {
    const item = schedules.find((s) => s.id === scheduleId)
    if (!item) return
    setEditingId(scheduleId)
    setDraftSchedule(item)
    setDialogOpen(true)
  }

  const autoSaveSchedule = async (items: ScheduleItem[]) => {
    try {
      await container.dataService.saveSchedules(items)
      setMessage('Schedule saved.')
    } catch {
      setMessage('Could not save schedule.')
    }
  }

  const addScheduleForDate = async () => {
    if (!draftSchedule || !draftSchedule.date) return
    const now = new Date().toISOString()
    const id = `schedule_${Date.now()}`
    const item: ScheduleItem = {
      id,
      week: 1,
      activity: draftSchedule.subject || draftSchedule.activity || 'Teaching session',
      subject: draftSchedule.subject || draftSchedule.activity || 'Teaching session',
      teacher: draftSchedule.teacher || actor,
      teacherId: draftSchedule.teacherId || user?.email,
      module: draftSchedule.module,
      presentation: draftSchedule.presentation,
      className: draftSchedule.className || '',
      room: draftSchedule.room || '',
      date: draftSchedule.date,
      startTime: draftSchedule.startTime || '09:00',
      endTime: draftSchedule.endTime || '10:30',
      time: `${draftSchedule.startTime || '09:00'}-${draftSchedule.endTime || '10:30'}`,
      status: draftSchedule.status || 'scheduled',
      deliveryMode: draftSchedule.deliveryMode || 'offline',
      is_makeup: draftSchedule.is_makeup ?? false,
      note: draftSchedule.note || '',
      locationUrl: draftSchedule.locationUrl || '',
      createdBy: actor,
      updatedBy: actor,
      createdAt: now,
      updatedAt: now,
      changeLog: [makeLog(id, 'created', actor, changeReason || 'Created schedule')],
    }
    const updated = [...schedules, item]
    setSchedules(updated)
    await autoSaveSchedule(updated)

    if (draftSchedule.module && draftSchedule.presentation) {
      try {
        const course = await container.dataService.getCourse(draftSchedule.module, draftSchedule.presentation)
        const studentIds = (course.students ?? []).map(s => s.id_student)
        
        if (studentIds.length > 0) {
          const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
          await fetch(`${BASE_URL}/notify/broadcast`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              student_ids: studentIds,
              type: 'general',
              title: 'New Class Scheduled',
              content: `A new class "${item.subject}" has been scheduled on ${item.date} at ${item.startTime}.`,
              sender_role: 'instructor',
              course_code: draftSchedule.module,
            }),
          })
        }
      } catch (e) {
        console.error('Failed to notify students:', e)
      }
    }

    setDialogOpen(false)
    setDraftSchedule(null)
  }

  const updateScheduleForDate = () => {
    if (!draftSchedule || !editingId) return
    const updated = schedules.map((item) => item.id === editingId ? {
      ...item,
      subject: draftSchedule.subject || item.subject,
      className: draftSchedule.className || item.className,
      teacher: draftSchedule.teacher || item.teacher,
      date: draftSchedule.date || item.date,
      startTime: draftSchedule.startTime || item.startTime,
      endTime: draftSchedule.endTime || item.endTime,
      time: `${draftSchedule.startTime || item.startTime}-${draftSchedule.endTime || item.endTime}`,
      room: draftSchedule.room || item.room,
      locationUrl: draftSchedule.locationUrl || item.locationUrl,
      note: draftSchedule.note || item.note,
      status: draftSchedule.status || item.status,
      updatedBy: actor,
      updatedAt: new Date().toISOString(),
    } : item)
    setSchedules(updated)
    autoSaveSchedule(updated)
    setDialogOpen(false)
    setDraftSchedule(null)
    setEditingId(null)
  }

  const handleSaveDialog = () => {
    if (editingId) {
      updateScheduleForDate()
    } else {
      addScheduleForDate()
    }
  }

  const removeSchedule = (id: string) => {
    const updated = schedules.filter((item) => item.id !== id)
    setSchedules(updated)
    autoSaveSchedule(updated)
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
          <Box>
            {viewMode === 'day' && <DayView date={anchorDate} events={visibleSchedules} onSelect={(event) => openEditDialog(event.id)} />}
            {viewMode === 'week' && <WeekView dates={weekDates} events={visibleSchedules} onSelect={(event) => openEditDialog(event.id)} onAddForDate={openAddDialog} />}
            {viewMode === 'month' && <MonthView anchorDate={anchorDate} events={visibleSchedules} onSelect={(event) => openEditDialog(event.id)} onAddForDate={openAddDialog} />}
          </Box>
        )}
      </Box>

      <Dialog open={dialogOpen} onClose={() => { setDialogOpen(false); setDraftSchedule(null); setEditingId(null) }} maxWidth="sm" fullWidth>
        <DialogContent>
          <Typography sx={{ fontWeight: 700, mb: 2 }}>{editingId ? 'Edit teaching session' : 'Add teaching session'}</Typography>
          <Stack spacing={2}>
            {index && (
              <Stack direction="row" spacing={2}>
                <FormControl size="small" fullWidth disabled={!canEdit}>
                  <InputLabel sx={{ fontSize: 12 }}>Module</InputLabel>
                  <Select
                    value={draftSchedule?.module ?? ''}
                    label="Module"
                    onChange={(e) => {
                      const mod = e.target.value
                      const firstPres = index.courses.find((c) => c.module === mod)?.presentation ?? ''
                      setDraftSchedule((prev) => prev ? { ...prev, module: mod, presentation: firstPres } : prev)
                    }}
                  >
                    {[...new Set(index.courses.map((c) => c.module))].map((m) => (
                      <MenuItem key={m} value={m} sx={{ fontSize: 13 }}>{m}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <FormControl size="small" fullWidth disabled={!canEdit}>
                  <InputLabel sx={{ fontSize: 12 }}>Presentation</InputLabel>
                  <Select
                    value={draftSchedule?.presentation ?? ''}
                    label="Presentation"
                    onChange={(e) => setDraftSchedule((prev) => prev ? { ...prev, presentation: e.target.value } : prev)}
                  >
                    {index.courses.filter((c) => c.module === draftSchedule?.module).map((c) => (
                      <MenuItem key={c.presentation} value={c.presentation} sx={{ fontSize: 13 }}>{c.presentation}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Stack>
            )}
            <TextField
              size="small"
              label="Subject"
              value={draftSchedule?.subject ?? ''}
              onChange={(e) => setDraftSchedule((prev) => prev ? { ...prev, subject: e.target.value } : prev)}
              fullWidth
              disabled={!canEdit}
            />
            <TextField
              size="small"
              label="Class"
              value={draftSchedule?.className ?? ''}
              onChange={(e) => setDraftSchedule((prev) => prev ? { ...prev, className: e.target.value } : prev)}
              fullWidth
              disabled={!canEdit}
            />
            <TextField
              size="small"
              label="Teacher"
              value={draftSchedule?.teacher ?? ''}
              onChange={(e) => setDraftSchedule((prev) => prev ? { ...prev, teacher: e.target.value } : prev)}
              fullWidth
              disabled={!canEdit}
            />
            <TextField
              size="small"
              type="date"
              label="Date"
              value={draftSchedule?.date ?? ''}
              onChange={(e) => setDraftSchedule((prev) => prev ? { ...prev, date: e.target.value } : prev)}
              InputLabelProps={{ shrink: true }}
              fullWidth
              disabled={!canEdit}
            />
            <Stack direction="row" spacing={1}>
              <TextField
                size="small"
                type="time"
                label="Start"
                value={draftSchedule?.startTime ?? ''}
                onChange={(e) => setDraftSchedule((prev) => prev ? { ...prev, startTime: e.target.value } : prev)}
                InputLabelProps={{ shrink: true }}
                fullWidth
                disabled={!canEdit}
              />
              <TextField
                size="small"
                type="time"
                label="End"
                value={draftSchedule?.endTime ?? ''}
                onChange={(e) => setDraftSchedule((prev) => prev ? { ...prev, endTime: e.target.value } : prev)}
                InputLabelProps={{ shrink: true }}
                fullWidth
                disabled={!canEdit}
              />
            </Stack>
            <TextField
              size="small"
              label="Room"
              value={draftSchedule?.room ?? ''}
              onChange={(e) => setDraftSchedule((prev) => prev ? { ...prev, room: e.target.value } : prev)}
              fullWidth
              disabled={!canEdit}
            />
            <TextField
              size="small"
              label="Meeting link"
              value={draftSchedule?.locationUrl ?? ''}
              onChange={(e) => setDraftSchedule((prev) => prev ? { ...prev, locationUrl: e.target.value } : prev)}
              fullWidth
              disabled={!canEdit}
            />
            <TextField
              size="small"
              label="Note"
              value={draftSchedule?.note ?? ''}
              onChange={(e) => setDraftSchedule((prev) => prev ? { ...prev, note: e.target.value } : prev)}
              multiline
              minRows={2}
              fullWidth
              disabled={!canEdit}
            />
            <Stack direction="row" spacing={1}>
              <Button variant="contained" onClick={handleSaveDialog} disabled={!canEdit || !draftSchedule?.date}>
                {editingId ? 'Update' : 'Create'}
              </Button>
              {editingId && (
                <Button variant="outlined" color="error" onClick={() => { removeSchedule(editingId); setDialogOpen(false); setDraftSchedule(null); setEditingId(null) }} disabled={!canEdit}>
                  Delete
                </Button>
              )}
              <Button variant="outlined" onClick={() => { setDialogOpen(false); setDraftSchedule(null); setEditingId(null) }}>
                Cancel
              </Button>
            </Stack>
          </Stack>
        </DialogContent>
      </Dialog>
    </Box>
  )
}

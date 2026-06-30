import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Chip,
  Divider,
  FormControlLabel,
  Grid,
  IconButton,
  MenuItem,
  Paper,
  Stack,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Toolbar,
  Tooltip,
  Typography,
} from '@mui/material'
import AddIcon from '@mui/icons-material/AddRounded'
import CancelIcon from '@mui/icons-material/EventBusyRounded'
import ContentCopyIcon from '@mui/icons-material/ContentCopyRounded'
import DeleteIcon from '@mui/icons-material/DeleteRounded'
import RestoreIcon from '@mui/icons-material/RestoreRounded'
import SaveIcon from '@mui/icons-material/SaveRounded'
import { tokens } from '../../../theme'
import { container } from '../../../di/container'
import { useAuthStore } from '../../../shared/stores/authStore'
import { useContextStore } from '../../../shared/stores/contextStore'
import type { ScheduleChangeLog, ScheduleItem, ScheduleStatus } from '../../../types/domain'

type ViewMode = 'week' | 'month'

const statusLabels: Record<ScheduleStatus, string> = {
  scheduled: 'Scheduled',
  completed: 'Completed',
  cancelled: 'Cancelled',
  rescheduled: 'Rescheduled',
}

const statusColors: Record<ScheduleStatus, 'default' | 'success' | 'warning' | 'error'> = {
  scheduled: 'default',
  completed: 'success',
  cancelled: 'error',
  rescheduled: 'warning',
}

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
  const subject = item.subject || item.activity || ''
  const startTime = item.startTime || (item.time?.includes('-') ? item.time.split('-')[0].trim() : '')
  const endTime = item.endTime || (item.time?.includes('-') ? item.time.split('-')[1]?.trim() : '')

  return {
    ...item,
    id,
    week: Number(item.week || 1),
    activity,
    subject,
    date: item.date || '',
    startTime,
    endTime,
    time: startTime && endTime ? `${startTime}-${endTime}` : item.time || '',
    teacher: item.teacher || actor,
    className: item.className || '',
    room: item.room || '',
    locationUrl: item.locationUrl || '',
    status,
    note: item.note ?? '',
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
    if (!item.week || item.week < 1 || item.week > numWeeks) errors.push(`${label}: week must be between 1 and ${numWeeks}.`)
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

export function TeachingScheduleView() {
  const { user } = useAuthStore()
  const { selectedModule, selectedPresentation, currentWeek, numWeeks } = useContextStore()
  const actor = user?.name || user?.email || 'Teacher'
  const canEdit = editableRoles.has(user?.role ?? '')

  const [schedules, setSchedules] = useState<ScheduleItem[]>([])
  const [savedSnapshot, setSavedSnapshot] = useState<ScheduleItem[]>([])
  const [selectedId, setSelectedId] = useState('')
  const [loading, setLoading] = useState(false)
  const [viewMode, setViewMode] = useState<ViewMode>('week')
  const [weekFilter, setWeekFilter] = useState(currentWeek)
  const [teacherFilter, setTeacherFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState<'all' | ScheduleStatus>('all')
  const [changeReason, setChangeReason] = useState('')
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!selectedModule || !selectedPresentation) {
      setSchedules([])
      setSavedSnapshot([])
      return
    }

    let mounted = true
    setLoading(true)
    container.dataService.getSchedules(selectedModule, selectedPresentation)
      .then((items) => {
        if (!mounted) return
        const normalized = items.map((item, index) => normalizeSchedule(item, index, actor))
        setSchedules(normalized)
        setSavedSnapshot(normalized)
        setSelectedId(normalized[0]?.id ?? '')
      })
      .catch(() => setMessage('Could not load schedules.'))
      .finally(() => setLoading(false))

    return () => { mounted = false }
  }, [selectedModule, selectedPresentation])

  const teachers = useMemo(() => {
    return [...new Set(schedules.map((item) => item.teacher).filter(Boolean))] as string[]
  }, [schedules])

  const validationErrors = useMemo(() => validateSchedules(schedules, numWeeks), [schedules, numWeeks])

  const visibleSchedules = useMemo(() => {
    return schedules
      .filter((item) => viewMode === 'month' || item.week === weekFilter)
      .filter((item) => teacherFilter === 'all' || item.teacher === teacherFilter)
      .filter((item) => statusFilter === 'all' || item.status === statusFilter)
      .sort((a, b) => `${a.date} ${a.startTime}`.localeCompare(`${b.date} ${b.startTime}`))
  }, [schedules, viewMode, weekFilter, teacherFilter, statusFilter])

  const selected = schedules.find((item) => item.id === selectedId) ?? visibleSchedules[0] ?? schedules[0]

  const updateSelected = (patch: Partial<ScheduleItem>) => {
    if (!selected) return
    setSchedules((items) => items.map((item) => {
      if (item.id !== selected.id) return item
      const startTime = patch.startTime ?? item.startTime
      const endTime = patch.endTime ?? item.endTime
      return {
        ...item,
        ...patch,
        activity: patch.subject ?? item.activity,
        time: startTime && endTime ? `${startTime}-${endTime}` : item.time,
        updatedBy: actor,
        updatedAt: new Date().toISOString(),
      }
    }))
  }

  const addSchedule = () => {
    const now = new Date().toISOString()
    const id = `schedule_${Date.now()}`
    const item: ScheduleItem = {
      id,
      week: weekFilter || currentWeek,
      activity: 'New teaching session',
      subject: 'New teaching session',
      teacher: actor,
      className: selectedModule || 'Class',
      room: '',
      date: todayIso(),
      startTime: '09:00',
      endTime: '10:30',
      time: '09:00-10:30',
      status: 'scheduled',
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

  const duplicateSchedule = (item: ScheduleItem) => {
    const id = `schedule_${Date.now()}`
    const copy = {
      ...item,
      id,
      status: 'scheduled' as ScheduleStatus,
      note: item.note ? `${item.note} (copy)` : '',
      createdBy: actor,
      updatedBy: actor,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      changeLog: [makeLog(id, 'created', actor, 'Duplicated schedule')],
    }
    setSchedules((items) => [...items, copy])
    setSelectedId(id)
  }

  const setStatus = (item: ScheduleItem, status: ScheduleStatus) => {
    const action = status === 'cancelled' ? 'cancelled' : 'restored'
    setSchedules((items) => items.map((current) => current.id === item.id
      ? {
          ...current,
          status,
          updatedBy: actor,
          updatedAt: new Date().toISOString(),
          changeLog: [...(current.changeLog ?? []), makeLog(current.id, action, actor, changeReason, current, { ...current, status })],
        }
      : current
    ))
  }

  const removeSchedule = (id: string) => {
    setSchedules((items) => items.filter((item) => item.id !== id))
    if (selectedId === id) setSelectedId('')
  }

  const saveSchedules = async () => {
    if (!selectedModule || !selectedPresentation) return
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
      await container.dataService.saveSchedules(selectedModule, selectedPresentation, schedulesWithLogs)
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
    total: schedules.length,
    active: schedules.filter((item) => item.status !== 'cancelled').length,
    conflicts: validationErrors.length,
    makeups: schedules.filter((item) => item.is_makeup).length,
  }

  if (!selectedModule || !selectedPresentation) {
    return (
      <Box sx={{ p: 4 }}>
        <Alert severity="info">Select a course first to view and update the teaching schedule.</Alert>
      </Box>
    )
  }

  return (
    <Box sx={{ minHeight: '100%', bgcolor: tokens.surface.default }}>
      <Toolbar sx={{ px: 3, bgcolor: tokens.surface.paper, borderBottom: `1px solid ${tokens.border.default}` }}>
        <Box sx={{ flexGrow: 1 }}>
          <Typography sx={{ fontWeight: 700, color: tokens.text.primary }}>Teaching Schedule</Typography>
          <Typography sx={{ fontSize: 12, color: tokens.text.secondary }}>{selectedModule} / {selectedPresentation}</Typography>
        </Box>
        <Button startIcon={<AddIcon />} variant="contained" onClick={addSchedule} disabled={!canEdit}>
          Add session
        </Button>
        <Button startIcon={<SaveIcon />} sx={{ ml: 1 }} variant="outlined" onClick={saveSchedules} disabled={!canEdit || loading}>
          Save
        </Button>
      </Toolbar>

      <Box sx={{ p: 3 }}>
        {message && <Alert sx={{ mb: 2 }} severity={message.includes('success') ? 'success' : 'warning'} onClose={() => setMessage('')}>{message}</Alert>}
        {!canEdit && <Alert sx={{ mb: 2 }} severity="info">Your role can view schedules but cannot update them.</Alert>}
        {validationErrors.length > 0 && (
          <Alert sx={{ mb: 2 }} severity="error">
            {validationErrors.slice(0, 4).join(' ')}
            {validationErrors.length > 4 ? ` +${validationErrors.length - 4} more.` : ''}
          </Alert>
        )}

        <Grid container spacing={2} sx={{ mb: 2 }}>
          {[
            ['Total sessions', stats.total],
            ['Active sessions', stats.active],
            ['Conflicts', stats.conflicts],
            ['Make-up sessions', stats.makeups],
          ].map(([label, value]) => (
            <Grid item xs={6} md={3} key={label}>
              <Paper sx={{ p: 2, border: `1px solid ${tokens.border.default}`, borderRadius: 2 }}>
                <Typography sx={{ fontSize: 11, color: tokens.text.secondary, textTransform: 'uppercase' }}>{label}</Typography>
                <Typography sx={{ mt: 0.5, fontSize: 24, fontWeight: 700 }}>{value}</Typography>
              </Paper>
            </Grid>
          ))}
        </Grid>

        <Paper sx={{ p: 2, mb: 2, border: `1px solid ${tokens.border.default}`, borderRadius: 2 }}>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems={{ xs: 'stretch', md: 'center' }}>
            <TextField select size="small" label="View" value={viewMode} onChange={(e) => setViewMode(e.target.value as ViewMode)} sx={{ minWidth: 140 }}>
              <MenuItem value="week">Week</MenuItem>
              <MenuItem value="month">All weeks</MenuItem>
            </TextField>
            <TextField size="small" type="number" label="Week" value={weekFilter} disabled={viewMode === 'month'} onChange={(e) => setWeekFilter(Number(e.target.value))} sx={{ width: 120 }} />
            <TextField select size="small" label="Teacher" value={teacherFilter} onChange={(e) => setTeacherFilter(e.target.value)} sx={{ minWidth: 180 }}>
              <MenuItem value="all">All teachers</MenuItem>
              {teachers.map((teacher) => <MenuItem key={teacher} value={teacher}>{teacher}</MenuItem>)}
            </TextField>
            <TextField select size="small" label="Status" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value as 'all' | ScheduleStatus)} sx={{ minWidth: 160 }}>
              <MenuItem value="all">All statuses</MenuItem>
              {Object.entries(statusLabels).map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}
            </TextField>
            <TextField size="small" label="Change reason" value={changeReason} onChange={(e) => setChangeReason(e.target.value)} sx={{ flexGrow: 1 }} />
          </Stack>
        </Paper>

        <Grid container spacing={2}>
          <Grid item xs={12} lg={8}>
            <Paper sx={{ border: `1px solid ${tokens.border.default}`, borderRadius: 2, overflow: 'hidden' }}>
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: tokens.surface.raised }}>
                    <TableCell>Week</TableCell>
                    <TableCell>Date</TableCell>
                    <TableCell>Time</TableCell>
                    <TableCell>Subject</TableCell>
                    <TableCell>Class</TableCell>
                    <TableCell>Teacher</TableCell>
                    <TableCell>Room</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {visibleSchedules.map((item) => (
                    <TableRow
                      key={item.id}
                      hover
                      selected={item.id === selected?.id}
                      onClick={() => setSelectedId(item.id)}
                      sx={{ cursor: 'pointer' }}
                    >
                      <TableCell>{item.week}</TableCell>
                      <TableCell>{item.date || 'No date'}</TableCell>
                      <TableCell>{item.startTime && item.endTime ? `${item.startTime}-${item.endTime}` : item.time}</TableCell>
                      <TableCell>{item.subject || item.activity}</TableCell>
                      <TableCell>{item.className || '-'}</TableCell>
                      <TableCell>{item.teacher || '-'}</TableCell>
                      <TableCell>{item.room || '-'}</TableCell>
                      <TableCell>
                        <Chip size="small" label={statusLabels[item.status ?? 'scheduled']} color={statusColors[item.status ?? 'scheduled']} />
                      </TableCell>
                      <TableCell align="right" onClick={(event) => event.stopPropagation()}>
                        <Tooltip title="Duplicate">
                          <span><IconButton size="small" onClick={() => duplicateSchedule(item)} disabled={!canEdit}><ContentCopyIcon fontSize="small" /></IconButton></span>
                        </Tooltip>
                        {item.status === 'cancelled' ? (
                          <Tooltip title="Restore">
                            <span><IconButton size="small" onClick={() => setStatus(item, 'scheduled')} disabled={!canEdit}><RestoreIcon fontSize="small" /></IconButton></span>
                          </Tooltip>
                        ) : (
                          <Tooltip title="Cancel">
                            <span><IconButton size="small" onClick={() => setStatus(item, 'cancelled')} disabled={!canEdit}><CancelIcon fontSize="small" /></IconButton></span>
                          </Tooltip>
                        )}
                        <Tooltip title="Delete draft">
                          <span><IconButton size="small" onClick={() => removeSchedule(item.id)} disabled={!canEdit}><DeleteIcon fontSize="small" /></IconButton></span>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                  {visibleSchedules.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={9}>
                        <Typography sx={{ py: 4, textAlign: 'center', color: tokens.text.secondary }}>No sessions match the current filters.</Typography>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </Paper>
          </Grid>

          <Grid item xs={12} lg={4}>
            <Paper sx={{ p: 2, border: `1px solid ${tokens.border.default}`, borderRadius: 2 }}>
              <Typography sx={{ fontWeight: 700, mb: 1 }}>Session details</Typography>
              {selected ? (
                <Stack spacing={1.5}>
                  <TextField size="small" label="Subject" value={selected.subject ?? ''} onChange={(e) => updateSelected({ subject: e.target.value })} disabled={!canEdit} />
                  <Grid container spacing={1}>
                    <Grid item xs={4}><TextField fullWidth size="small" type="number" label="Week" value={selected.week} onChange={(e) => updateSelected({ week: Number(e.target.value) })} disabled={!canEdit} /></Grid>
                    <Grid item xs={8}><TextField fullWidth size="small" type="date" label="Date" value={selected.date ?? ''} onChange={(e) => updateSelected({ date: e.target.value })} InputLabelProps={{ shrink: true }} disabled={!canEdit} /></Grid>
                  </Grid>
                  <Grid container spacing={1}>
                    <Grid item xs={6}><TextField fullWidth size="small" type="time" label="Start" value={selected.startTime ?? ''} onChange={(e) => updateSelected({ startTime: e.target.value })} InputLabelProps={{ shrink: true }} disabled={!canEdit} /></Grid>
                    <Grid item xs={6}><TextField fullWidth size="small" type="time" label="End" value={selected.endTime ?? ''} onChange={(e) => updateSelected({ endTime: e.target.value })} InputLabelProps={{ shrink: true }} disabled={!canEdit} /></Grid>
                  </Grid>
                  <TextField size="small" label="Class" value={selected.className ?? ''} onChange={(e) => updateSelected({ className: e.target.value })} disabled={!canEdit} />
                  <TextField size="small" label="Teacher" value={selected.teacher ?? ''} onChange={(e) => updateSelected({ teacher: e.target.value })} disabled={!canEdit} />
                  <TextField size="small" label="Room" value={selected.room ?? ''} onChange={(e) => updateSelected({ room: e.target.value })} disabled={!canEdit} />
                  <TextField size="small" label="Online link" value={selected.locationUrl ?? ''} onChange={(e) => updateSelected({ locationUrl: e.target.value })} disabled={!canEdit} />
                  <TextField select size="small" label="Status" value={selected.status ?? 'scheduled'} onChange={(e) => updateSelected({ status: e.target.value as ScheduleStatus })} disabled={!canEdit}>
                    {Object.entries(statusLabels).map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}
                  </TextField>
                  <FormControlLabel control={<Switch checked={!!selected.is_makeup} onChange={(e) => updateSelected({ is_makeup: e.target.checked })} disabled={!canEdit} />} label="Make-up session" />
                  <TextField size="small" label="Note" value={selected.note ?? ''} onChange={(e) => updateSelected({ note: e.target.value })} multiline minRows={2} disabled={!canEdit} />

                  <Divider />
                  <Typography sx={{ fontWeight: 700, fontSize: 13 }}>Change history</Typography>
                  <Stack spacing={1} sx={{ maxHeight: 180, overflow: 'auto' }}>
                    {(selected.changeLog ?? []).slice().reverse().map((log) => (
                      <Box key={log.id} sx={{ borderLeft: `2px solid ${tokens.brand.primaryLight}`, pl: 1 }}>
                        <Typography sx={{ fontSize: 12, fontWeight: 600 }}>{log.action} / {new Date(log.changedAt).toLocaleString()}</Typography>
                        <Typography sx={{ fontSize: 12, color: tokens.text.secondary }}>{log.changedBy}: {log.reason}</Typography>
                      </Box>
                    ))}
                    {(selected.changeLog ?? []).length === 0 && <Typography sx={{ fontSize: 12, color: tokens.text.secondary }}>No changes recorded yet.</Typography>}
                  </Stack>
                </Stack>
              ) : (
                <Typography sx={{ color: tokens.text.secondary }}>Select or add a session to edit details.</Typography>
              )}
            </Paper>
          </Grid>
        </Grid>
      </Box>
    </Box>
  )
}

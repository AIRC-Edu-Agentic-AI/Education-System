import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Autocomplete,
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

type ScheduleStatus = 'scheduled' | 'completed' | 'cancelled' | 'rescheduled'

interface ScheduleChangeLog {
  id: string
  scheduleId: string
  changedAt: string
  changedBy: string
  action: 'created' | 'updated' | 'cancelled' | 'restored'
  reason: string
}

interface Schedule {
  _id?: string
  module: string
  presentation: string
  week: number
  date: string
  startTime: string
  endTime: string
  subject: string
  className: string
  teacher: string
  room: string
  status: ScheduleStatus
  isMakeup: boolean
  note: string
  changeLog: ScheduleChangeLog[]
}

type ViewMode = 'week' | 'month'

interface ScheduleCrudProps {
  module: string
  presentation: string
}

const API_BASE = 'http://localhost:8000/api/schedules'
const CLASSES_API = 'http://localhost:8000/api/classes'
const ROOMS_API = 'http://localhost:8000/api/rooms'

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

const actor = 'Teacher'
const numWeeks = 15

function todayIso() {
  return new Date().toISOString().slice(0, 10)
}

function minutes(time?: string) {
  if (!time) return NaN
  const [hours, mins] = time.split(':').map(Number)
  return hours * 60 + mins
}

function overlaps(a: Schedule, b: Schedule) {
  return minutes(a.startTime) < minutes(b.endTime) && minutes(b.startTime) < minutes(a.endTime)
}

function normalizeSchedule(item: Partial<Schedule>): Schedule {
  return {
    _id: item._id,
    module: item.module || '',
    presentation: item.presentation || '',
    week: Number(item.week || 1),
    date: item.date || '',
    startTime: item.startTime || '',
    endTime: item.endTime || '',
    subject: item.subject || '',
    className: item.className || '',
    teacher: item.teacher || '',
    room: item.room || '',
    status: item.status || 'scheduled',
    isMakeup: !!item.isMakeup,
    note: item.note || '',
    changeLog: item.changeLog || [],
  }
}

function extractNames(data: unknown): string[] {
  if (!Array.isArray(data)) return []
  return data.map((entry) => (typeof entry === 'string' ? entry : entry?.name || entry?.className || entry?.room || '')).filter(Boolean)
}

function makeLog(scheduleId: string, action: ScheduleChangeLog['action'], reason: string): ScheduleChangeLog {
  return {
    id: `log_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    scheduleId,
    changedAt: new Date().toISOString(),
    changedBy: actor,
    action,
    reason: reason.trim() || 'Schedule updated',
  }
}

function validateSchedules(items: Schedule[]) {
  const errors: string[] = []
  const activeItems = items.filter((item) => item.status !== 'cancelled')

  items.forEach((item) => {
    const label = item.subject || item._id || 'Untitled'
    if (!item.week || item.week < 1 || item.week > numWeeks) errors.push(`${label}: week must be between 1 and ${numWeeks}.`)
    if (!item.date) errors.push(`${label}: date is required.`)
    if (!item.startTime || !item.endTime) errors.push(`${label}: start and end time are required.`)
    if (item.startTime && item.endTime && minutes(item.startTime) >= minutes(item.endTime)) {
      errors.push(`${label}: start time must be before end time.`)
    }
    if (!item.teacher.trim()) errors.push(`${label}: teacher is required.`)
    if (!item.className.trim()) errors.push(`${label}: class is required.`)
    if (!item.subject.trim()) errors.push(`${label}: subject is required.`)
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

export default function ScheduleCrud({ module, presentation }: ScheduleCrudProps) {
  const [schedules, setSchedules] = useState<Schedule[]>([])
  const [classOptions, setClassOptions] = useState<string[]>([])
  const [roomOptions, setRoomOptions] = useState<string[]>([])
  const [selectedId, setSelectedId] = useState('')
  const [loading, setLoading] = useState(false)
  const [viewMode, setViewMode] = useState<ViewMode>('week')
  const [weekFilter, setWeekFilter] = useState(1)
  const [teacherFilter, setTeacherFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState<'all' | ScheduleStatus>('all')
  const [changeReason, setChangeReason] = useState('')
  const [message, setMessage] = useState('')

  const fetchSchedules = async () => {
    if (!module || !presentation) {
      setSchedules([])
      setSelectedId('')
      return
    }

    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}?module=${encodeURIComponent(module)}&presentation=${encodeURIComponent(presentation)}`)
      const data = await res.json()
      const normalized = (data as Partial<Schedule>[])
        .map(normalizeSchedule)
        .filter((item) => item.module === module && item.presentation === presentation)
      setSchedules(normalized)
      setSelectedId(normalized[0]?._id ?? '')
    } catch {
      setMessage('Could not load schedules.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSchedules()
  }, [module, presentation])

  useEffect(() => {
    fetch(CLASSES_API)
      .then((res) => res.json())
      .then((data) => setClassOptions(extractNames(data)))
      .catch(() => setClassOptions([]))

    fetch(ROOMS_API)
      .then((res) => res.json())
      .then((data) => setRoomOptions(extractNames(data)))
      .catch(() => setRoomOptions([]))
  }, [])

  const teachers = useMemo(() => {
    return [...new Set(schedules.map((item) => item.teacher).filter(Boolean))]
  }, [schedules])

  const validationErrors = useMemo(() => validateSchedules(schedules), [schedules])

  const visibleSchedules = useMemo(() => {
    return schedules
      .filter((item) => viewMode === 'month' || item.week === weekFilter)
      .filter((item) => teacherFilter === 'all' || item.teacher === teacherFilter)
      .filter((item) => statusFilter === 'all' || item.status === statusFilter)
      .sort((a, b) => `${a.date} ${a.startTime}`.localeCompare(`${b.date} ${b.startTime}`))
  }, [schedules, viewMode, weekFilter, teacherFilter, statusFilter])

  const selected = schedules.find((item) => item._id === selectedId) ?? visibleSchedules[0] ?? schedules[0]

  const updateSelected = (patch: Partial<Schedule>) => {
    if (!selected) return
    setSchedules((items) => items.map((item) => (item._id === selected._id ? { ...item, ...patch } : item)))
  }

  const addSchedule = () => {
    const newItem: Schedule = {
      module,
      presentation,
      week: weekFilter,
      date: todayIso(),
      startTime: '09:00',
      endTime: '10:30',
      subject: 'New teaching session',
      className: '',
      teacher: actor,
      room: '',
      status: 'scheduled',
      isMakeup: false,
      note: '',
      changeLog: [],
    }

    fetch(API_BASE, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newItem),
    })
      .then((res) => res.json())
      .then((created) => {
        const normalized = normalizeSchedule(created)
        normalized.changeLog = [makeLog(normalized._id || '', 'created', changeReason || 'Created schedule')]
        setSchedules((items) => [...items, normalized])
        setSelectedId(normalized._id ?? '')
      })
      .catch(() => setMessage('Could not add schedule.'))
  }

  const duplicateSchedule = (item: Schedule) => {
    const copy: Schedule = {
      ...item,
      _id: undefined,
      status: 'scheduled',
      note: item.note ? `${item.note} (copy)` : '',
      changeLog: [],
    }

    fetch(API_BASE, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(copy),
    })
      .then((res) => res.json())
      .then((created) => {
        const normalized = normalizeSchedule(created)
        normalized.changeLog = [makeLog(normalized._id || '', 'created', 'Duplicated schedule')]
        setSchedules((items) => [...items, normalized])
        setSelectedId(normalized._id ?? '')
      })
      .catch(() => setMessage('Could not duplicate schedule.'))
  }

  const setStatus = async (item: Schedule, status: ScheduleStatus) => {
    const action = status === 'cancelled' ? 'cancelled' : 'restored'
    const updated: Schedule = {
      ...item,
      status,
      changeLog: [...item.changeLog, makeLog(item._id || '', action, changeReason)],
    }

    try {
      await fetch(`${API_BASE}/${item._id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updated),
      })
      setSchedules((items) => items.map((current) => (current._id === item._id ? updated : current)))
    } catch {
      setMessage('Could not update schedule status.')
    }
  }

  const removeSchedule = async (id: string) => {
    try {
      await fetch(`${API_BASE}/${id}`, { method: 'DELETE' })
      setSchedules((items) => items.filter((item) => item._id !== id))
      if (selectedId === id) setSelectedId('')
    } catch {
      setMessage('Could not delete schedule.')
    }
  }

  const saveSchedules = async () => {
    if (validationErrors.length > 0) {
      setMessage('Please fix schedule conflicts before saving.')
      return
    }

    setLoading(true)
    try {
      await Promise.all(
        schedules.map((item) =>
          item._id
            ? fetch(`${API_BASE}/${item._id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(item),
              })
            : Promise.resolve()
        )
      )
      setChangeReason('')
      setMessage('Schedule saved successfully.')
      fetchSchedules()
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
    makeups: schedules.filter((item) => item.isMakeup).length,
  }

  if (!module || !presentation) {
    return (
      <Box sx={{ p: 4 }}>
        <Alert severity="info">Select a module and presentation first to view the teaching schedule.</Alert>
      </Box>
    )
  }

  return (
    <Box sx={{ minHeight: '100%', bgcolor: 'background.default' }}>
      <Toolbar sx={{ px: 3, bgcolor: 'background.paper', borderBottom: '1px solid', borderColor: 'divider' }}>
        <Box sx={{ flexGrow: 1 }}>
          <Typography sx={{ fontWeight: 700 }}>Schedule Management</Typography>
          <Typography sx={{ fontSize: 12, color: 'text.secondary' }}>{module} / {presentation}</Typography>
        </Box>
        <Button startIcon={<AddIcon />} variant="contained" onClick={addSchedule}>
          Add session
        </Button>
        <Button startIcon={<SaveIcon />} sx={{ ml: 1 }} variant="outlined" onClick={saveSchedules} disabled={loading}>
          Save
        </Button>
      </Toolbar>

      <Box sx={{ p: 3 }}>
        {message && (
          <Alert sx={{ mb: 2 }} severity={message.includes('success') ? 'success' : 'warning'} onClose={() => setMessage('')}>
            {message}
          </Alert>
        )}
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
              <Paper sx={{ p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 2 }}>
                <Typography sx={{ fontSize: 11, color: 'text.secondary', textTransform: 'uppercase' }}>{label}</Typography>
                <Typography sx={{ mt: 0.5, fontSize: 24, fontWeight: 700 }}>{value}</Typography>
              </Paper>
            </Grid>
          ))}
        </Grid>

        <Paper sx={{ p: 2, mb: 2, border: '1px solid', borderColor: 'divider', borderRadius: 2 }}>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems={{ xs: 'stretch', md: 'center' }}>
            <TextField select size="small" label="View" value={viewMode} onChange={(e) => setViewMode(e.target.value as ViewMode)} sx={{ minWidth: 140 }}>
              <MenuItem value="week">Week</MenuItem>
              <MenuItem value="month">All weeks</MenuItem>
            </TextField>
            <TextField size="small" type="number" label="Week" value={weekFilter} disabled={viewMode === 'month'} onChange={(e) => setWeekFilter(Number(e.target.value))} sx={{ width: 120 }} />
            <TextField select size="small" label="Teacher" value={teacherFilter} onChange={(e) => setTeacherFilter(e.target.value)} sx={{ minWidth: 180 }}>
              <MenuItem value="all">All teachers</MenuItem>
              {teachers.map((teacher) => (
                <MenuItem key={teacher} value={teacher}>{teacher}</MenuItem>
              ))}
            </TextField>
            <TextField select size="small" label="Status" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value as 'all' | ScheduleStatus)} sx={{ minWidth: 160 }}>
              <MenuItem value="all">All statuses</MenuItem>
              {Object.entries(statusLabels).map(([value, label]) => (
                <MenuItem key={value} value={value}>{label}</MenuItem>
              ))}
            </TextField>
            <TextField size="small" label="Change reason" value={changeReason} onChange={(e) => setChangeReason(e.target.value)} sx={{ flexGrow: 1 }} />
          </Stack>
        </Paper>

        <Grid container spacing={2}>
          <Grid item xs={12} lg={8}>
            <Paper sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 2, overflow: 'hidden' }}>
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: 'action.hover' }}>
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
                      key={item._id}
                      hover
                      selected={item._id === selected?._id}
                      onClick={() => setSelectedId(item._id ?? '')}
                      sx={{ cursor: 'pointer' }}
                    >
                      <TableCell>{item.week}</TableCell>
                      <TableCell>{item.date || 'No date'}</TableCell>
                      <TableCell>{item.startTime && item.endTime ? `${item.startTime}-${item.endTime}` : '-'}</TableCell>
                      <TableCell>{item.subject}</TableCell>
                      <TableCell>{item.className || '-'}</TableCell>
                      <TableCell>{item.teacher || '-'}</TableCell>
                      <TableCell>{item.room || '-'}</TableCell>
                      <TableCell>
                        <Chip size="small" label={statusLabels[item.status]} color={statusColors[item.status]} />
                      </TableCell>
                      <TableCell align="right" onClick={(event) => event.stopPropagation()}>
                        <Tooltip title="Duplicate">
                          <IconButton size="small" onClick={() => duplicateSchedule(item)}>
                            <ContentCopyIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        {item.status === 'cancelled' ? (
                          <Tooltip title="Restore">
                            <IconButton size="small" onClick={() => setStatus(item, 'scheduled')}>
                              <RestoreIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        ) : (
                          <Tooltip title="Cancel">
                            <IconButton size="small" onClick={() => setStatus(item, 'cancelled')}>
                              <CancelIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        )}
                        <Tooltip title="Delete">
                          <IconButton size="small" onClick={() => item._id && removeSchedule(item._id)}>
                            <DeleteIcon fontSize="small" sx={{ color: 'error.main' }} />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                  {visibleSchedules.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={9}>
                        <Typography sx={{ py: 4, textAlign: 'center', color: 'text.secondary' }}>No sessions match the current filters.</Typography>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </Paper>
          </Grid>

          <Grid item xs={12} lg={4}>
            <Paper sx={{ p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 2 }}>
              <Typography sx={{ fontWeight: 700, mb: 1 }}>Session details</Typography>
              {selected ? (
                <Stack spacing={1.5}>
                  <TextField size="small" label="Subject" value={selected.subject} onChange={(e) => updateSelected({ subject: e.target.value })} />
                  <Grid container spacing={1}>
                    <Grid item xs={4}>
                      <TextField fullWidth size="small" type="number" label="Week" value={selected.week} onChange={(e) => updateSelected({ week: Number(e.target.value) })} />
                    </Grid>
                    <Grid item xs={8}>
                      <TextField fullWidth size="small" type="date" label="Date" value={selected.date} onChange={(e) => updateSelected({ date: e.target.value })} InputLabelProps={{ shrink: true }} />
                    </Grid>
                  </Grid>
                  <Grid container spacing={1}>
                    <Grid item xs={6}>
                      <TextField fullWidth size="small" type="time" label="Start" value={selected.startTime} onChange={(e) => updateSelected({ startTime: e.target.value })} InputLabelProps={{ shrink: true }} />
                    </Grid>
                    <Grid item xs={6}>
                      <TextField fullWidth size="small" type="time" label="End" value={selected.endTime} onChange={(e) => updateSelected({ endTime: e.target.value })} InputLabelProps={{ shrink: true }} />
                    </Grid>
                  </Grid>
                  <Autocomplete
                    size="small"
                    options={classOptions}
                    value={selected.className || null}
                    onChange={(_, value) => updateSelected({ className: value || '' })}
                    renderInput={(params) => <TextField {...params} label="Class" />}
                  />
                  <TextField size="small" label="Teacher" value={selected.teacher} onChange={(e) => updateSelected({ teacher: e.target.value })} />
                  <Autocomplete
                    size="small"
                    options={roomOptions}
                    value={selected.room || null}
                    onChange={(_, value) => updateSelected({ room: value || '' })}
                    renderInput={(params) => <TextField {...params} label="Room" />}
                  />
                  <TextField select size="small" label="Status" value={selected.status} onChange={(e) => updateSelected({ status: e.target.value as ScheduleStatus })}>
                    {Object.entries(statusLabels).map(([value, label]) => (
                      <MenuItem key={value} value={value}>{label}</MenuItem>
                    ))}
                  </TextField>
                  <FormControlLabel control={<Switch checked={selected.isMakeup} onChange={(e) => updateSelected({ isMakeup: e.target.checked })} />} label="Make-up session" />
                  <TextField size="small" label="Note" value={selected.note} onChange={(e) => updateSelected({ note: e.target.value })} multiline minRows={2} />

                  <Divider />
                  <Typography sx={{ fontWeight: 700, fontSize: 13 }}>Change history</Typography>
                  <Stack spacing={1} sx={{ maxHeight: 180, overflow: 'auto' }}>
                    {selected.changeLog.slice().reverse().map((log) => (
                      <Box key={log.id} sx={{ borderLeft: '2px solid', borderColor: 'primary.light', pl: 1 }}>
                        <Typography sx={{ fontSize: 12, fontWeight: 600 }}>{log.action} / {new Date(log.changedAt).toLocaleString()}</Typography>
                        <Typography sx={{ fontSize: 12, color: 'text.secondary' }}>{log.changedBy}: {log.reason}</Typography>
                      </Box>
                    ))}
                    {selected.changeLog.length === 0 && <Typography sx={{ fontSize: 12, color: 'text.secondary' }}>No changes recorded yet.</Typography>}
                  </Stack>
                </Stack>
              ) : (
                <Typography sx={{ color: 'text.secondary' }}>Select or add a session to edit details.</Typography>
              )}
            </Paper>
          </Grid>
        </Grid>
      </Box>
    </Box>
  )
}

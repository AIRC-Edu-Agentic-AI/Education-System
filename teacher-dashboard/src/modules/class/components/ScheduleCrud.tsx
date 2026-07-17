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
  Card,
  Stack,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
  TableContainer,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material'
import AddIcon from '@mui/icons-material/AddRounded'
import CancelIcon from '@mui/icons-material/EventBusyRounded'
import ContentCopyIcon from '@mui/icons-material/ContentCopyRounded'
import DeleteIcon from '@mui/icons-material/DeleteRounded'
import RestoreIcon from '@mui/icons-material/RestoreRounded'
import SaveIcon from '@mui/icons-material/SaveRounded'
import HistoryIcon from '@mui/icons-material/HistoryRounded'
import ExpandMoreIcon from '@mui/icons-material/ExpandMoreRounded'
import { COURSE_MAPPING } from '../utils/courseMapping'

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

interface ScheduleCrudProps {
  module: string
  presentation: string
}

const _API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000/api'
const API_BASE = `${_API_BASE}/schedules`
const CLASSES_API = `${_API_BASE}/classes`
const ROOMS_API = `${_API_BASE}/rooms`

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

function minutes(time?: string) {
  if (!time) return NaN
  const [hours, mins] = time.split(':').map(Number)
  return hours * 60 + mins
}

function overlaps(a: Schedule, b: Schedule) {
  // Bỏ qua kiểm tra trùng nếu chưa nhập đủ thời gian
  if (!a.startTime || !a.endTime || !b.startTime || !b.endTime) return false;
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
    const label = item.subject || item.className || 'New Session'
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
      if (item.teacher && item.teacher === other.teacher) errors.push(`Teacher conflict: ${item.teacher} is booked on ${item.date}.`)
      if (item.className && item.className === other.className) errors.push(`Class conflict: ${item.className} is booked on ${item.date}.`)
      if (item.room && item.room === other.room) errors.push(`Room conflict: ${item.room} is booked on ${item.date}.`)
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
  
  const [weekFilter, setWeekFilter] = useState<number | 'all'>('all')
  const [teacherFilter, setTeacherFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState<'all' | ScheduleStatus>('all')
  const [changeReason, setChangeReason] = useState('')
  const [message, setMessage] = useState('')

  const subjectOptions = useMemo(() => {
    const names = Object.values(COURSE_MAPPING).map(course => course.name)
    return [...new Set(names)].sort()
  }, [])

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
    fetch(CLASSES_API).then(res => res.json()).then(data => setClassOptions(extractNames(data))).catch(() => {})
    fetch(ROOMS_API).then(res => res.json()).then(data => setRoomOptions(extractNames(data))).catch(() => {})
  }, [])

  const teachers = useMemo(() => [...new Set(schedules.map((item) => item.teacher).filter(Boolean))], [schedules])
  const validationErrors = useMemo(() => validateSchedules(schedules), [schedules])

  const visibleSchedules = useMemo(() => {
    return schedules
      .filter((item) => weekFilter === 'all' || item.week === weekFilter)
      .filter((item) => teacherFilter === 'all' || item.teacher === teacherFilter)
      .filter((item) => statusFilter === 'all' || item.status === statusFilter)
      .sort((a, b) => `${a.date} ${a.startTime}`.localeCompare(`${b.date} ${b.startTime}`))
  }, [schedules, weekFilter, teacherFilter, statusFilter])

  const selected = schedules.find((item) => item._id === selectedId) ?? visibleSchedules[0] ?? schedules[0]

  const updateSelected = (patch: Partial<Schedule>) => {
    if (!selected) return
    setSchedules((items) => items.map((item) => (item._id === selected._id ? { ...item, ...patch } : item)))
  }

  // TẠO NHÁP: Không gọi API POST ngay lập tức
  const addSchedule = () => {
    const tempId = `temp_${Date.now()}`;
    const newItem: Schedule = {
      _id: tempId,
      module, presentation, week: weekFilter === 'all' ? 1 : weekFilter,
      date: '', startTime: '', endTime: '', 
      subject: '', className: '', teacher: '', room: '',
      status: 'scheduled', isMakeup: false, note: '', changeLog: [],
    }
    setSchedules(items => [newItem, ...items])
    setSelectedId(tempId)
  }

  // NHÂN BẢN: Cũng tạo nháp, không gọi API
  const duplicateSchedule = (item: Schedule) => {
    const tempId = `temp_${Date.now()}`;
    const copy: Schedule = { 
      ...item, 
      _id: tempId, 
      status: 'scheduled', 
      note: item.note ? `${item.note} (copy)` : '', 
      changeLog: [] 
    }
    setSchedules(items => [copy, ...items])
    setSelectedId(tempId)
  }

  const setStatus = async (item: Schedule, status: ScheduleStatus) => {
    // Không cho phép đổi trạng thái của lịch đang nháp
    if (item._id?.startsWith('temp_')) {
        updateSelected({ status });
        return;
    }
    
    const action = status === 'cancelled' ? 'cancelled' : 'restored'
    const updated: Schedule = { ...item, status, changeLog: [...item.changeLog, makeLog(item._id || '', action, changeReason)] }
    try {
      await fetch(`${API_BASE}/${item._id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(updated) })
      setSchedules(items => items.map(current => (current._id === item._id ? updated : current)))
    } catch {
      setMessage('Could not update status.')
    }
  }

  // XÓA TỨC THÌ: Bấm xóa lịch nháp thì mất luôn, không cần hỏi API
  const removeSchedule = async (id: string) => {
    if (id.startsWith('temp_')) {
      setSchedules(items => items.filter(item => item._id !== id))
      if (selectedId === id) setSelectedId('')
      return;
    }

    try {
      await fetch(`${API_BASE}/${id}`, { method: 'DELETE' })
      setSchedules(items => items.filter(item => item._id !== id))
      if (selectedId === id) setSelectedId('')
    } catch {
      setMessage('Could not delete schedule.')
    }
  }

  // LƯU TOÀN BỘ: POST lịch mới và PUT lịch cũ
  const saveSchedules = async () => {
    if (validationErrors.length > 0) return setMessage('Please fix conflicts before saving.')
    setLoading(true)
    try {
      await Promise.all(schedules.map(item => {
        const isNew = item._id?.startsWith('temp_');
        const payload = { ...item };
        
        // Tạo log nếu đây là lịch mới
        if (isNew) {
            delete payload._id;
            payload.changeLog = [makeLog('', 'created', changeReason || 'Created schedule')];
            return fetch(API_BASE, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
        } else if (item._id) {
            return fetch(`${API_BASE}/${item._id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
        }
        return Promise.resolve();
      }))
      setChangeReason('')
      setMessage('Saved successfully.')
      fetchSchedules() // Load lại DB để lấy Real ID
    } catch {
      setMessage('Could not save schedules.')
    } finally {
      setLoading(false)
    }
  }

  const stats = {
    total: schedules.length, active: schedules.filter(i => i.status !== 'cancelled').length,
    conflicts: validationErrors.length, makeups: schedules.filter(i => i.isMakeup).length,
  }

  if (!module || !presentation) return <Box sx={{ p: 3 }}><Alert severity="info">Select a module to view schedules.</Alert></Box>

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Stack direction="row" spacing={1} alignItems="center">
          <Chip size="small" label={`Total: ${stats.total}`} />
          <Chip size="small" label={`Active: ${stats.active}`} color="success" variant="outlined" />
          {stats.conflicts > 0 && <Chip size="small" label={`${stats.conflicts} Conflicts`} color="error" />}
          {stats.makeups > 0 && <Chip size="small" label={`${stats.makeups} Make-ups`} color="warning" variant="outlined" />}
        </Stack>
        <Stack direction="row" spacing={1}>
          <TextField size="small" placeholder="Reason for changes..." value={changeReason} onChange={e => setChangeReason(e.target.value)} sx={{ width: 200 }} />
          <Button startIcon={<SaveIcon />} variant="contained" onClick={saveSchedules} disabled={loading} disableElevation>
            Save All
          </Button>
        </Stack>
      </Box>

      <Box sx={{ px: 2, pb: 2, flexGrow: 1, overflow: 'hidden' }}>
        {message && <Alert sx={{ mb: 2, py: 0 }} severity={message.includes('success') ? 'success' : 'warning'} onClose={() => setMessage('')}>{message}</Alert>}
        {validationErrors.length > 0 && <Alert sx={{ mb: 2, py: 0 }} severity="error">{validationErrors[0]} {validationErrors.length > 1 ? `(+${validationErrors.length - 1} more)` : ''}</Alert>}

        <Grid container spacing={2} sx={{ height: '100%' }}>
          <Grid item xs={12} lg={8} sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <Box sx={{ display: 'flex', gap: 1, mb: 1.5 }}>
              <TextField select size="small" label="Week" value={weekFilter} onChange={e => setWeekFilter(e.target.value === 'all' ? 'all' : Number(e.target.value))} sx={{ minWidth: 100 }}>
                <MenuItem value="all">All Weeks</MenuItem>
                {[...Array(numWeeks)].map((_, i) => <MenuItem key={i + 1} value={i + 1}>Week {i + 1}</MenuItem>)}
              </TextField>
              <TextField select size="small" label="Teacher" value={teacherFilter} onChange={e => setTeacherFilter(e.target.value)} sx={{ minWidth: 150 }}>
                <MenuItem value="all">All Teachers</MenuItem>
                {teachers.map(t => <MenuItem key={t} value={t}>{t}</MenuItem>)}
              </TextField>
              <TextField select size="small" label="Status" value={statusFilter} onChange={e => setStatusFilter(e.target.value as any)} sx={{ minWidth: 140 }}>
                <MenuItem value="all">All Statuses</MenuItem>
                {Object.entries(statusLabels).map(([v, l]) => <MenuItem key={v} value={v}>{l}</MenuItem>)}
              </TextField>
            </Box>

            <Card elevation={0} sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 2, flexGrow: 1, overflow: 'hidden' }}>
              <TableContainer sx={{ height: '100%' }}>
                <Table stickyHeader size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 600 }}>Wk</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Date & Time</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Subject</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Class / Room</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Teacher</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Status</TableCell>
                      <TableCell align="right" sx={{ fontWeight: 600 }}>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {visibleSchedules.map((item) => (
                      <TableRow 
                        key={item._id} 
                        hover 
                        selected={item._id === selected?._id} 
                        onClick={() => setSelectedId(item._id ?? '')} 
                        sx={{ 
                            cursor: 'pointer',
                            // Highlight màu nền nhẹ nếu đang là nháp chưa lưu
                            ...(item._id?.startsWith('temp_') && { bgcolor: 'warning.50' }) 
                        }}
                      >
                        <TableCell>{item.week}</TableCell>
                        <TableCell>
                          <Box sx={{ fontWeight: 600, fontSize: 13 }}>{item.date || '-'}</Box>
                          <Box sx={{ fontSize: 11, color: 'text.secondary' }}>{item.startTime} - {item.endTime}</Box>
                        </TableCell>
                        <TableCell>{item.subject || <Typography color="error.main" fontSize={12}>Missing</Typography>}</TableCell>
                        <TableCell>
                          <Box sx={{ fontSize: 13 }}>{item.className || '-'}</Box>
                          <Box sx={{ fontSize: 11, color: 'text.secondary' }}>{item.room || '-'}</Box>
                        </TableCell>
                        <TableCell>{item.teacher || '-'}</TableCell>
                        <TableCell>
                          <Chip size="small" label={item._id?.startsWith('temp_') ? 'Unsaved' : statusLabels[item.status]} color={item._id?.startsWith('temp_') ? 'default' : statusColors[item.status]} sx={{ height: 20, fontSize: 10, fontWeight: 600 }} />
                        </TableCell>
                        <TableCell align="right" onClick={e => e.stopPropagation()}>
                          <IconButton size="small" onClick={() => duplicateSchedule(item)}><ContentCopyIcon sx={{ fontSize: 16 }} /></IconButton>
                          {item.status === 'cancelled' ? (
                            <IconButton size="small" onClick={() => setStatus(item, 'scheduled')}><RestoreIcon sx={{ fontSize: 16 }} /></IconButton>
                          ) : (
                            <IconButton size="small" onClick={() => setStatus(item, 'cancelled')}><CancelIcon sx={{ fontSize: 16 }} /></IconButton>
                          )}
                          <IconButton size="small" onClick={() => item._id && removeSchedule(item._id)}><DeleteIcon sx={{ fontSize: 16, color: 'error.main' }} /></IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                    {visibleSchedules.length === 0 && (
                      <TableRow><TableCell colSpan={7} sx={{ textAlign: 'center', py: 4, color: 'text.secondary' }}>No sessions found.</TableCell></TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </Card>
          </Grid>

          <Grid item xs={12} lg={4} sx={{ height: '100%' }}>
            <Card elevation={0} sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
              <Box sx={{ px: 2, py: 1.5, borderBottom: '1px solid', borderColor: 'divider', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography sx={{ fontWeight: 600 }}>Session Details</Typography>
                <Button size="small" startIcon={<AddIcon />} variant="outlined" onClick={addSchedule} sx={{ py: 0.25 }}>Add New</Button>
              </Box>
              
              <Box sx={{ p: 2, flexGrow: 1, overflowY: 'auto' }}>
                {selected ? (
                  <Stack spacing={2}>
                    <Autocomplete
                      fullWidth
                      freeSolo
                      size="small"
                      options={subjectOptions}
                      value={selected.subject || null}
                      onChange={(_, v) => updateSelected({ subject: v || '' })}
                      onInputChange={(_, v) => updateSelected({ subject: v || '' })}
                      renderInput={params => <TextField {...params} label="Subject" required />}
                    />
                    
                    <Stack direction="row" spacing={2}>
                      <Autocomplete sx={{ flex: 1 }} size="small" options={classOptions} value={selected.className || null} onChange={(_, v) => updateSelected({ className: v || '' })} renderInput={p => <TextField {...p} label="Class" required />} />
                      <TextField sx={{ flex: 1 }} size="small" label="Teacher" value={selected.teacher} onChange={e => updateSelected({ teacher: e.target.value })} required />
                    </Stack>

                    <Stack direction="row" spacing={2}>
                      <TextField sx={{ width: 80 }} size="small" type="number" label="Week" value={selected.week} onChange={e => updateSelected({ week: Number(e.target.value) })} />
                      <TextField sx={{ flex: 1 }} size="small" type="date" label="Date" value={selected.date} onChange={e => updateSelected({ date: e.target.value })} InputLabelProps={{ shrink: true }} required />
                    </Stack>

                    <Stack direction="row" spacing={2}>
                      <TextField sx={{ flex: 1 }} size="small" type="time" label="Start" value={selected.startTime} onChange={e => updateSelected({ startTime: e.target.value })} InputLabelProps={{ shrink: true }} required />
                      <TextField sx={{ flex: 1 }} size="small" type="time" label="End" value={selected.endTime} onChange={e => updateSelected({ endTime: e.target.value })} InputLabelProps={{ shrink: true }} required />
                    </Stack>

                    <Autocomplete size="small" options={roomOptions} value={selected.room || null} onChange={(_, v) => updateSelected({ room: v || '' })} renderInput={p => <TextField {...p} label="Room" />} />

                    <Stack direction="row" spacing={2} alignItems="center">
                      <TextField sx={{ flex: 1 }} select size="small" label="Status" value={selected.status} onChange={e => updateSelected({ status: e.target.value as ScheduleStatus })}>
                        {Object.entries(statusLabels).map(([v, l]) => <MenuItem key={v} value={v}>{l}</MenuItem>)}
                      </TextField>
                      <FormControlLabel sx={{ flex: 1, m: 0 }} control={<Switch size="small" checked={selected.isMakeup} onChange={e => updateSelected({ isMakeup: e.target.checked })} />} label={<Typography fontSize={13}>Make-up class</Typography>} />
                    </Stack>

                    <TextField fullWidth size="small" label="Note" value={selected.note} onChange={e => updateSelected({ note: e.target.value })} multiline minRows={2} />

                    <Accordion disableGutters elevation={0} sx={{ border: '1px solid', borderColor: 'divider', '&:before': { display: 'none' } }}>
                      <AccordionSummary expandIcon={<ExpandMoreIcon sx={{ fontSize: 18 }} />} sx={{ minHeight: 36, '& .MuiAccordionSummary-content': { my: 1 } }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}><HistoryIcon sx={{ fontSize: 16 }} /><Typography fontSize={13} fontWeight={600}>Change History</Typography></Box>
                      </AccordionSummary>
                      <AccordionDetails sx={{ pt: 0, pb: 1, px: 2, maxHeight: 150, overflowY: 'auto' }}>
                        <Stack spacing={1}>
                          {selected.changeLog.slice().reverse().map(log => (
                            <Box key={log.id} sx={{ pl: 1, borderLeft: '2px solid primary.main' }}>
                              <Typography fontSize={11} fontWeight={600} color="text.primary">{log.action} • {new Date(log.changedAt).toLocaleString()}</Typography>
                              <Typography fontSize={11} color="text.secondary">{log.changedBy}: {log.reason}</Typography>
                            </Box>
                          ))}
                          {selected.changeLog.length === 0 && <Typography fontSize={11} color="text.secondary">No modifications yet.</Typography>}
                        </Stack>
                      </AccordionDetails>
                    </Accordion>
                  </Stack>
                ) : (
                  <Box sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Typography color="text.secondary" fontSize={13}>Select a session to view details.</Typography>
                  </Box>
                )}
              </Box>
            </Card>
          </Grid>
        </Grid>
      </Box>
    </Box>
  )
}
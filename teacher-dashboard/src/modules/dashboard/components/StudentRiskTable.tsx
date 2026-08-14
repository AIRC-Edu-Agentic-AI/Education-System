import { useState, useMemo, useEffect } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000/api'
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
import {
  Typography, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, TableSortLabel, Chip, Box, TextField, InputAdornment,
  LinearProgress, TablePagination, Button, Dialog, DialogTitle,
  DialogContent, DialogActions, CircularProgress
} from '@mui/material'
import SearchIcon from '@mui/icons-material/SearchRounded'
import TrendingUpIcon from '@mui/icons-material/TrendingUpRounded'
import TrendingDownIcon from '@mui/icons-material/TrendingDownRounded'
import RemoveIcon from '@mui/icons-material/RemoveRounded'
import { TIER_COLORS, type TierNumber } from '../../../shared/constants/tiers'
import { tokens } from '../../../theme'
import type { StudentProfile } from '../../../types/domain'

type LocalStudentProfile = StudentProfile & { name?: string }

interface Props {
  students: LocalStudentProfile[]
  currentWeek: number
  onSelect: (s: LocalStudentProfile) => void
  selectedId: number | null
  module?: string
  presentation?: string
}

function riskTrend(s: LocalStudentProfile, week: number): 'up' | 'down' | 'flat' {
  const wi = week - 1
  if (wi < 2) return 'flat'
  const delta = (s.risk_by_week[wi] ?? 0) - (s.risk_by_week[wi - 2] ?? 0)
  if (delta > 0.05) return 'up'
  if (delta < -0.05) return 'down'
  return 'flat'
}

export function StudentRiskTable({ students, currentWeek, onSelect, selectedId, module, presentation }: Props) {
  const [sortField, setSortField] = useState<'risk' | 'id' | 'imd' | 'name'>('risk')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(10)

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search)
      setPage(0)
    }, 150)
    return () => clearTimeout(timer)
  }, [search])

  // --- Dialog & API States ---
  const [warningStudent, setWarningStudent] = useState<LocalStudentProfile | null>(null)
  const [warningMessage, setWarningMessage] = useState('')
  const [isSending, setIsSending] = useState(false)

  const [tierFilter, setTierFilter] = useState<'all' | '1' | '2' | '3'>('all')
  const [scoreFilter, setScoreFilter] = useState<'all' | 'high' | 'good' | 'average' | 'low'>('all')
  
  // --- Group Broadcast Dialog States ---
  const [groupBroadcastOpen, setGroupBroadcastOpen] = useState(false)
  const [groupBroadcastTitle, setGroupBroadcastTitle] = useState('')
  const [groupBroadcastContent, setGroupBroadcastContent] = useState('')
  const [groupBroadcastType, setGroupBroadcastType] = useState('academic_warning')
  const [isGroupSending, setIsGroupSending] = useState(false)

  const weekIdx = Math.max(0, currentWeek - 1)

  const getStudentMark = (s: LocalStudentProfile) => {
    const weekDay = currentWeek * 7
    const due = (s.assessments ?? []).filter((a) => a.date_due != null && a.date_due <= weekDay)
    if (due.length === 0) return null
    const scored = due.filter((a) => a.score != null)
    if (scored.length === 0) return null
    const totalWeight = scored.reduce((sum, a) => sum + (a.weight ?? 1), 0)
    const weightedSum = scored.reduce((sum, a) => sum + a.score! * (a.weight ?? 1), 0)
    return totalWeight > 0 ? Math.round(weightedSum / totalWeight) : null
  }

  const sorted = useMemo(() => {
    const filtered = students.filter((s) => {
      // 1. Search text filter
      if (debouncedSearch) {
        const searchLower = debouncedSearch.toLowerCase().trim()
        const studentIdStr = String(s.id_student ?? '')
        const imdStr = s.imd_band ? String(s.imd_band).toLowerCase() : ''
        const nameStr = s.name ? String(s.name).toLowerCase() : ''
        
        const matchSearch = (
          studentIdStr.toLowerCase().includes(searchLower) || 
          imdStr.includes(searchLower) ||
          nameStr.includes(searchLower)
        )
        if (!matchSearch) return false
      }

      // 2. Risk Tier Filter
      const tier = (s.tier_by_week[weekIdx] ?? 1) as TierNumber
      if (tierFilter !== 'all' && String(tier) !== tierFilter) {
        return false
      }

      // 3. Mark/Score Filter
      if (scoreFilter !== 'all') {
        const mark = getStudentMark(s)
        if (mark === null) {
          // If no mark yet, check risk score as proxy
          const rScore = s.risk_by_week[weekIdx] ?? 0.3
          const estMark = (1.0 - rScore) * 100
          if (scoreFilter === 'high' && estMark < 80) return false
          if (scoreFilter === 'good' && (estMark < 65 || estMark >= 80)) return false
          if (scoreFilter === 'average' && (estMark < 50 || estMark >= 65)) return false
          if (scoreFilter === 'low' && estMark >= 50) return false
        } else {
          if (scoreFilter === 'high' && mark < 80) return false
          if (scoreFilter === 'good' && (mark < 65 || mark >= 80)) return false
          if (scoreFilter === 'average' && (mark < 50 || mark >= 65)) return false
          if (scoreFilter === 'low' && mark >= 50) return false
        }
      }

      return true
    })

    return [...filtered].sort((a, b) => {
      if (sortField === 'name') {
        const nameA = a.name || ''
        const nameB = b.name || ''
        return sortDir === 'desc' ? nameB.localeCompare(nameA) : nameA.localeCompare(nameB)
      }

      let va = 0, vb = 0
      if (sortField === 'risk') { va = a.risk_by_week[weekIdx] ?? 0; vb = b.risk_by_week[weekIdx] ?? 0 }
      else if (sortField === 'id') { va = a.id_student; vb = b.id_student }
      else if (sortField === 'imd') { va = a.imd_band.charCodeAt(0); vb = b.imd_band.charCodeAt(0) }
      
      return sortDir === 'desc' ? vb - va : va - vb
    })
  }, [students, sortField, sortDir, weekIdx, search, tierFilter, scoreFilter])

  const visibleStudents = useMemo(() => {
    return sorted.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
  }, [sorted, page, rowsPerPage])

  const handleSort = (field: typeof sortField) => {
    if (sortField === field) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    else { setSortField(field); setSortDir('desc') }
  }

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage)
  }

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10))
    setPage(0)
  }

  // --- Handlers for Warning Action ---
  const handleOpenWarning = (e: React.MouseEvent, student: LocalStudentProfile) => {
    e.stopPropagation()
    setWarningStudent(student)
    
    const studentName = student.name || `Student #${student.id_student}`
    setWarningMessage(
      `Dear ${studentName},\n\n` +
      `Our records show a recent drop in your academic engagement. ` +
      `We want to ensure you have the support you need to succeed. ` +
      `Please reach out to your academic advisor as soon as possible to discuss how we can help you stay on track.\n\n` +
      `Best regards,\nAcademic Support Team`
    )
  }

  const handleCloseWarning = () => {
    setWarningStudent(null)
    setWarningMessage('')
  }

  const handleSendWarning = async () => {
    if (!warningStudent) return
    setIsSending(true)
    
    try {
      const studentName = warningStudent.name || `Student #${warningStudent.id_student}`
      const courseCode = module && presentation ? `${module} ${presentation}` : (module || undefined)

      const res = await fetch(`${BASE_URL}/notify/broadcast`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_ids: [warningStudent.id_student],
          type: 'academic_warning',
          title: `Academic Warning for ${studentName}`,
          content: warningMessage,
          sender_role: 'instructor',
          course_code: courseCode,
        })
      })

      if (!res.ok) {
        const errorText = await res.text()
        throw new Error(`Failed to send: ${res.status} - ${errorText}`)
      }
      
      handleCloseWarning()
    } catch (error) {
      console.error(error)
      alert("There was an error sending the warning. Please try again.")
    } finally {
      setIsSending(false)
    }
  }

  // --- Handlers for Group Broadcast Action ---
  const [broadcastTarget, setBroadcastTarget] = useState<'filtered' | 'tier3' | 'tier2' | 'tier1' | 'all'>('filtered')

  const targetStudents = useMemo(() => {
    if (broadcastTarget === 'tier3') return students.filter(s => (s.tier_by_week[weekIdx] ?? 1) === 3)
    if (broadcastTarget === 'tier2') return students.filter(s => (s.tier_by_week[weekIdx] ?? 1) === 2)
    if (broadcastTarget === 'tier1') return students.filter(s => (s.tier_by_week[weekIdx] ?? 1) === 1)
    if (broadcastTarget === 'all') return students
    return sorted
  }, [broadcastTarget, students, sorted, weekIdx])

  const applyTemplate = (tpl: 'tier3' | 'tier2' | 'tier1' | 'general') => {
    if (tpl === 'tier3') {
      setBroadcastTarget('tier3')
      setGroupBroadcastType('academic_warning')
      setGroupBroadcastTitle('[ACADEMIC WARNING] Performance Improvement & Support Guidance')
      setGroupBroadcastContent(
        `Dear student,\n\n` +
        `Our academic tracking system indicates that your current progress and activity in this course may put your outcome at risk. ` +
        `The Teaching Team strongly recommends completing any pending coursework and scheduling a consultation with your Instructor or Academic Advisor this week for personalized guidance.\n\n` +
        `Best regards,\nCourse Teaching Team`
      )
    } else if (tpl === 'tier2') {
      setBroadcastTarget('tier2')
      setGroupBroadcastType('study_reminder')
      setGroupBroadcastTitle('[STUDY REMINDER] Coursework Deadlines & Review Schedule')
      setGroupBroadcastContent(
        `Dear student,\n\n` +
        `Please make sure to check the upcoming assessment deadlines and review the core lecture concepts. ` +
        `If you need help with any exercises or topics, please post in the Discussion forum or contact a teaching assistant.\n\n` +
        `Best of luck!`
      )
    } else if (tpl === 'tier1') {
      setBroadcastTarget('tier1')
      setGroupBroadcastType('general_notice')
      setGroupBroadcastTitle('[COMMENDATION] Outstanding Performance & Advanced Resources')
      setGroupBroadcastContent(
        `Dear student,\n\n` +
        `The Teaching Team commends your active engagement and excellent results in recent weeks. ` +
        `Supplementary advanced reading materials and enrichment exercises have been published on the course portal for your continued exploration.\n\n` +
        `Keep up the great work!`
      )
    } else {
      setBroadcastTarget('all')
      setGroupBroadcastType('general_notice')
      setGroupBroadcastTitle('Course Announcement & Academic Schedule Update')
      setGroupBroadcastContent(
        `Dear students,\n\n` +
        `Please review the updated study schedule and new learning resources available on the portal. ` +
        `Remember to submit all assignments on time and actively take part in discussions.\n\n` +
        `Best regards,\nCourse Teaching Team`
      )
    }
  }

  const handleOpenGroupBroadcast = (initialTier?: '1' | '2' | '3') => {
    if (initialTier === '3' || tierFilter === '3') {
      applyTemplate('tier3')
    } else if (initialTier === '2' || tierFilter === '2') {
      applyTemplate('tier2')
    } else if (initialTier === '1' || tierFilter === '1') {
      applyTemplate('tier1')
    } else {
      const filterLabel = tierFilter !== 'all' ? `Tier ${tierFilter}` : (scoreFilter !== 'all' ? `score group ${scoreFilter}` : 'filtered cohort')
      setBroadcastTarget('filtered')
      setGroupBroadcastType('general_notice')
      setGroupBroadcastTitle(`Important Course Notice [${filterLabel.toUpperCase()}]`)
      setGroupBroadcastContent(
        `Dear students,\n\n` +
        `The instructor has posted a study update and guidance for ${filterLabel}.\n` +
        `Please complete your upcoming assessments on time and contact teaching assistants if you need any assistance!\n\n` +
        `Best regards,\nCourse Teaching Team`
      )
    }
    setGroupBroadcastOpen(true)
  }

  const handleSendGroupBroadcast = async () => {
    if (targetStudents.length === 0) return
    setIsGroupSending(true)
    try {
      const targetStudentIds = targetStudents.map(s => s.id_student)
      const courseCode = module && presentation ? `${module} ${presentation}` : (module || undefined)

      const res = await fetch(`${BASE_URL}/notify/broadcast`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_ids: targetStudentIds,
          type: groupBroadcastType,
          title: groupBroadcastTitle,
          content: groupBroadcastContent,
          sender_role: 'instructor',
          course_code: courseCode,
        })
      })

      if (!res.ok) throw new Error('Failed to broadcast message to group')
      setGroupBroadcastOpen(false)
      alert(`Successfully sent broadcast to ${targetStudentIds.length} students!`)
    } catch (err: any) {
      alert(err.message || 'Error sending group broadcast')
    } finally {
      setIsGroupSending(false)
    }
  }

  const TrendIcon = ({ s }: { s: LocalStudentProfile }) => {
    const t = riskTrend(s, currentWeek)
    if (t === 'up') return <TrendingUpIcon sx={{ fontSize: 14, color: tokens.brand.danger }} />
    if (t === 'down') return <TrendingDownIcon sx={{ fontSize: 14, color: tokens.brand.primaryLight }} />
    return <RemoveIcon sx={{ fontSize: 14, color: tokens.text.muted }} />
  }

  return (
    <Box className="dashboard-section-card" sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
      {/* ── Top Header & Actions ── */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 1.5 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography sx={{ fontSize: 13, fontWeight: 700, color: 'text.primary' }}>
            STUDENTS ENROLLED — WEEK {currentWeek}
          </Typography>
          <Chip label={`${sorted.length} students`} size="small" sx={{ fontSize: 11, fontWeight: 600, height: 20, bgcolor: tokens.surface.subtle }} />
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Button
            size="small"
            variant="outlined"
            onClick={() => handleOpenGroupBroadcast()}
            disabled={sorted.length === 0}
            sx={{ fontSize: 11, fontWeight: 600, textTransform: 'none', color: tokens.brand.primary, borderColor: tokens.brand.primaryMuted }}
          >
            📢 Broadcast to Group ({sorted.length})
          </Button>

          <TextField
            size="small"
            placeholder="Search by ID, Name, IMD..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(0); }}
            InputProps={{
              startAdornment: <InputAdornment position="start"><SearchIcon sx={{ fontSize: 16, color: 'text.muted' }} /></InputAdornment>,
              sx: { fontSize: 12, fontFamily: tokens.font.mono, borderRadius: 1.5, height: 32 },
            }}
            sx={{ width: 220 }}
          />
        </Box>
      </Box>

      {/* ── Filters Row: Risk Tier & Mark Filters ── */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap', bgcolor: tokens.surface.subtle, p: 1, borderRadius: 1.5 }}>
        <Typography variant="caption" sx={{ color: tokens.text.secondary, fontWeight: 600, mr: 0.5 }}>
          Risk Tier:
        </Typography>
        <Chip
          label="All"
          size="small"
          onClick={() => { setTierFilter('all'); setPage(0); }}
          color={tierFilter === 'all' ? 'primary' : 'default'}
          variant={tierFilter === 'all' ? 'filled' : 'outlined'}
          sx={{ height: 22, fontSize: 10, fontWeight: 600 }}
        />
        <Chip
          label="Tier 1 (Low)"
          size="small"
          onClick={() => { setTierFilter('1'); setPage(0); }}
          color={tierFilter === '1' ? 'success' : 'default'}
          variant={tierFilter === '1' ? 'filled' : 'outlined'}
          sx={{ height: 22, fontSize: 10, fontWeight: 600 }}
        />
        <Chip
          label="Tier 2 (Moderate)"
          size="small"
          onClick={() => { setTierFilter('2'); setPage(0); }}
          color={tierFilter === '2' ? 'warning' : 'default'}
          variant={tierFilter === '2' ? 'filled' : 'outlined'}
          sx={{ height: 22, fontSize: 10, fontWeight: 600 }}
        />
        <Chip
          label="Tier 3 (High)"
          size="small"
          onClick={() => { setTierFilter('3'); setPage(0); }}
          color={tierFilter === '3' ? 'error' : 'default'}
          variant={tierFilter === '3' ? 'filled' : 'outlined'}
          sx={{ height: 22, fontSize: 10, fontWeight: 600 }}
        />

        <Box sx={{ width: 1, height: 16, bgcolor: tokens.border.default, mx: 0.5 }} />

        <Typography variant="caption" sx={{ color: tokens.text.secondary, fontWeight: 600, mr: 0.5 }}>
          Marks Filter:
        </Typography>
        <Chip
          label="All Scores"
          size="small"
          onClick={() => { setScoreFilter('all'); setPage(0); }}
          color={scoreFilter === 'all' ? 'primary' : 'default'}
          variant={scoreFilter === 'all' ? 'filled' : 'outlined'}
          sx={{ height: 22, fontSize: 10, fontWeight: 600 }}
        />
        <Chip
          label=">= 80 (High)"
          size="small"
          onClick={() => { setScoreFilter('high'); setPage(0); }}
          color={scoreFilter === 'high' ? 'success' : 'default'}
          variant={scoreFilter === 'high' ? 'filled' : 'outlined'}
          sx={{ height: 22, fontSize: 10, fontWeight: 600 }}
        />
        <Chip
          label="65–79 (Good)"
          size="small"
          onClick={() => { setScoreFilter('good'); setPage(0); }}
          color={scoreFilter === 'good' ? 'info' : 'default'}
          variant={scoreFilter === 'good' ? 'filled' : 'outlined'}
          sx={{ height: 22, fontSize: 10, fontWeight: 600 }}
        />
        <Chip
          label="50–64 (Average)"
          size="small"
          onClick={() => { setScoreFilter('average'); setPage(0); }}
          color={scoreFilter === 'average' ? 'warning' : 'default'}
          variant={scoreFilter === 'average' ? 'filled' : 'outlined'}
          sx={{ height: 22, fontSize: 10, fontWeight: 600 }}
        />
        <Chip
          label="< 50 (Low)"
          size="small"
          onClick={() => { setScoreFilter('low'); setPage(0); }}
          color={scoreFilter === 'low' ? 'error' : 'default'}
          variant={scoreFilter === 'low' ? 'filled' : 'outlined'}
          sx={{ height: 22, fontSize: 10, fontWeight: 600 }}
        />
      </Box>

      <TableContainer sx={{ flex: 1, maxHeight: 600 }}>
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              {[
                { id: 'id', label: 'Student ID' },
                { id: 'name', label: 'Student Name' },
                { id: 'imd', label: 'IMD band' },
                { id: null, label: 'Age' },
                { id: null, label: 'Att.' },
                { id: 'risk', label: 'Risk score' },
                { id: null, label: 'Tier' },
                { id: null, label: 'Trend' },
                { id: null, label: 'Actions' },
              ].map((col, idx) => (
                <TableCell
                  key={col.label + idx}
                  sx={{ bgcolor: tokens.surface.raised, fontFamily: tokens.font.mono, fontSize: 11, color: tokens.text.secondary, fontWeight: 600, py: 1.5 }}
                >
                  {col.id ? (
                    <TableSortLabel
                      active={sortField === col.id}
                      direction={sortField === col.id ? sortDir : 'asc'}
                      onClick={() => handleSort(col.id as typeof sortField)}
                      sx={{ fontSize: 11, color: '#6B7280 !important' }}
                    >
                      {col.label}
                    </TableSortLabel>
                  ) : col.label}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {visibleStudents.map((s) => {
              const risk = s.risk_by_week[weekIdx] ?? 0
              const tier = (s.tier_by_week[weekIdx] ?? 1) as TierNumber
              const tc = TIER_COLORS[tier]
              const selected = s.id_student === selectedId
              const withdrawn = s.final_result === 'Withdrawn'
              const studentName = s.name || `Student #${s.id_student}`

              return (
                <TableRow
                  key={s.id_student}
                  onClick={() => onSelect(s)}
                  sx={{
                    cursor: 'pointer',
                    opacity: withdrawn ? 0.55 : 1,
                    bgcolor: selected ? tokens.surface.selected : 'transparent',
                    '&:hover': { bgcolor: tokens.surface.raised },
                    borderLeft: selected ? '3px solid #1D9E75' : '3px solid transparent',
                  }}
                >
                  <TableCell sx={{ fontFamily: tokens.font.mono, fontSize: 12, color: tokens.text.primary }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                      #{s.id_student}
                      {withdrawn && <Chip label="W" size="small" sx={{ fontSize: 9, height: 16, bgcolor: tokens.surface.neutral }} />}
                    </Box>
                  </TableCell>
                  <TableCell sx={{ fontSize: 12, color: tokens.text.primary, whiteSpace: 'nowrap' }}>
                    {studentName}
                  </TableCell>
                  <TableCell sx={{ fontFamily: tokens.font.mono, fontSize: 11, color: tokens.text.secondary }}>{s.imd_band}</TableCell>
                  <TableCell sx={{ fontFamily: tokens.font.mono, fontSize: 11, color: tokens.text.secondary }}>{s.age_band}</TableCell>
                  <TableCell sx={{ fontFamily: tokens.font.mono, fontSize: 11, color: tokens.text.secondary, textAlign: 'center' }}>{s.num_of_prev_attempts}</TableCell>
                  <TableCell sx={{ minWidth: 120 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <LinearProgress
                        variant="determinate"
                        value={risk * 100}
                        sx={{
                          flex: 1, height: 6, borderRadius: 3, bgcolor: tokens.surface.subtle,
                          '& .MuiLinearProgress-bar': {
                            bgcolor: risk < 0.33 ? TIER_COLORS[1].solid : risk < 0.66 ? TIER_COLORS[2].solid : TIER_COLORS[3].solid,
                            borderRadius: 3,
                          },
                        }}
                      />
                      <Typography sx={{ fontSize: 11, fontFamily: tokens.font.mono, minWidth: 32 }}>{(risk * 100).toFixed(0)}%</Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip label={tc.label} size="small" sx={{ bgcolor: tc.subtle, color: tc.text, fontSize: 10, height: 18 }} />
                  </TableCell>
                  <TableCell><TrendIcon s={s} /></TableCell>
                  
                  <TableCell>
                    {tier === 3 && !withdrawn && (
                      <Button
                        size="small"
                        variant="outlined"
                        color="error"
                        onClick={(e) => handleOpenWarning(e, s)}
                        sx={{ fontSize: 10, textTransform: 'none', py: 0.25 }}
                      >
                        Notify
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </TableContainer>
      
      <TablePagination
        rowsPerPageOptions={[10, 25, 50]}
        component="div"
        count={sorted.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />

      <Dialog 
        open={Boolean(warningStudent)} 
        onClose={handleCloseWarning}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ fontSize: 16, fontWeight: 700 }}>
          Send Academic Warning
        </DialogTitle>
        <DialogContent dividers>
          <Typography sx={{ fontSize: 13, mb: 2, color: 'text.secondary' }}>
            Sending to: <strong>{warningStudent?.name || `Student #${warningStudent?.id_student}`}</strong>
          </Typography>
          <TextField
            fullWidth
            multiline
            rows={8}
            variant="outlined"
            value={warningMessage}
            onChange={(e) => setWarningMessage(e.target.value)}
            sx={{
              '& .MuiInputBase-root': { fontSize: 13, fontFamily: 'sans-serif' }
            }}
          />
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button 
            onClick={handleCloseWarning} 
            color="inherit" 
            disabled={isSending}
            sx={{ textTransform: 'none', fontSize: 13 }}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleSendWarning} 
            color="error" 
            variant="contained"
            disabled={isSending || !warningMessage.trim()}
            startIcon={isSending ? <CircularProgress size={16} color="inherit" /> : null}
            sx={{ textTransform: 'none', fontSize: 13, boxShadow: 'none' }}
          >
            {isSending ? 'Sending...' : 'Send Warning'}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog
        open={groupBroadcastOpen}
        onClose={() => setGroupBroadcastOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ fontSize: 16, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span>📢 Broadcast to Group ({targetStudents.length} Students)</span>
          <Chip
            label={`${targetStudents.length} recipients`}
            size="small"
            color={broadcastTarget === 'tier3' ? 'error' : broadcastTarget === 'tier2' ? 'warning' : 'primary'}
            sx={{ fontWeight: 600, fontSize: 11 }}
          />
        </DialogTitle>
        <DialogContent dividers sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Box>
            <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600, display: 'block', mb: 0.75 }}>
              1. SELECT TARGET STUDENT GROUP:
            </Typography>
            <Box sx={{ display: 'flex', gap: 0.75, flexWrap: 'wrap' }}>
              <Chip
                label={`Filtered Selection (${sorted.length})`}
                size="small"
                onClick={() => setBroadcastTarget('filtered')}
                color={broadcastTarget === 'filtered' ? 'primary' : 'default'}
                variant={broadcastTarget === 'filtered' ? 'filled' : 'outlined'}
                sx={{ fontSize: 11, fontWeight: 600 }}
              />
              <Chip
                label="Tier 3 (High Risk)"
                size="small"
                onClick={() => applyTemplate('tier3')}
                color={broadcastTarget === 'tier3' ? 'error' : 'default'}
                variant={broadcastTarget === 'tier3' ? 'filled' : 'outlined'}
                sx={{ fontSize: 11, fontWeight: 600 }}
              />
              <Chip
                label="Tier 2 (Moderate)"
                size="small"
                onClick={() => applyTemplate('tier2')}
                color={broadcastTarget === 'tier2' ? 'warning' : 'default'}
                variant={broadcastTarget === 'tier2' ? 'filled' : 'outlined'}
                sx={{ fontSize: 11, fontWeight: 600 }}
              />
              <Chip
                label="Tier 1 (Low Risk)"
                size="small"
                onClick={() => applyTemplate('tier1')}
                color={broadcastTarget === 'tier1' ? 'success' : 'default'}
                variant={broadcastTarget === 'tier1' ? 'filled' : 'outlined'}
                sx={{ fontSize: 11, fontWeight: 600 }}
              />
              <Chip
                label={`Entire Cohort (${students.length})`}
                size="small"
                onClick={() => applyTemplate('general')}
                color={broadcastTarget === 'all' ? 'info' : 'default'}
                variant={broadcastTarget === 'all' ? 'filled' : 'outlined'}
                sx={{ fontSize: 11, fontWeight: 600 }}
              />
            </Box>
          </Box>

          <Box>
            <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600, display: 'block', mb: 0.75 }}>
              2. QUICK MESSAGE TEMPLATES:
            </Typography>
            <Box sx={{ display: 'flex', gap: 0.75, flexWrap: 'wrap' }}>
              <Button size="small" variant="outlined" color="error" onClick={() => applyTemplate('tier3')} sx={{ fontSize: 10, textTransform: 'none', py: 0.25 }}>
                ⚠️ Tier 3 Warning
              </Button>
              <Button size="small" variant="outlined" color="warning" onClick={() => applyTemplate('tier2')} sx={{ fontSize: 10, textTransform: 'none', py: 0.25 }}>
                📌 Tier 2 Reminder
              </Button>
              <Button size="small" variant="outlined" color="success" onClick={() => applyTemplate('tier1')} sx={{ fontSize: 10, textTransform: 'none', py: 0.25 }}>
                🌟 Tier 1 Commendation
              </Button>
              <Button size="small" variant="outlined" color="inherit" onClick={() => applyTemplate('general')} sx={{ fontSize: 10, textTransform: 'none', py: 0.25 }}>
                📢 General Announcement
              </Button>
            </Box>
          </Box>

          <TextField
            fullWidth
            size="small"
            label="Announcement Title"
            value={groupBroadcastTitle}
            onChange={(e) => setGroupBroadcastTitle(e.target.value)}
          />
          <TextField
            fullWidth
            multiline
            rows={5}
            label="Detailed Content"
            value={groupBroadcastContent}
            onChange={(e) => setGroupBroadcastContent(e.target.value)}
          />
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button
            onClick={() => setGroupBroadcastOpen(false)}
            color="inherit"
            disabled={isGroupSending}
            sx={{ textTransform: 'none' }}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSendGroupBroadcast}
            variant="contained"
            color="primary"
            disabled={isGroupSending || !groupBroadcastTitle.trim() || !groupBroadcastContent.trim() || targetStudents.length === 0}
            startIcon={isGroupSending ? <CircularProgress size={16} color="inherit" /> : null}
            sx={{ textTransform: 'none', fontWeight: 600 }}
          >
            {isGroupSending ? 'Sending...' : `Send to ${targetStudents.length} Students`}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
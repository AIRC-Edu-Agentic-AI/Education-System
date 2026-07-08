import { useState, useMemo } from 'react'
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
}

function riskTrend(s: LocalStudentProfile, week: number): 'up' | 'down' | 'flat' {
  const wi = week - 1
  if (wi < 2) return 'flat'
  const delta = (s.risk_by_week[wi] ?? 0) - (s.risk_by_week[wi - 2] ?? 0)
  if (delta > 0.05) return 'up'
  if (delta < -0.05) return 'down'
  return 'flat'
}

export function StudentRiskTable({ students, currentWeek, onSelect, selectedId }: Props) {
  const [sortField, setSortField] = useState<'risk' | 'id' | 'imd' | 'name'>('risk')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [search, setSearch] = useState('')
  
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(10)

  // --- Dialog & API States ---
  const [warningStudent, setWarningStudent] = useState<LocalStudentProfile | null>(null)
  const [warningMessage, setWarningMessage] = useState('')
  const [isSending, setIsSending] = useState(false)

  const weekIdx = Math.max(0, currentWeek - 1)

  const sorted = useMemo(() => {
    const filtered = students.filter((s) => {
      if (!search) return true
      const searchLower = search.toLowerCase()
      return (
        String(s.id_student).includes(searchLower) || 
        s.imd_band.toLowerCase().includes(searchLower) ||
        (s.name && s.name.toLowerCase().includes(searchLower))
      )
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
  }, [students, sortField, sortDir, weekIdx, search])

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
    e.stopPropagation() // Prevent triggering the row's onSelect
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
      
      // Sửa URL trỏ đến backend port 8000 và thay đổi payload cho khớp định dạng DB
      const res = await fetch('http://localhost:8000/api/notifications', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          senderRole: 'Instructor',
          receiverRole: 'Student',
          type: 'Academic Warning',
          title: `Academic Warning for ${studentName}`,
          content: warningMessage,
          student_id: warningStudent.id_student // Vẫn gửi kèm id sinh viên nếu backend cần xử lý riêng
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

  const TrendIcon = ({ s }: { s: LocalStudentProfile }) => {
    const t = riskTrend(s, currentWeek)
    if (t === 'up') return <TrendingUpIcon sx={{ fontSize: 14, color: tokens.brand.danger }} />
    if (t === 'down') return <TrendingDownIcon sx={{ fontSize: 14, color: tokens.brand.primaryLight }} />
    return <RemoveIcon sx={{ fontSize: 14, color: tokens.text.muted }} />
  }

  return (
    <Box className="dashboard-section-card" sx={{ display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Typography sx={{ fontSize: 13, fontWeight: 700, color: 'text.primary' }}>
          STUDENTS ENROLLED — WEEK {currentWeek}
        </Typography>
        <TextField
          size="small"
          placeholder="Search by ID, Name or IMD..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(0); }}
          InputProps={{
            startAdornment: <InputAdornment position="start"><SearchIcon sx={{ fontSize: 16, color: 'text.muted' }} /></InputAdornment>,
            sx: { fontSize: 12, fontFamily: tokens.font.mono, borderRadius: 1.5 },
          }}
          sx={{ width: 260 }}
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
                { id: null, label: 'Actions' }, // <--- Cột mới
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
                  
                  {/* --- Ô chứa nút Action --- */}
                  <TableCell>
                    {tier === 3 && !withdrawn && (
                      <Button
                        size="small"
                        variant="outlined"
                        color="error"
                        onClick={(e) => handleOpenWarning(e, s)}
                        sx={{ fontSize: 10, textTransform: 'none', py: 0.25 }}
                      >
                        Send Warning
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

      {/* --- Dialog Soạn Tin Nhắn Cảnh Báo --- */}
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
    </Box>
  )
}
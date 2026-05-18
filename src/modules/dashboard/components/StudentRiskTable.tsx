import { useState, useMemo } from 'react'
import {
  Typography, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, TableSortLabel, Chip, Box, TextField, InputAdornment,
  LinearProgress, TablePagination
} from '@mui/material'
import SearchIcon from '@mui/icons-material/SearchRounded'
import TrendingUpIcon from '@mui/icons-material/TrendingUpRounded'
import TrendingDownIcon from '@mui/icons-material/TrendingDownRounded'
import RemoveIcon from '@mui/icons-material/RemoveRounded'
import type { StudentProfile, Tier } from '../../../types/domain'

interface Props {
  students: StudentProfile[]
  currentWeek: number
  onSelect: (s: StudentProfile) => void
  selectedId: number | null
}

const TIER_COLORS: Record<Tier, { bg: string; text: string; label: string }> = {
  1: { bg: '#E1F5EE', text: '#0F6E56', label: 'Tier 1' },
  2: { bg: '#FAEEDA', text: '#854F0B', label: 'Tier 2' },
  3: { bg: '#FCEBEB', text: '#A32D2D', label: 'Tier 3' },
}

function riskTrend(s: StudentProfile, week: number): 'up' | 'down' | 'flat' {
  const wi = week - 1
  if (wi < 2) return 'flat'
  const delta = (s.risk_by_week[wi] ?? 0) - (s.risk_by_week[wi - 2] ?? 0)
  if (delta > 0.05) return 'up'
  if (delta < -0.05) return 'down'
  return 'flat'
}

export function StudentRiskTable({ students, currentWeek, onSelect, selectedId }: Props) {
  const [sortField, setSortField] = useState<'risk' | 'id' | 'imd'>('risk')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [search, setSearch] = useState('')
  
  // Pagination State
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(10)

  const weekIdx = Math.max(0, currentWeek - 1)

  const sorted = useMemo(() => {
    const filtered = students.filter((s) =>
      search ? String(s.id_student).includes(search) || s.imd_band.toLowerCase().includes(search.toLowerCase()) : true
    )
    return [...filtered].sort((a, b) => {
      let va = 0, vb = 0
      if (sortField === 'risk') { va = a.risk_by_week[weekIdx] ?? 0; vb = b.risk_by_week[weekIdx] ?? 0 }
      else if (sortField === 'id') { va = a.id_student; vb = b.id_student }
      else if (sortField === 'imd') { va = a.imd_band.charCodeAt(0); vb = b.imd_band.charCodeAt(0) }
      return sortDir === 'desc' ? vb - va : va - vb
    })
  }, [students, sortField, sortDir, weekIdx, search])

  // Get current page of students
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

  const TrendIcon = ({ s }: { s: StudentProfile }) => {
    const t = riskTrend(s, currentWeek)
    if (t === 'up') return <TrendingUpIcon sx={{ fontSize: 14, color: '#E24B4A' }} />
    if (t === 'down') return <TrendingDownIcon sx={{ fontSize: 14, color: '#1D9E75' }} />
    return <RemoveIcon sx={{ fontSize: 14, color: '#9CA3AF' }} />
  }

  return (
    <Box className="dashboard-section-card" sx={{ display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Typography sx={{ fontSize: 13, fontWeight: 700, color: '#0A1628', fontFamily: '"IBM Plex Sans", sans-serif' }}>
          STUDENTS ENROLLED — WEEK {currentWeek}
        </Typography>
        <TextField
          size="small"
          placeholder="Search by ID or IMD..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(0); }}
          InputProps={{
            startAdornment: <InputAdornment position="start"><SearchIcon sx={{ fontSize: 16, color: '#9CA3AF' }} /></InputAdornment>,
            sx: { fontSize: 12, fontFamily: '"IBM Plex Mono", monospace', borderRadius: 1.5 },
          }}
          sx={{ width: 240 }}
        />
      </Box>

      <TableContainer sx={{ flex: 1, maxHeight: 600 }}>
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              {[
                { id: 'id', label: 'Student ID' },
                { id: 'imd', label: 'IMD band' },
                { id: null, label: 'Age' },
                { id: null, label: 'Att.' },
                { id: 'risk', label: 'Risk score' },
                { id: null, label: 'Tier' },
                { id: null, label: 'Trend' },
              ].map((col) => (
                <TableCell
                  key={col.label}
                  sx={{ bgcolor: '#F8F7F4', fontFamily: '"IBM Plex Mono", monospace', fontSize: 11, color: '#6B7280', fontWeight: 600, py: 1.5 }}
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
              const tier = (s.tier_by_week[weekIdx] ?? 1) as Tier
              const tc = TIER_COLORS[tier]
              const selected = s.id_student === selectedId
              const withdrawn = s.final_result === 'Withdrawn'

              return (
                <TableRow
                  key={s.id_student}
                  onClick={() => onSelect(s)}
                  sx={{
                    cursor: 'pointer',
                    opacity: withdrawn ? 0.55 : 1,
                    bgcolor: selected ? '#F0FDF8' : 'transparent',
                    '&:hover': { bgcolor: '#F8F7F4' },
                    borderLeft: selected ? '3px solid #1D9E75' : '3px solid transparent',
                  }}
                >
                  <TableCell sx={{ fontFamily: '"IBM Plex Mono", monospace', fontSize: 12, color: '#0A1628' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                      #{s.id_student}
                      {withdrawn && <Chip label="W" size="small" sx={{ fontSize: 9, height: 16, bgcolor: '#F3F4F6' }} />}
                    </Box>
                  </TableCell>
                  <TableCell sx={{ fontFamily: '"IBM Plex Mono", monospace', fontSize: 11, color: '#6B7280' }}>{s.imd_band}</TableCell>
                  <TableCell sx={{ fontFamily: '"IBM Plex Mono", monospace', fontSize: 11, color: '#6B7280' }}>{s.age_band}</TableCell>
                  <TableCell sx={{ fontFamily: '"IBM Plex Mono", monospace', fontSize: 11, color: '#6B7280', textAlign: 'center' }}>{s.num_of_prev_attempts}</TableCell>
                  <TableCell sx={{ minWidth: 120 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <LinearProgress
                        variant="determinate"
                        value={risk * 100}
                        sx={{
                          flex: 1, height: 6, borderRadius: 3, bgcolor: '#F0EFE9',
                          '& .MuiLinearProgress-bar': {
                            bgcolor: risk < 0.33 ? '#1D9E75' : risk < 0.66 ? '#EF9F27' : '#E24B4A',
                            borderRadius: 3,
                          },
                        }}
                      />
                      <Typography sx={{ fontSize: 11, fontFamily: '"IBM Plex Mono", monospace', minWidth: 32 }}>{(risk * 100).toFixed(0)}%</Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip label={tc.label} size="small" sx={{ bgcolor: tc.bg, color: tc.text, fontSize: 10, height: 18, fontFamily: '"IBM Plex Mono", monospace' }} />
                  </TableCell>
                  <TableCell><TrendIcon s={s} /></TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </TableContainer>
      
      {/* Dynamic pagination controls */}
      <TablePagination
        rowsPerPageOptions={[10, 25, 50]}
        component="div"
        count={sorted.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />
    </Box>
  )
}
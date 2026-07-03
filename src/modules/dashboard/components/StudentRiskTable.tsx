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
import { TIER_COLORS, type TierNumber } from '../../../shared/constants/tiers'
import { tokens } from '../../../theme'
import type { StudentProfile } from '../../../types/domain'

interface Props {
  students: StudentProfile[]
  currentWeek: number
  onSelect: (s: StudentProfile) => void
  selectedId: number | null
}

const LAST_NAMES = ['Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Huỳnh', 'Phan', 'Vũ', 'Võ', 'Đặng', 'Bùi', 'Đỗ', 'Hồ', 'Ngô', 'Dương', 'Lý', 'Đinh', 'Trịnh', 'Tô', 'Đoàn']

const MIDDLE_NAMES_MALE = ['Văn', 'Hữu', 'Đức', 'Minh', 'Quốc', 'Trung', 'Anh', 'Thanh', 'Quang', 'Tuấn']
const MIDDLE_NAMES_FEMALE = ['Thị', 'Ngọc', 'Thu', 'Phương', 'Lan', 'Mai', 'Hương', 'Bích', 'Kim', 'Thùy']

const FIRST_NAMES_MALE = ['An', 'Bình', 'Cường', 'Dũng', 'Hùng', 'Khoa', 'Long', 'Mạnh', 'Nam', 'Phúc', 'Quân', 'Sơn', 'Tài', 'Thắng', 'Tiến', 'Toàn', 'Trí', 'Tuấn', 'Việt', 'Vũ']
const FIRST_NAMES_FEMALE = ['An', 'Ánh', 'Chi', 'Dung', 'Hà', 'Hoa', 'Hồng', 'Hương', 'Lan', 'Linh', 'Mai', 'My', 'Nga', 'Ngọc', 'Nhung', 'Phương', 'Trang', 'Trinh', 'Uyên', 'Vân']

function hashId(id: number): number {
  let h = id ^ 0xdeadbeef
  h = Math.imul(h ^ (h >>> 16), 0x45d9f3b)
  h = Math.imul(h ^ (h >>> 16), 0x45d9f3b)
  return Math.abs(h ^ (h >>> 16))
}

function generateName(id: number, gender: string): string {
  const h = hashId(id)
  const isMale = gender === 'M'
  const lastName = LAST_NAMES[h % LAST_NAMES.length]
  const midNames = isMale ? MIDDLE_NAMES_MALE : MIDDLE_NAMES_FEMALE
  const firstNames = isMale ? FIRST_NAMES_MALE : FIRST_NAMES_FEMALE
  const middleName = midNames[(h >> 4) % midNames.length]
  const firstName = firstNames[(h >> 8) % firstNames.length]
  return `${lastName} ${middleName} ${firstName}`
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

  const visibleStudents = useMemo(() => {
    return sorted.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
  }, [sorted, page, rowsPerPage])

  const handleSort = (field: typeof sortField) => {
    if (sortField === field) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    else { setSortField(field); setSortDir('desc') }
  }

  const handleChangePage = (_: unknown, newPage: number) => setPage(newPage)

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10))
    setPage(0)
  }

  const TrendIcon = ({ s }: { s: StudentProfile }) => {
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
          placeholder="Search by ID or IMD..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(0) }}
          InputProps={{
            startAdornment: <InputAdornment position="start"><SearchIcon sx={{ fontSize: 16, color: 'text.muted' }} /></InputAdornment>,
            sx: { fontSize: 12, fontFamily: tokens.font.mono, borderRadius: 1.5 },
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
                { id: null, label: 'Student Name' },
                { id: 'imd', label: 'IMD band' },
                { id: null, label: 'Age' },
                { id: null, label: 'Att.' },
                { id: 'risk', label: 'Risk score' },
                { id: null, label: 'Tier' },
                { id: null, label: 'Trend' },
              ].map((col) => (
                <TableCell
                  key={col.label}
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
              const studentName = generateName(s.id_student, s.gender ?? 'M')

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
                  <TableCell sx={{ fontSize: 12, color: tokens.text.primary, whiteSpace: 'nowrap' }}>{studentName}</TableCell>
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
    </Box>
  )
}
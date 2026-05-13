import { useEffect } from 'react'
import {
  Box, Typography, Select, MenuItem, FormControl, InputLabel,
  Slider, CircularProgress, Alert, Toolbar,
} from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { container } from '../../../di/container'
import { useContextStore } from '../../../shared/stores/contextStore'
import { useAuthStore } from '../../../shared/stores/authStore'
import { RiskTilesRow } from '../components/RiskTilesRow'
import { TierDistributionChart } from '../components/TierDistributionChart'
import { MarkDistributionChart } from '../components/MarkDistributionChart'
import { StudentRiskTable } from '../components/StudentRiskTable'
import type { StudentProfile } from '../../../types/domain'

export function DashboardView() {
  const navigate = useNavigate()
  const {
    selectedModule, selectedPresentation, currentWeek,
    setModule, setPresentation, setCurrentWeek, setNumWeeks, setActiveStudent,
  } = useContextStore()

  const { user } = useAuthStore()
  const isAdmin = user?.role === 'admin'
  const isAdvisor = user?.role === 'academic_advisor'

  // Load index of available courses
  const { data: index, isLoading: indexLoading, error: indexError } = useQuery({
    queryKey: ['oulad-index'],
    queryFn: () => container.dataService.getIndex(),
    retry: false,
  })

  // Auto-select first allowed course when index loads
  useEffect(() => {
    if (index && !selectedModule && index.courses.length > 0) {
      const allowedCourses = (isAdmin || isAdvisor)
        ? index.courses
        : index.courses.filter(
            (c) => user?.modules?.includes(c.module) && user?.presentations?.includes(c.presentation)
          )
      const first = allowedCourses[0]
      if (first) {
        setModule(first.module)
        setPresentation(first.presentation)
        setNumWeeks(first.num_weeks)
      }
    }
  }, [index, selectedModule, user])

  // Load course data when module/presentation is selected
  const { data: course, isLoading: courseLoading } = useQuery({
    queryKey: ['course', selectedModule, selectedPresentation],
    queryFn: () => container.dataService.getCourse(selectedModule, selectedPresentation),
    enabled: !!selectedModule && !!selectedPresentation,
  })

  // Update numWeeks when course loads
  useEffect(() => {
    if (course) setNumWeeks(course.num_weeks)
  }, [course, setNumWeeks])

  const numWeeks = course?.num_weeks ?? 39
  const students = course?.students ?? []

  // Filtered options based on role
  const allModules = [...new Set(index?.courses.map((c) => c.module) ?? [])]
  const moduleOptions = (isAdmin || isAdvisor)
    ? allModules
    : allModules.filter((m) => user?.modules?.includes(m))

  const presentationOptions = index?.courses
    .filter((c) => c.module === selectedModule)
    .filter((c) => (isAdmin || isAdvisor) ? true : user?.presentations?.includes(c.presentation))
    .map((c) => c.presentation) ?? []

  const handleStudentSelect = (s: StudentProfile) => {
    setActiveStudent(s)
    navigate(`/student/${s.id_student}`)
  }

  if (indexError) {
    return (
      <Box sx={{ p: 4 }}>
        <Alert severity="warning" sx={{ borderRadius: 2 }}>
          <strong>No preprocessed data found.</strong><br />
          Place OULAD CSV files in <code>public/data/oulad/</code> and run <code>npm run preprocess</code>.
        </Alert>
      </Box>
    )
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Header toolbar */}
      <Toolbar
        sx={{
          bgcolor: '#fff', borderBottom: '1px solid #E5E3DC', gap: 2, flexWrap: 'wrap',
          minHeight: '60px !important', px: 3, py: 1,
        }}
      >
        <Typography sx={{ fontSize: 14, fontWeight: 500, color: '#0A1628', fontFamily: '"IBM Plex Sans", sans-serif', mr: 1 }}>
          Class Overview
        </Typography>

        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel sx={{ fontSize: 12 }}>Module</InputLabel>
          <Select
            value={selectedModule}
            label="Module"
            onChange={(e) => {
              const mod = e.target.value
              const firstPres = index?.courses.find((c) => c.module === mod)?.presentation ?? ''
              setModule(mod)
              setPresentation(firstPres)
            }}
            sx={{ fontSize: 12, fontFamily: '"IBM Plex Mono", monospace' }}
          >
            {moduleOptions.map((m) => (
              <MenuItem key={m} value={m} sx={{ fontSize: 12, fontFamily: '"IBM Plex Mono", monospace' }}>{m}</MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel sx={{ fontSize: 12 }}>Presentation</InputLabel>
          <Select
            value={selectedPresentation}
            label="Presentation"
            onChange={(e) => setPresentation(e.target.value)}
            sx={{ fontSize: 12, fontFamily: '"IBM Plex Mono", monospace' }}
          >
            {presentationOptions.map((p) => (
              <MenuItem key={p} value={p} sx={{ fontSize: 12, fontFamily: '"IBM Plex Mono", monospace' }}>{p}</MenuItem>
            ))}
          </Select>
        </FormControl>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, minWidth: 240 }}>
          <Typography sx={{ fontSize: 11, color: '#6B7280', fontFamily: '"IBM Plex Mono", monospace', whiteSpace: 'nowrap' }}>
            Week
          </Typography>
          <Slider
            min={1}
            max={numWeeks}
            value={currentWeek}
            onChange={(_, v) => setCurrentWeek(v as number)}
            size="small"
            sx={{ color: '#1D9E75', flex: 1 }}
          />
          <Typography sx={{ fontSize: 12, fontFamily: '"IBM Plex Mono", monospace', color: '#0A1628', minWidth: 36 }}>
            {currentWeek}/{numWeeks}
          </Typography>
        </Box>
      </Toolbar>

      {/* Content */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 3 }}>
        {(indexLoading || courseLoading) && (
          <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'center', mb: 3 }}>
            <CircularProgress size={18} sx={{ color: '#1D9E75' }} />
            <Typography sx={{ fontSize: 13, color: '#6B7280', fontFamily: '"IBM Plex Mono", monospace' }}>
              Loading OULAD data…
            </Typography>
          </Box>
        )}

        {students.length > 0 && (
          <>
            <RiskTilesRow students={students} currentWeek={currentWeek} />

            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: 2, mb: 2, alignItems: 'start' }}>
              <StudentRiskTable
                students={students}
                currentWeek={currentWeek}
                onSelect={handleStudentSelect}
                selectedId={useContextStore.getState().activeStudent?.id_student ?? null}
              />
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <TierDistributionChart students={students} numWeeks={numWeeks} currentWeek={currentWeek} />
                <MarkDistributionChart students={students} currentWeek={currentWeek} />
              </Box>
            </Box>
          </>
        )}
      </Box>
    </Box>
  )
}
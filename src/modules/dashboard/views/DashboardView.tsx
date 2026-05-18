import { useEffect } from 'react'
import { Box, Typography, CircularProgress, Alert, Toolbar } from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { container } from '../../../di/container'
import { useContextStore } from '../../../shared/stores/contextStore'
import { RiskTilesRow } from '../components/RiskTilesRow'
import { TierDistributionChart } from '../components/TierDistributionChart'
import { MarkDistributionChart } from '../components/MarkDistributionChart'
import { StudentRiskTable } from '../components/StudentRiskTable'
import type { StudentProfile } from '../../../types/domain'

export function DashboardView() {
  const navigate = useNavigate()
  const { selectedModule, selectedPresentation, currentWeek, setNumWeeks, setActiveStudent } = useContextStore()

  const { error: indexError } = useQuery({
    queryKey: ['oulad-index'],
    queryFn: () => container.dataService.getIndex(),
    retry: false,
  })

  const { data: course, isLoading: courseLoading } = useQuery({
    queryKey: ['course', selectedModule, selectedPresentation],
    queryFn: () => container.dataService.getCourse(selectedModule, selectedPresentation),
    enabled: !!selectedModule && !!selectedPresentation,
  })

  useEffect(() => {
    if (course) setNumWeeks(course.num_weeks)
  }, [course, setNumWeeks])

  const numWeeks = course?.num_weeks ?? 39
  const students = course?.students ?? []

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
      <Toolbar sx={{ bgcolor: '#fff', borderBottom: '1px solid #E5E3DC', minHeight: '52px !important', px: 3 }}>
        <Typography sx={{ fontSize: 14, fontWeight: 500, color: '#0A1628', fontFamily: '"IBM Plex Sans", sans-serif' }}>
          Class Overview
        </Typography>
      </Toolbar>

      <Box sx={{ flex: 1, overflow: 'auto', p: 3 }}>
        {courseLoading && (
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

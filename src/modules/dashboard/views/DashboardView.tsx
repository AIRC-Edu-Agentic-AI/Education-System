import { useEffect } from 'react'
import { Box, Typography, CircularProgress, Alert, Toolbar, Grid } from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { container } from '../../../di/container'
import { useContextStore } from '../../../shared/stores/contextStore'

import { RiskTilesRow } from '../components/RiskTilesRow'
import { TierDistributionChart } from '../components/TierDistributionChart'
import { MarkDistributionChart } from '../components/MarkDistributionChart'
import { StudentRiskTable } from '../components/StudentRiskTable'
import { CourseInfoSections } from '../components/CourseInfoSections'
import { CourseSchedule } from '../components/CourseSchedule'

import './DashboardView.css'
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

  if (indexError) return <Box sx={{ p: 4 }}><Alert severity="warning">Data not found.</Alert></Box>

  return (
    <Box className="dashboard-container">
      <Toolbar className="dashboard-header" sx={{ px: 3 }}>
        <Typography className="dashboard-header-title">Class Analytics Overview</Typography>
      </Toolbar>

      <Box className="dashboard-content-scroll">
        {courseLoading && (
          <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'center', p: 3 }}>
            <CircularProgress size={18} sx={{ color: '#1D9E75' }} />
            <Typography sx={{ fontSize: 13, color: '#6B7280' }}>Loading course data...</Typography>
          </Box>
        )}

        {students.length > 0 && (
          <Box sx={{ p: 3 }}>
            <RiskTilesRow students={students} currentWeek={currentWeek} />

            <Box className="dashboard-main-grid">
              <StudentRiskTable
                students={students}
                currentWeek={currentWeek}
                onSelect={handleStudentSelect}
                selectedId={useContextStore.getState().activeStudent?.id_student ?? null}
              />
              <Box className="dashboard-chart-column">
                <TierDistributionChart students={students} numWeeks={numWeeks} currentWeek={currentWeek} />
                <MarkDistributionChart students={students} currentWeek={currentWeek} />
              </Box>
            </Box>

            <Typography className="dashboard-management-title" sx={{ mt: 4, mb: 2 }}>
              Course Management — {selectedModule}
            </Typography>
            
            <Grid container spacing={3} sx={{ pb: 4 }}>
              <Grid item xs={12} lg={7}>
                <Box className="dashboard-section-card" sx={{ height: '100%', minHeight: 450 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 2 }}>Weekly Schedule</Typography>
                  <CourseSchedule />
                </Box>
              </Grid>
              <Grid item xs={12} lg={5}>
                <Box className="dashboard-section-card" sx={{ height: '100%', minHeight: 450 }}>
                  <CourseInfoSections />
                </Box>
              </Grid>
            </Grid>
          </Box>
        )}
      </Box>
    </Box>
  )
}

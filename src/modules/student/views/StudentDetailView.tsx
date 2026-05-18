import { useParams, useNavigate } from 'react-router-dom'
import { Box, Typography, Button, Grid, Toolbar, CircularProgress } from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import ChatIcon from '@mui/icons-material/ChatBubbleOutlineRounded'
import ArrowBackIcon from '@mui/icons-material/ArrowBackRounded'
import { container } from '../../../di/container'
import { useContextStore } from '../../../shared/stores/contextStore'
import { StudentDemographicsCard } from '../components/StudentDemographicsCard'
import { RiskTrajectoryChart }     from '../components/RiskTrajectoryChart'
import { VleActivityChart }        from '../components/VleActivityChart'
import { AssessmentPanel }         from '../components/AssessmentPanel'
import { StudentNotesCard }        from '../components/StudentNotesCard'
import { MasteryGraphCard }        from '../components/MasteryGraphCard'

export function StudentDetailView() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { selectedModule, selectedPresentation, currentWeek, setActiveStudent, setChatPanelOpen } = useContextStore()

  const { data: student, isLoading } = useQuery({
    queryKey: ['student', selectedModule, selectedPresentation, id],
    queryFn: () => container.dataService.getStudent(selectedModule, selectedPresentation, Number(id)),
    enabled: !!selectedModule && !!selectedPresentation && !!id,
  })

  if (isLoading) return (
    <Box sx={{ display: 'flex', p: 4, gap: 1.5, alignItems: 'center' }}>
      <CircularProgress size={18} sx={{ color: '#1D9E75' }} />
      <Typography sx={{ fontSize: 13, color: '#6B7280', fontFamily: '"IBM Plex Mono", monospace' }}>
        Loading student data…
      </Typography>
    </Box>
  )

  if (!student) return (
    <Box sx={{ p: 4 }}>
      <Typography sx={{ color: '#E24B4A' }}>Student not found. Select a module/presentation first.</Typography>
    </Box>
  )

  const handleOpenChat = () => {
    setActiveStudent(student)
    setChatPanelOpen(true)
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      <Toolbar sx={{ bgcolor: '#fff', borderBottom: '1px solid #E5E3DC', gap: 2, minHeight: '60px !important', px: 3 }}>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/')} size="small" sx={{ color: '#6B7280', fontSize: 12 }}>
          Overview
        </Button>
        <Typography sx={{ fontSize: 14, fontWeight: 500, color: '#0A1628', fontFamily: '"IBM Plex Sans", sans-serif', flex: 1 }}>
          Student #{student.id_student} — {selectedModule} {selectedPresentation}
        </Typography>
        <Button variant="contained" size="small" startIcon={<ChatIcon />} onClick={handleOpenChat}
          sx={{ fontSize: 12, bgcolor: '#0F6E56', '&:hover': { bgcolor: '#085041' } }}>
          Discuss with AI
        </Button>
      </Toolbar>

      <Box sx={{ flex: 1, overflow: 'auto', p: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={4}>
            <Grid container spacing={2} sx={{ height: '100%' }}>
              <Grid item xs={12}>
                <StudentDemographicsCard student={student} />
              </Grid>
              <Grid item xs={12}>
                <StudentNotesCard studentId={student.id_student} />
              </Grid>
            </Grid>
          </Grid>

          <Grid item xs={12} md={8}>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <RiskTrajectoryChart student={student} currentWeek={currentWeek} />
              </Grid>
              <Grid item xs={12}>
                <VleActivityChart student={student} currentWeek={currentWeek} />
              </Grid>
              <Grid item xs={12}>
                <AssessmentPanel student={student} currentWeek={currentWeek} />
              </Grid>
              <Grid item xs={12}>
                <MasteryGraphCard student={student} module={selectedModule} />
              </Grid>
            </Grid>
          </Grid>
        </Grid>
      </Box>
    </Box>
  )
}

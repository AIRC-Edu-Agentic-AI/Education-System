import React, { useState } from 'react';
import { Box, Button, Typography, Divider } from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBackRounded';
import CalendarMonthIcon from '@mui/icons-material/CalendarMonthRounded';
import ScheduleCrud from '../components/ScheduleCrud';
import NotificationManager from '../components/NotificationManager';
import AttendanceDashboard from '../components/AttendanceDashboard';
import { useContextStore } from '../../../shared/stores/contextStore';
import { getUetCourseInfo } from '../utils/courseMapping';

export const ClassView = () => {
  const { selectedModule, selectedPresentation } = useContextStore();
  const uetCourse = getUetCourseInfo(selectedModule);
  const [isScheduleOpen, setIsScheduleOpen] = useState(false);

  if (isScheduleOpen) {
    return (
      <Box sx={{ bgcolor: 'background.default', minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ px: 3, py: 1.5, bgcolor: 'background.paper', borderBottom: '1px solid', borderColor: 'divider', display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => setIsScheduleOpen(false)}
            size="small"
            variant="outlined"
            sx={{ textTransform: 'none', borderRadius: 2 }}
          >
            Back to Dashboard
          </Button>
          <Divider orientation="vertical" flexItem />
          <Typography variant="body2" color="text.secondary">
            {uetCourse.code} — {uetCourse.name}
          </Typography>
        </Box>
        <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
          <ScheduleCrud module={selectedModule} presentation={selectedPresentation} />
        </Box>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3, bgcolor: 'background.default', minHeight: '100vh' }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h5" fontWeight={700} color="text.primary">
          {uetCourse.code} — {uetCourse.name}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
          Semester: {selectedPresentation}
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        <Box sx={{
          px: 3, py: 2,
          bgcolor: 'background.paper',
          borderRadius: 2,
          border: '1px solid',
          borderColor: 'divider',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: 2,
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Box sx={{ p: 1, bgcolor: 'primary.main', borderRadius: 1.5, display: 'flex', alignItems: 'center' }}>
              <CalendarMonthIcon sx={{ fontSize: 20, color: '#fff' }} />
            </Box>
            <Box>
              <Typography variant="body1" fontWeight={600} color="text.primary">Schedule Management</Typography>
              <Typography variant="caption" color="text.secondary">Manage teaching sessions and make-up classes</Typography>
            </Box>
          </Box>
          <Button
            variant="contained"
            onClick={() => setIsScheduleOpen(true)}
            startIcon={<CalendarMonthIcon />}
            sx={{ textTransform: 'none', borderRadius: 2, whiteSpace: 'nowrap' }}
          >
            Open Schedule
          </Button>
        </Box>

        <AttendanceDashboard module={selectedModule} presentation={selectedPresentation} />
        <NotificationManager />
      </Box>
    </Box>
  );
};
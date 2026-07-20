import React, { useState } from 'react';
import { Box, Tab, Tabs, Typography, Chip, Grid } from '@mui/material';
import DashboardIcon from '@mui/icons-material/DashboardRounded';
import CalendarMonthIcon from '@mui/icons-material/CalendarMonthRounded';
import ScheduleCrud from '../components/ScheduleCrud';
import NotificationManager from '../components/NotificationManager';
import AttendanceDashboard from '../components/AttendanceDashboard';
import ChatManager from '../components/ChatManager';
import { useContextStore } from '../../../shared/stores/contextStore';
import { getUetCourseInfo } from '../utils/courseMapping';

export const ClassView = () => {
  const { selectedModule, selectedPresentation } = useContextStore();
  const uetCourse = getUetCourseInfo(selectedModule);
  const [activeTab, setActiveTab] = useState(0);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', bgcolor: 'background.default' }}>
      <Box sx={{ px: 3, pt: 3, pb: 0, bgcolor: 'background.paper', borderBottom: '1px solid', borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <Typography variant="h6" fontWeight={700} color="text.primary" lineHeight={1.3}>
            {uetCourse.code} â€” {uetCourse.name}
          </Typography>
          <Chip label={selectedPresentation} size="small" sx={{ height: 20, fontSize: 11, bgcolor: 'action.selected' }} />
        </Box>

        <Tabs
          value={activeTab}
          onChange={(_, v) => setActiveTab(v)}
          sx={{
            '& .MuiTab-root': { minHeight: 44, fontSize: 13, textTransform: 'none', fontWeight: 500 },
            '& .Mui-selected': { fontWeight: 700 },
          }}
        >
          <Tab icon={<DashboardIcon sx={{ fontSize: 16 }} />} iconPosition="start" label="Overview" />
          <Tab icon={<CalendarMonthIcon sx={{ fontSize: 16 }} />} iconPosition="start" label="Schedule" />
          <Tab icon={<DashboardIcon sx={{ fontSize: 16 }} />} iconPosition="start" label="Messages" />
        </Tabs>
      </Box>

      <Box sx={{ flex: 1, p: activeTab === 1 ? 0 : 3 }}>
        {activeTab === 0 && (
          <Grid container spacing={2}>
            <Grid item xs={12} md={5}>
              <AttendanceDashboard module={selectedModule} presentation={selectedPresentation} />
            </Grid>
            <Grid item xs={12} md={7}>
              <NotificationManager module={selectedModule} presentation={selectedPresentation} />
            </Grid>
          </Grid>
        )}
        {activeTab === 1 && (
          <ScheduleCrud module={selectedModule} presentation={selectedPresentation} />
        )}
        {activeTab === 2 && (
          <ChatManager module={selectedModule} presentation={selectedPresentation} />
        )}
      </Box>
    </Box>
  );
};
import React, { useState } from 'react';
import { Box, Tab, Tabs, Typography, Chip, Grid } from '@mui/material';
import DashboardIcon from '@mui/icons-material/DashboardRounded';
import NotificationManager from '../components/NotificationManager';
import AttendanceDashboard from '../components/AttendanceDashboard';
import ChatManager from '../components/ChatManager';
import AssignmentManager from '../components/AssignmentManager';
import { useContextStore } from '../../../shared/stores/contextStore';

export const ClassView = () => {
  const { selectedModule, selectedPresentation } = useContextStore();
  const courseCode = `${selectedModule} ${selectedPresentation}`;
  const [activeTab, setActiveTab] = useState(0);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', bgcolor: 'background.default' }}>
      <Box sx={{ px: 3, pt: 3, pb: 0, bgcolor: 'background.paper', borderBottom: '1px solid', borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <Typography variant="h6" fontWeight={700} color="text.primary" lineHeight={1.3}>
            {selectedModule}
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
          <Tab icon={<DashboardIcon sx={{ fontSize: 16 }} />} iconPosition="start" label="Communication" />
          <Tab icon={<DashboardIcon sx={{ fontSize: 16 }} />} iconPosition="start" label="Assignments" />
        </Tabs>
      </Box>

      <Box sx={{ flex: 1, p: 3 }}>
        {activeTab === 0 && (
          <Grid container spacing={2}>
            <Grid item xs={12} md={12}>
              <AttendanceDashboard module={selectedModule} presentation={selectedPresentation} />
            </Grid>
          </Grid>
        )}
        {activeTab === 1 && (
          <Grid container spacing={2} sx={{ height: 'calc(100vh - 180px)' }}>
             <Grid item xs={12} md={5} sx={{ height: '100%', overflowY: 'auto' }}>
                <NotificationManager module={selectedModule} presentation={selectedPresentation} />
             </Grid>
             <Grid item xs={12} md={7} sx={{ height: '100%' }}>
                <ChatManager module={selectedModule} presentation={selectedPresentation} />
             </Grid>
          </Grid>
        )}
        {activeTab === 2 && (
          <Box sx={{ height: 'calc(100vh - 180px)' }}>
            <AssignmentManager module={selectedModule} presentation={selectedPresentation} />
          </Box>
        )}
      </Box>
    </Box>
  );
};
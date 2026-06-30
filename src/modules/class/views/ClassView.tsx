import React from 'react';
import ScheduleCrud from '../components/ScheduleCrud';
import NotificationManager from '../components/NotificationManager';
import AttendanceDashboard from '../components/AttendanceDashboard';
import { useContextStore } from '../../../shared/stores/contextStore';

export const ClassView = () => {
  const { selectedModule, selectedPresentation } = useContextStore();

  return (
    <div style={{ padding: '24px', backgroundColor: '#f4f6f8', minHeight: '100vh' }}>
      <h1 style={{ marginBottom: '24px', color: '#2c3e50', fontSize: '28px' }}>
        Class & Teaching Management
      </h1>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <ScheduleCrud />
        <AttendanceDashboard module={selectedModule} presentation={selectedPresentation} />
        <NotificationManager />
      </div>
    </div>
  );
};
import React, { useState } from 'react';
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
      <div style={{ backgroundColor: '#f4f6f8', minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '12px 24px', backgroundColor: '#fff', borderBottom: '1px solid #e0e0e0' }}>
          <button
            onClick={() => setIsScheduleOpen(false)}
            style={{
              padding: '8px 16px',
              backgroundColor: '#f1f3f4',
              color: '#3c4043',
              border: '1px solid #dadce0',
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: 'bold',
            }}
          >
            &larr; Back to Dashboard
          </button>
        </div>
        <div style={{ flexGrow: 1, overflow: 'auto' }}>
          <ScheduleCrud module={selectedModule} presentation={selectedPresentation} />
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: '24px', backgroundColor: '#f4f6f8', minHeight: '100vh' }}>
      <h1 style={{ marginBottom: '8px', color: '#2c3e50', fontSize: '28px' }}>
        {uetCourse.code} - {uetCourse.name}
      </h1>
      <p style={{ marginBottom: '24px', color: '#666', fontSize: '16px' }}>
        Class semester: {selectedPresentation}
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <div style={{
          padding: '24px',
          backgroundColor: '#fff',
          borderRadius: '8px',
          border: '1px solid #ddd',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <div>
            <h3 style={{ margin: '0 0 8px 0', color: '#2c3e50', fontSize: '20px' }}>Schedule Management</h3>
            <p style={{ margin: 0, color: '#666', fontSize: '14px' }}>Manage teaching sessions and make-up classes.</p>
          </div>
          <button
            onClick={() => setIsScheduleOpen(true)}
            style={{
              padding: '10px 24px',
              backgroundColor: '#00796b',
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: 'bold',
            }}
          >
            Open Schedule
          </button>
        </div>

        <AttendanceDashboard module={selectedModule} presentation={selectedPresentation} />
        <NotificationManager />
      </div>
    </div>
  );
};
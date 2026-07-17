import { useMemo } from 'react';
import { Box, Typography, Paper, List, ListItem, Link, Chip, Divider } from '@mui/material';
// Adjust the import path based on your folder structure
import { useContextStore } from '../../../shared/stores/contextStore';

// Local interface for Schedule UI, ensuring no modifications to the domain layer
interface ScheduleItemUI {
  id: string;
  week: number;
  title: string;
  description: string;
  lectureLink: string;
  isCurrent: boolean;
  isPast: boolean;
}

export function CourseSchedule() {
  const { selectedModule, currentWeek, numWeeks } = useContextStore();

  // Generate mock schedule data dynamically based on contextStore state
  const scheduleItems = useMemo<ScheduleItemUI[]>(() => {
    // Return empty if no module is selected yet
    if (!selectedModule) return [];

    const items: ScheduleItemUI[] = [];
    
    // Create mock data for each week up to numWeeks (default is 39)
    for (let w = 1; w <= numWeeks; w++) {
      items.push({
        id: `schedule-week-${w}`,
        week: w,
        title: `Lecture Week ${w}: Core Concepts of ${selectedModule}`,
        description: `This session covers the fundamental and advanced topics assigned for week ${w}. Please ensure you have reviewed the preliminary materials before joining.`,
        lectureLink: `https://lms.university.edu/${selectedModule}/lectures/week-${w}`,
        isCurrent: w === currentWeek,
        isPast: w < currentWeek,
      });
    }
    
    return items;
  }, [selectedModule, currentWeek, numWeeks]);

  // If no module is selected, we can hide the schedule or show a placeholder
  if (!selectedModule) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center', bgcolor: '#fcfcfc', border: '1px solid #E5E3DC', borderRadius: 2 }}>
        <Typography color="text.secondary">Please select a module to view the schedule.</Typography>
      </Paper>
    );
  }

  return (
    <Box sx={{ mt: 2 }}>
      <Paper sx={{ p: 2, border: '1px solid #E5E3DC', borderRadius: 2, bgcolor: '#fcfcfc', maxHeight: 500, overflowY: 'auto' }}>
        <Typography sx={{ fontWeight: 700, fontSize: 12, color: '#1D9E75', mb: 2, textTransform: 'uppercase', position: 'sticky', top: 0, bgcolor: '#fcfcfc', zIndex: 1, pb: 1 }}>
          Course Schedule & Lectures
        </Typography>
        
        <List disablePadding>
          {scheduleItems.map((item, index) => (
            <Box key={item.id}>
              <ListItem 
                sx={{ 
                  display: 'flex', 
                  flexDirection: 'column', 
                  alignItems: 'flex-start',
                  p: 2,
                  borderRadius: 2,
                  mb: 1,
                  // Highlight current week, dim past weeks
                  bgcolor: item.isCurrent ? '#F0FDF4' : (item.isPast ? '#F9FAFB' : '#FFFFFF'),
                  border: item.isCurrent ? '1px solid #86EFAC' : '1px solid transparent',
                  opacity: item.isPast ? 0.6 : 1,
                  transition: 'all 0.2s ease-in-out',
                }}
              >
                {/* Header: Week number and Status badge */}
                <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%', mb: 1 }}>
                  <Typography sx={{ fontWeight: 800, fontSize: 14, color: item.isCurrent ? '#166534' : 'text.primary' }}>
                    Week {item.week}
                  </Typography>
                  {item.isCurrent && (
                    <Chip label="Current Week" size="small" sx={{ bgcolor: '#22C55E', color: 'white', fontWeight: 600, fontSize: 10, height: 20 }} />
                  )}
                  {item.isPast && (
                    <Chip label="Completed" size="small" variant="outlined" sx={{ fontSize: 10, height: 20 }} />
                  )}
                </Box>

                {/* Content: Title and Description */}
                <Typography sx={{ fontWeight: 600, fontSize: 15, mb: 0.5 }}>
                  {item.title}
                </Typography>
                <Typography sx={{ fontSize: 13, color: 'text.secondary', mb: 1.5 }}>
                  {item.description}
                </Typography>

                {/* Footer: Lecture Link */}
                <Link 
                  href={item.lectureLink} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  sx={{ 
                    fontSize: 13, 
                    fontWeight: 600, 
                    color: item.isPast ? 'text.secondary' : '#2563EB',
                    textDecoration: 'none',
                    '&:hover': { textDecoration: 'underline' }
                  }}
                >
                  {item.isPast ? 'Review Lecture Recording ↗' : 'Join Lecture ↗'}
                </Link>
              </ListItem>
              
              {/* Render divider except for the last item */}
              {index < scheduleItems.length - 1 && <Divider sx={{ my: 0.5, borderStyle: 'dashed' }} />}
            </Box>
          ))}
        </List>
      </Paper>
    </Box>
  );
}
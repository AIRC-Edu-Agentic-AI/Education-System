import { useState, useMemo } from 'react';
import { 
  Box, Typography, List, ListItemText, Divider, 
  Skeleton, Dialog, DialogTitle, DialogContent, IconButton, ListItemButton 
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import { useQuery } from '@tanstack/react-query';
import { useContextStore } from '../../../shared/stores/contextStore';
import { container } from '../../../di/container';
import { AssessmentRecord } from '../../../types/domain';

interface AssignmentUI extends AssessmentRecord {
  weekDue: number;
  averageScore: number;
  distribution: number[]; 
}

export function CourseInfoSections() {
  const { selectedModule, selectedPresentation, currentWeek } = useContextStore();
  const [selectedAsgn, setSelectedAsgn] = useState<AssignmentUI | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['course-info', selectedModule, selectedPresentation],
    queryFn: () => container.dataService.getCourse(selectedModule, selectedPresentation),
    enabled: !!selectedModule && !!selectedPresentation
  });

  const assignments = useMemo(() => {
    if (!data || !data.students) return [];

    return data.students[0].assessments.map((baseAsgn): AssignmentUI => {
      let totalScore = 0, count = 0;
      const dist = [0, 0, 0, 0, 0];

      data.students.forEach(student => {
        const sa = student.assessments.find(a => a.id_assessment === baseAsgn.id_assessment);
        if (sa && typeof sa.score === 'number') {
          totalScore += sa.score; count++;
          if (sa.score <= 20) dist[0]++;
          else if (sa.score <= 40) dist[1]++;
          else if (sa.score <= 60) dist[2]++;
          else if (sa.score <= 80) dist[3]++;
          else dist[4]++;
        }
      });

      const isExam = baseAsgn.assessment_type === 'Exam';
      return {
        ...baseAsgn,
        weekDue: baseAsgn.date_due ? Math.ceil(baseAsgn.date_due / 7) : (isExam ? 39 : 0),
        averageScore: count > 0 ? Math.round(totalScore / count) : 0,
        distribution: dist
      };
    }).sort((a, b) => a.weekDue - b.weekDue);
  }, [data, currentWeek]);

  if (isLoading) return <Skeleton variant="rectangular" height={300} sx={{ borderRadius: 2 }} />;

  return (
    <Box>
      <Typography sx={{ fontWeight: 700, fontSize: 13, color: '#1D9E75', mb: 2, textTransform: 'uppercase' }}>
        Assignments Overview
      </Typography>
      <List dense sx={{ p: 0 }}>
        {assignments.map((item) => {
          const isFuture = item.weekDue > currentWeek;
          return (
            <ListItemButton 
              key={item.id_assessment} 
              onClick={() => setSelectedAsgn(item)}
              sx={{ 
                mb: 1, borderRadius: 2, border: '1px solid #F1F5F9',
                opacity: isFuture ? 0.6 : 1,
                bgcolor: isFuture ? 'transparent' : '#F8FAFC'
              }}
            >
              <ListItemText 
                primary={item.assessment_type} 
                secondary={`Week ${item.weekDue} | Weight: ${item.weight}%`}
                primaryTypographyProps={{ fontWeight: 700, fontSize: 13, color: isFuture ? '#64748B' : '#0F172A' }}
              />
              <Typography sx={{ fontWeight: 800, fontSize: 14, color: isFuture ? '#94A3B8' : '#1D9E75' }}>
                {isFuture ? '—' : `${item.averageScore}%`}
              </Typography>
            </ListItemButton>
          );
        })}
      </List>

      <Dialog open={!!selectedAsgn} onClose={() => setSelectedAsgn(null)} fullWidth maxWidth="sm">
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontWeight: 700 }}>
          {selectedAsgn?.assessment_type} Details
          <IconButton onClick={() => setSelectedAsgn(null)}><CloseIcon /></IconButton>
        </DialogTitle>
        <DialogContent dividers>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3, p: 2, bgcolor: '#F8FAFC', borderRadius: 2 }}>
            <Box>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 700 }}>AVG SCORE</Typography>
              <Typography variant="h5" sx={{ fontWeight: 800, color: '#1D9E75' }}>
                {selectedAsgn && selectedAsgn.weekDue > currentWeek ? 'TBD' : `${selectedAsgn?.averageScore}%`}
              </Typography>
            </Box>
            <Box sx={{ textAlign: 'right' }}>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 700 }}>WEIGHT</Typography>
              <Typography variant="h5" sx={{ fontWeight: 800 }}>{selectedAsgn?.weight}%</Typography>
            </Box>
          </Box>

          <Typography sx={{ fontWeight: 600, fontSize: 14, mb: 2 }}>Grade Distribution</Typography>
          <Box sx={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-around', height: 140, mb: 3, pt: 2 }}>
            {selectedAsgn?.distribution.map((val, idx) => {
              const labels = ['0-20', '21-40', '41-60', '61-80', '81-100'];
              const maxVal = Math.max(...(selectedAsgn?.distribution || [1]));
              return (
                <Box key={idx} sx={{ textAlign: 'center', width: '15%' }}>
                  <Typography sx={{ fontSize: 10, mb: 0.5, fontWeight: 600 }}>{val}</Typography>
                  <Box sx={{ 
                    height: `${(val / maxVal) * 100}px`, 
                    /* Restore old colors: Red-ish for low, Yellow for mid, Green-ish for high */
                    bgcolor: idx < 2 ? '#FDA4AF' : (idx === 2 ? '#FDE047' : '#6EE7B7'),
                    borderRadius: '4px 4px 0 0',
                    minHeight: 2 
                  }} />
                  <Typography sx={{ fontSize: 9, mt: 1, color: 'text.secondary' }}>{labels[idx]}</Typography>
                </Box>
              );
            })}
          </Box>

          <Divider sx={{ my: 2 }} />

          {/* Restore Assignment Info & Resources */}
          <Typography sx={{ fontWeight: 600, fontSize: 14, mb: 1 }}>Assignment Info</Typography>
          <Typography sx={{ fontSize: 13, color: '#4B5563', mb: 2 }}>
            This {selectedAsgn?.assessment_type} (ID: {selectedAsgn?.id_assessment}) is due on Day {selectedAsgn?.date_due}.
            It contributes significantly to the student's continuous assessment grade.
          </Typography>

          <Typography sx={{ fontWeight: 600, fontSize: 14, mb: 1 }}>Linked Resources</Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Typography sx={{ fontSize: 13, color: '#2563EB', cursor: 'pointer', '&:hover': { textDecoration: 'underline' } }}>
              • Download Handout (PDF)
            </Typography>
            <Typography sx={{ fontSize: 13, color: '#2563EB', cursor: 'pointer', '&:hover': { textDecoration: 'underline' } }}>
              • Submission Portal
            </Typography>
          </Box>
        </DialogContent>
      </Dialog>
    </Box>
  );
}
import React, { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Box, Typography, Skeleton, Stack } from '@mui/material';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000/api'

interface AttendanceStat {
  name: string;
  value: number;
  color: string;
}

interface AttendanceDashboardProps {
  module: string;
  presentation: string;
}

export default function AttendanceDashboard({ module, presentation }: AttendanceDashboardProps) {
  const [data, setData] = useState<AttendanceStat[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!module || !presentation) {
      setData([]);
      return;
    }

    const fetchStats = async () => {
      setLoading(true);
      try {
        const res = await fetch(`${API_BASE}/attendance-stats/${module}/${presentation}`);
        if (!res.ok) throw new Error('Network response was not ok');
        const stats = await res.json();

        const groupedStats = stats.reduce((acc: AttendanceStat[], item: AttendanceStat) => {
          const nameMap: Record<string, string> = {
            Pass: 'On Time',
            Distinction: 'On Time',
            Fail: 'Late',
            Withdrawn: 'Absent',
          };
          const colorMap: Record<string, string> = {
            'On Time': '#4CAF50',
            Late: '#FFC107',
            Absent: '#F44336',
          };

          const newName = nameMap[item.name] || item.name;
          const existing = acc.find((x) => x.name === newName);
          if (existing) {
            existing.value += item.value;
          } else {
            acc.push({ name: newName, value: item.value, color: colorMap[newName] || '#9E9E9E' });
          }
          return acc;
        }, []);

        setData(groupedStats);
      } catch (error) {
        console.error('Error fetching attendance data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [module, presentation]);

  const total = data.reduce((sum, d) => sum + d.value, 0);

  return (
    <Box sx={{ p: 2.5, border: '1px solid', borderColor: 'divider', borderRadius: 2, bgcolor: 'background.paper' }}>
      <Typography variant="body2" fontWeight={700} color="text.primary" sx={{ mb: 2 }}>
        Class Attendance Overview
      </Typography>

      {loading ? (
        <Stack direction="row" spacing={2} alignItems="center">
          <Skeleton variant="circular" width={160} height={160} />
          <Stack spacing={1} flex={1}>
            <Skeleton variant="rounded" height={20} width="60%" />
            <Skeleton variant="rounded" height={20} width="45%" />
            <Skeleton variant="rounded" height={20} width="50%" />
          </Stack>
        </Stack>
      ) : data.length > 0 ? (
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems="center">
          <Box sx={{ width: 200, height: 200, flexShrink: 0 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => [`${value} students`, '']} />
              </PieChart>
            </ResponsiveContainer>
          </Box>

          <Stack spacing={1.5} flex={1}>
            {data.map((entry) => (
              <Box key={entry.name} sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: entry.color, flexShrink: 0 }} />
                  <Typography variant="body2" color="text.secondary">{entry.name}</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  <Typography variant="body2" fontWeight={600} color="text.primary">{entry.value}</Typography>
                  <Typography variant="caption" color="text.disabled" sx={{ minWidth: 36, textAlign: 'right' }}>
                    {total > 0 ? `${((entry.value / total) * 100).toFixed(0)}%` : '—'}
                  </Typography>
                </Box>
              </Box>
            ))}
            <Box sx={{ pt: 1, borderTop: '1px solid', borderColor: 'divider', display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="caption" color="text.secondary">Total</Typography>
              <Typography variant="caption" fontWeight={700} color="text.primary">{total} students</Typography>
            </Box>
          </Stack>
        </Stack>
      ) : (
        <Typography variant="body2" color="text.disabled" textAlign="center" sx={{ py: 4 }}>
          Select a module and presentation to view attendance data.
        </Typography>
      )}
    </Box>
  );
}
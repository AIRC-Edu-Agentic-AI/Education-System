import React, { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';

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

  useEffect(() => {
    const fetchStats = async () => {
      if (!module || !presentation) {
        setData([]);
        return;
      }

      try {
        const res = await fetch(`http://localhost:8000/api/attendance-stats/${module}/${presentation}`);
        if (!res.ok) throw new Error('Network response was not ok');
        const stats = await res.json();

        const groupedStats = stats.reduce((acc: AttendanceStat[], item: any) => {
          const nameMap: Record<string, string> = {
            'Pass': 'On Time',
            'Distinction': 'On Time',
            'Fail': 'Late',
            'Withdrawn': 'Absent'
          };
          
          const newName = nameMap[item.name] || item.name;
          const existing = acc.find(x => x.name === newName);
          
          if (existing) {
            existing.value += item.value;
          } else {
            const colorMap: Record<string, string> = {
              'On Time': '#4CAF50',
              'Late': '#FFC107',
              'Absent': '#F44336'
            };
            
            acc.push({
              name: newName,
              value: item.value,
              color: colorMap[newName] || item.color || '#9E9E9E'
            });
          }
          return acc;
        }, []);

        setData(groupedStats);
      } catch (error) {
        console.error("Error fetching attendance data:", error);
      }
    };
    
    fetchStats();
  }, [module, presentation]);

  return (
    <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '8px', marginTop: '20px', backgroundColor: '#fff' }}>
      <h3 style={{ marginTop: 0, marginBottom: '20px' }}>Class Attendance Overview</h3>
      
      {data.length > 0 ? (
        <div style={{ width: '100%', height: 350 }}>
          <ResponsiveContainer>
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={70}
                outerRadius={110}
                paddingAngle={5}
                dataKey="value"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => `${value} students`} />
              <Legend verticalAlign="bottom" height={36} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <p style={{ color: '#666', textAlign: 'center' }}>Please select a module and presentation</p>
      )}
    </div>
  );
}
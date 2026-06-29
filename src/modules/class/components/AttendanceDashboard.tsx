import React, { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface AttendanceStat {
  name: string;
  value: number;
  color: string;
}

export default function AttendanceDashboard() {
  const [data, setData] = useState<AttendanceStat[]>([]);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/attendance-stats');
        const stats = await res.json();
        setData(stats);
      } catch (error) {
        console.error("Error fetching attendance data:", error);
      }
    };
    fetchStats();
  }, []);

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
         paddingAngle={5}                dataKey="value"
 label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => `${value}% students`} />
              <Legend verticalAlign="bottom" height={36}/>
            </PieChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <p style={{ color: '#666', textAlign: 'center' }}>Loading chart...</p>
      )}
    </div>
  );
}
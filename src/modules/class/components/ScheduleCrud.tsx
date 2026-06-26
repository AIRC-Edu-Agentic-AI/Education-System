import React, { useState, useEffect } from 'react';

interface Schedule {
    _id?: string;
    subject: string;
    classroom: string;
    date: string;
    type: 'Regular' | 'Makeup';
}

export default function ScheduleCrud() {
    const [schedules, setSchedules] = useState<Schedule[]>([]);
    const [subject, setSubject] = useState('');
    const [classroom, setClassroom] = useState('');
    const [date, setDate] = useState('');
    const [type, setType] = useState<'Regular' | 'Makeup'>('Regular');
    const [editingId, setEditingId] = useState<string | null>(null);

    const fetchSchedules = async () => {
        const res = await fetch('http://localhost:8000/api/schedules');
        const data = await res.json();
        setSchedules(data);
    };

    useEffect(() => {
        fetchSchedules();
    }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const payload = { subject, classroom, date, type };

        if (editingId) {
            await fetch(`http://localhost:8000/api/schedules/${editingId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            setEditingId(null);
        } else {
            await fetch('http://localhost:8000/api/schedules', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
        }

        setSubject('');
        setClassroom('');
        setDate('');
        fetchSchedules();
    };

    const handleEdit = (item: Schedule) => {
        if (!item._id) return;
        setEditingId(item._id);
        setSubject(item.subject);
        setClassroom(item.classroom);
        setDate(item.date);
        setType(item.type);
    };

    const handleDelete = async (id: string) => {
        await fetch(`http://localhost:8000/api/schedules/${id}`, { method: 'DELETE' });
        fetchSchedules();
    };

    return (
        <div style={{ padding: '20px', border: '1px solid #ccc', borderRadius: '8px', backgroundColor: '#fff' }}>
            <h3 style={{ marginTop: 0 }}>Schedule Management</h3>
            
            <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap' }}>
                <input type="text" placeholder="Subject Name" value={subject} onChange={e => setSubject(e.target.value)} required style={{ padding: '6px' }} />
                <input type="text" placeholder="Room" value={classroom} onChange={e => setClassroom(e.target.value)} required style={{ padding: '6px' }} />
                <input type="date" value={date} onChange={e => setDate(e.target.value)} required style={{ padding: '6px' }} />
                <select value={type} onChange={e => setType(e.target.value as any)} style={{ padding: '6px' }}>
                    <option value="Regular">Regular Class</option>
                    <option value="Makeup">Makeup Class</option>
                </select>
                <button type="submit" style={{ padding: '6px 12px', cursor: 'pointer' }}>
                    {editingId ? 'Update Schedule' : 'Add Schedule'}
                </button>
                {editingId && <button type="button" onClick={() => { setEditingId(null); setSubject(''); setClassroom(''); setDate(''); }} style={{ padding: '6px' }}>Cancel</button>}
            </form>

            <table border={1} cellPadding={8} style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                <thead>
                    <tr style={{ backgroundColor: '#f2f2f2' }}>
                        <th>Subject</th>
                        <th>Room</th>
                        <th>Date</th>
                        <th>Type</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {schedules.map((item) => (
                        <tr key={item._id}>
                            <td>{item.subject}</td>
                            <td>{item.classroom}</td>
                            <td>{item.date}</td>
                            <td>
                                <span style={{ padding: '2px 6px', borderRadius: '4px', backgroundColor: item.type === 'Regular' ? '#e6f4ea' : '#feeed6', color: item.type === 'Regular' ? '#137333' : '#b06000' }}>
                                    {item.type}
                                </span>
                            </td>
                            <td>
                                <button onClick={() => handleEdit(item)} style={{ marginRight: '5px' }}>Edit</button>
                                <button onClick={() => item._id && handleDelete(item._id)} style={{ color: 'red' }}>Delete</button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
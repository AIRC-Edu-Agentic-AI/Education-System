import React, { useState, useEffect } from 'react';

interface NotificationItem {
  _id?: string;
  senderRole: 'Admin' | 'Instructor';
  receiverRole: 'Instructor' | 'Student';
  type: 'General Notice' | 'Exam Schedule' | 'Makeup Class';
  title: string;
  content: string;
  createdAt: string;
}

export default function NotificationManager() {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [type, setType] = useState<NotificationItem['type']>('General Notice');

  const fetchNotifications = async () => {
    const res = await fetch('http://localhost:8000/api/notifications');
    const data = await res.json();
    setNotifications(data);
  };

  useEffect(() => {
    fetchNotifications();
    if (Notification.permission !== 'granted') {
      Notification.requestPermission();
    }
  }, []);

  const handleSendNotification = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      senderRole: 'Instructor',
      receiverRole: 'Student',
      type,
      title,
      content
    };

    await fetch('http://localhost:8000/api/notifications', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (Notification.permission === 'granted') {
      new Notification(`[${type}] ${title}`, { body: content });
    }

    setTitle('');
    setContent('');
    fetchNotifications();
  };

  return (
    <div style={{ display: 'flex', gap: '20px', marginTop: '20px', flexWrap: 'wrap' }}>
      <div style={{ flex: '1 1 300px', padding: '20px', border: '1px solid #ddd', borderRadius: '8px', backgroundColor: '#fff' }}>
        <h3 style={{ marginTop: 0 }}>Broadcast Notification</h3>
        <form onSubmit={handleSendNotification} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <select value={type} onChange={e => setType(e.target.value as NotificationItem['type'])} style={{ padding: '8px' }}>
            <option value="General Notice">General Notice</option>
            <option value="Exam Schedule">Exam Schedule</option>
            <option value="Makeup Class">Makeup Class</option>
          </select>
          <input type="text" placeholder="Title" value={title} onChange={e => setTitle(e.target.value)} required style={{ padding: '8px' }} />
          <textarea placeholder="Detailed content..." value={content} onChange={e => setContent(e.target.value)} required style={{ padding: '8px', minHeight: '100px' }} />
          <button type="submit" style={{ padding: '10px', backgroundColor: '#1976d2', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
            Send Notification
          </button>
        </form>
      </div>

      <div style={{ flex: '2 1 400px', padding: '20px', border: '1px solid #ddd', borderRadius: '8px', backgroundColor: '#fff', maxHeight: '400px', overflowY: 'auto' }}>
        <h3 style={{ marginTop: 0 }}>System Inbox</h3>
        {notifications.length === 0 ? (
          <p style={{ color: '#666' }}>No notifications yet.</p>
        ) : (
          notifications.map((noti) => (
            <div key={noti._id} style={{ padding: '12px', borderBottom: '1px solid #eee', marginBottom: '8px', backgroundColor: '#f9f9f9', borderRadius: '6px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <strong style={{ color: noti.senderRole === 'Admin' ? '#d32f2f' : '#1976d2', fontSize: '14px' }}>
                  [{noti.type}] From: {noti.senderRole}
                </strong>
                <small style={{ color: '#888' }}>{new Date(noti.createdAt).toLocaleString()}</small>
              </div>
              <div style={{ fontWeight: 'bold', fontSize: '16px', marginBottom: '4px' }}>{noti.title}</div>
              <p style={{ margin: 0, fontSize: '14px', color: '#444' }}>{noti.content}</p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
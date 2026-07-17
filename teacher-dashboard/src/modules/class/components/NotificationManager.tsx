import React, { useState, useEffect } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000/api'
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
import {
  Box, Card, Typography, TextField, Button, Chip, Divider,
  List, ListItem, ListItemText, ListItemIcon, Avatar, CircularProgress,
  Tab, Tabs, Autocomplete
} from '@mui/material';
import CampaignRoundedIcon from '@mui/icons-material/CampaignRounded';
import SendRoundedIcon from '@mui/icons-material/SendRounded';
import InfoRoundedIcon from '@mui/icons-material/InfoRounded';
import EventNoteRoundedIcon from '@mui/icons-material/EventNoteRounded';
import UpdateRoundedIcon from '@mui/icons-material/UpdateRounded';
import ReportRoundedIcon from '@mui/icons-material/ReportRounded';
import ChatRoundedIcon from '@mui/icons-material/ChatRounded';

interface NotificationItem {
  _id?: string;
  senderRole: 'Admin' | 'Instructor';
  receiverRole: 'Instructor' | 'Student';
  receiverId?: number;
  receiverName?: string;
  type: 'General Notice' | 'Exam Schedule' | 'Makeup Class' | 'Academic Warning' | 'Direct Message';
  title: string;
  content: string;
  createdAt: string;
}

interface StudentOption {
  id: number;
  name: string;
}

interface NotificationManagerProps {
  module?: string;
  presentation?: string;
}

export default function NotificationManager({ module, presentation }: NotificationManagerProps) {
  const [activeTab, setActiveTab] = useState(0);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [type, setType] = useState<Exclude<NotificationItem['type'], 'Direct Message'>>('General Notice');
  const [isSending, setIsSending] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const [students, setStudents] = useState<StudentOption[]>([]);
  const [selectedStudent, setSelectedStudent] = useState<StudentOption | null>(null);
  const [dmTitle, setDmTitle] = useState('');
  const [dmContent, setDmContent] = useState('');
  const [isDmSending, setIsDmSending] = useState(false);
  const [studentsLoading, setStudentsLoading] = useState(false);

  const fetchNotifications = async () => {
    try {
      setIsLoading(true);
      const res = await fetch(`${API_BASE}/notifications`);
      const data = await res.json();
      setNotifications(data);
    } catch (error) {
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchStudents = async () => {
    if (!module || !presentation) return;
    setStudentsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/course/${module}/${presentation}`);
      const data = await res.json();
      const list: StudentOption[] = (data.students ?? []).map((s: { id_student: number; name?: string }) => ({
        id: s.id_student,
        name: s.name || `Student #${s.id_student}`,
      }));
      setStudents(list);
    } catch (error) {
      console.error(error);
    } finally {
      setStudentsLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
    if (Notification.permission !== 'granted') {
      Notification.requestPermission();
    }
  }, []);

  useEffect(() => {
    if (activeTab === 1) fetchStudents();
  }, [activeTab, module, presentation]);

  const handleSendBroadcast = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !content.trim() || isSending) return;
    setIsSending(true);
    try {
      // Gửi tới /notify/broadcast với đúng schema để student app đọc được
      const studentIds = students.map(s => s.id);
      await fetch(`${BASE_URL}/notify/broadcast`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_ids: studentIds,
          type: type.toLowerCase().replace(/ /g, '_'),
          title,
          content,
          sender_role: 'instructor',
        }),
      });
      if (Notification.permission === 'granted') {
        new Notification(`[${type}] ${title}`, { body: content });
      }
      setTitle('');
      setContent('');
      setType('General Notice');
      await fetchNotifications();
    } catch (error) {
      console.error(error);
    } finally {
      setIsSending(false);
    }
  };

  const handleSendDirect = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedStudent || !dmTitle.trim() || !dmContent.trim() || isDmSending) return;
    setIsDmSending(true);
    try {
      // Gửi trực tiếp tới student_id cụ thể — student app sẽ nhận được
      await fetch(`${BASE_URL}/notify/broadcast`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_ids: [selectedStudent.id],
          type: 'direct_message',
          title: dmTitle,
          content: dmContent,
          sender_role: 'instructor',
        }),
      });
      setDmTitle('');
      setDmContent('');
      setSelectedStudent(null);
      await fetchNotifications();
    } catch (error) {
      console.error(error);
    } finally {
      setIsDmSending(false);
    }
  };

  const getTypeUI = (notiType: NotificationItem['type']) => {
    switch (notiType) {
      case 'Exam Schedule': return { color: 'error' as const, icon: <EventNoteRoundedIcon color="error" fontSize="small" /> };
      case 'Makeup Class': return { color: 'warning' as const, icon: <UpdateRoundedIcon color="warning" fontSize="small" /> };
      case 'Academic Warning': return { color: 'error' as const, icon: <ReportRoundedIcon color="error" fontSize="small" /> };
      case 'Direct Message': return { color: 'secondary' as const, icon: <ChatRoundedIcon color="secondary" fontSize="small" /> };
      default: return { color: 'info' as const, icon: <InfoRoundedIcon color="info" fontSize="small" /> };
    }
  };

  return (
    <Card elevation={0} sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ px: 2, pt: 2, pb: 0 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1.5 }}>
          <Avatar sx={{ bgcolor: 'primary.50', color: 'primary.main', width: 32, height: 32 }}>
            <CampaignRoundedIcon fontSize="small" />
          </Avatar>
          <Box>
            <Typography variant="subtitle1" fontWeight={700} lineHeight={1.2}>Messaging</Typography>
            <Typography variant="caption" color="text.secondary">Send notifications or direct messages to students</Typography>
          </Box>
        </Box>
        <Tabs
          value={activeTab}
          onChange={(_, v) => setActiveTab(v)}
          sx={{ '& .MuiTab-root': { minHeight: 36, fontSize: 12, textTransform: 'none', fontWeight: 500 }, '& .Mui-selected': { fontWeight: 700 } }}
        >
          <Tab icon={<CampaignRoundedIcon sx={{ fontSize: 15 }} />} iconPosition="start" label="Broadcast" />
          <Tab icon={<ChatRoundedIcon sx={{ fontSize: 15 }} />} iconPosition="start" label="Direct Message" />
        </Tabs>
      </Box>

      <Divider />

      {activeTab === 0 && (
        <Box component="form" onSubmit={handleSendBroadcast} sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', gap: 1, mb: 1.5, flexWrap: 'wrap' }}>
            {(['General Notice', 'Exam Schedule', 'Makeup Class', 'Academic Warning'] as const).map((t) => (
              <Chip
                key={t} label={t} size="small"
                onClick={() => setType(t)}
                color={type === t ? getTypeUI(t).color : 'default'}
                variant={type === t ? 'filled' : 'outlined'}
                sx={{ fontWeight: type === t ? 600 : 400, fontSize: '0.75rem' }}
              />
            ))}
          </Box>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
            <TextField fullWidth size="small" label="Title" value={title} onChange={(e) => setTitle(e.target.value)} required InputLabelProps={{ shrink: true }} />
            <TextField fullWidth size="small" multiline rows={2} label="Detailed Content" placeholder="Enter the detailed content..." value={content} onChange={(e) => setContent(e.target.value)} required InputLabelProps={{ shrink: true }} />
            <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Button type="submit" variant="contained" disableElevation size="small"
                endIcon={isSending ? <CircularProgress size={14} color="inherit" /> : <SendRoundedIcon fontSize="small" />}
                disabled={!title.trim() || !content.trim() || isSending}
                sx={{ px: 2, py: 0.5, borderRadius: 1, fontWeight: 600, textTransform: 'none' }}
              >
                {isSending ? 'Sending...' : 'Send'}
              </Button>
            </Box>
          </Box>
        </Box>
      )}

      {activeTab === 1 && (
        <Box component="form" onSubmit={handleSendDirect} sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
            <Autocomplete
              size="small"
              options={students}
              loading={studentsLoading}
              value={selectedStudent}
              onChange={(_, value) => {
                setSelectedStudent(value)
                if (value) setDmTitle(`Message to ${value.name}`)
              }}
              getOptionLabel={(o) => `${o.name} (#${o.id})`}
              renderInput={(params) => (
                <TextField {...params} label="Select student" placeholder="Search by name or ID..."
                  InputProps={{ ...params.InputProps, endAdornment: (<>{studentsLoading ? <CircularProgress size={14} /> : null}{params.InputProps.endAdornment}</>) }}
                />
              )}
            />
            <TextField fullWidth size="small" label="Title" value={dmTitle} onChange={(e) => setDmTitle(e.target.value)} required InputLabelProps={{ shrink: true }} />
            <TextField fullWidth size="small" multiline rows={3} label="Message" placeholder="Write your message..." value={dmContent} onChange={(e) => setDmContent(e.target.value)} required InputLabelProps={{ shrink: true }} />
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              {selectedStudent && (
                <Typography variant="caption" color="text.secondary">
                  To: {selectedStudent.name} (#{selectedStudent.id})
                </Typography>
              )}
              <Button type="submit" variant="contained" disableElevation size="small" color="secondary"
                endIcon={isDmSending ? <CircularProgress size={14} color="inherit" /> : <SendRoundedIcon fontSize="small" />}
                disabled={!selectedStudent || !dmTitle.trim() || !dmContent.trim() || isDmSending}
                sx={{ ml: 'auto', px: 2, py: 0.5, borderRadius: 1, fontWeight: 600, textTransform: 'none' }}
              >
                {isDmSending ? 'Sending...' : 'Send Message'}
              </Button>
            </Box>
          </Box>
        </Box>
      )}

      <Divider />

      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', bgcolor: 'background.default', borderBottomLeftRadius: 8, borderBottomRightRadius: 8, overflow: 'hidden' }}>
        <Box sx={{ px: 2, py: 1, borderBottom: '1px solid', borderColor: 'divider' }}>
          <Typography variant="caption" fontWeight={700} color="text.secondary" textTransform="uppercase">System Inbox</Typography>
        </Box>
        <List sx={{ p: 0, flex: 1, overflowY: 'auto', maxHeight: 220 }}>
          {isLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}><CircularProgress size={20} /></Box>
          ) : notifications.length === 0 ? (
            <Typography variant="caption" color="text.secondary" sx={{ p: 2, display: 'block', textAlign: 'center' }}>No notifications yet.</Typography>
          ) : (
            notifications.map((noti, index) => (
              <React.Fragment key={noti._id || index}>
                <ListItem alignItems="flex-start" sx={{ px: 2, py: 1, '&:hover': { bgcolor: 'action.hover' }, bgcolor: noti.senderRole === 'Admin' ? 'error.50' : 'transparent' }}>
                  <ListItemIcon sx={{ minWidth: 32, mt: 0.5 }}>{getTypeUI(noti.type).icon}</ListItemIcon>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', pr: 1, mb: 0.25 }}>
                        <Typography variant="body2" fontWeight={600}>{noti.title}</Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ whiteSpace: 'nowrap' }}>{new Date(noti.createdAt).toLocaleString()}</Typography>
                      </Box>
                    }
                    secondary={
                      <Box component="span" sx={{ display: 'flex', flexDirection: 'column' }}>
                        <Typography variant="caption" sx={{ color: noti.senderRole === 'Admin' ? 'error.main' : 'primary.main', fontWeight: 600, mb: 0.25 }}>
                          [{noti.type}] From: {noti.senderRole}
                          {noti.receiverName && ` → ${noti.receiverName}`}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                          {noti.content}
                        </Typography>
                      </Box>
                    }
                  />
                </ListItem>
                {index < notifications.length - 1 && <Divider component="li" />}
              </React.Fragment>
            ))
          )}
        </List>
      </Box>
    </Card>
  );
}
import React, { useState, useEffect } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000/api'
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
import {
  Box, Card, Typography, TextField, Button, Chip, Divider,
  List, ListItem, ListItemText, ListItemIcon, Avatar, CircularProgress,
  Tab, Tabs, Autocomplete, IconButton, Tooltip, Dialog, DialogTitle,
  DialogContent, DialogActions, DialogContentText
} from '@mui/material';
import { createFilterOptions } from '@mui/material/Autocomplete';
import CampaignRoundedIcon from '@mui/icons-material/CampaignRounded';
import SendRoundedIcon from '@mui/icons-material/SendRounded';
import InfoRoundedIcon from '@mui/icons-material/InfoRounded';
import EventNoteRoundedIcon from '@mui/icons-material/EventNoteRounded';
import UpdateRoundedIcon from '@mui/icons-material/UpdateRounded';
import ReportRoundedIcon from '@mui/icons-material/ReportRounded';
import ChatRoundedIcon from '@mui/icons-material/ChatRounded';
import EditRoundedIcon from '@mui/icons-material/EditRounded';
import DeleteRoundedIcon from '@mui/icons-material/DeleteRounded';

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

interface ClassGroup {
  class_name: string;
  members: number[];
}

interface StudentOption {
  id: number;
  name: string;
}

interface NotificationManagerProps {
  module?: string;
  presentation?: string;
}

const filterOptions = createFilterOptions<StudentOption>({
  limit: 50,
});

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

  // Class group state
  const [classGroups, setClassGroups] = useState<ClassGroup[]>([]);
  const [selectedClassGroup, setSelectedClassGroup] = useState<ClassGroup | null>(null);
  const [classGroupsLoading, setClassGroupsLoading] = useState(false);
  const [classTitle, setClassTitle] = useState('');
  const [classContent, setClassContent] = useState('');
  const [isClassSending, setIsClassSending] = useState(false);
  const [classType, setClassType] = useState<Exclude<NotificationItem['type'], 'Direct Message'>>('General Notice');

  // Edit state
  const [editingNoti, setEditingNoti] = useState<NotificationItem | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editContent, setEditContent] = useState('');
  const [isEditing, setIsEditing] = useState(false);

  // Delete state
  const [deletingNoti, setDeletingNoti] = useState<NotificationItem | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchNotifications = async () => {
    try {
      setIsLoading(true);
      const res = await fetch(`${BASE_URL}/notify/notifications`);
      const data = await res.json();
      setNotifications(Array.isArray(data) ? data : []);
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
      const res = await fetch(`${API_BASE}/course/${module}/${presentation}/students-lite`);
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

  const fetchClasses = async () => {
    if (!module || !presentation) return;
    setClassGroupsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/course/${module}/${presentation}/classes`);
      const data = await res.json();
      setClassGroups(data.classes ?? []);
    } catch (error) {
      console.error(error);
    } finally {
      setClassGroupsLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
    if ('Notification' in window && Notification.permission !== 'granted') {
      Notification.requestPermission();
    }
  }, []);

  useEffect(() => {
    if (activeTab === 1) fetchStudents();
    if (activeTab === 2) fetchClasses();
  }, [activeTab, module, presentation]);

  const handleSendBroadcast = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !content.trim() || isSending) return;
    setIsSending(true);
    try {
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
          course_code: module,
        }),
      });
      if ('Notification' in window && Notification.permission === 'granted') {
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
      await fetch(`${BASE_URL}/notify/broadcast`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_ids: [selectedStudent.id],
          type: 'direct_message',
          title: dmTitle,
          content: dmContent,
          sender_role: 'instructor',
          course_code: module,
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

  const handleSendClassBroadcast = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedClassGroup || !classTitle.trim() || !classContent.trim() || isClassSending) return;
    setIsClassSending(true);
    try {
      await fetch(`${BASE_URL}/notify/broadcast`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_ids: selectedClassGroup.members,
          type: classType.toLowerCase().replace(/ /g, '_'),
          title: classTitle,
          content: classContent,
          sender_role: 'instructor',
        }),
      });
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(`[${classType}] ${classTitle}`, { body: classContent });
      }
      setClassTitle('');
      setClassContent('');
      setClassType('General Notice');
      setSelectedClassGroup(null);
      await fetchNotifications();
    } catch (error) {
      console.error(error);
    } finally {
      setIsClassSending(false);
    }
  };

  // --- Edit handlers ---
  const handleOpenEdit = (noti: NotificationItem) => {
    setEditingNoti(noti);
    setEditTitle(noti.title || '');
    setEditContent(noti.content || '');
  };

  const handleCloseEdit = () => {
    setEditingNoti(null);
    setEditTitle('');
    setEditContent('');
  };

  const handleSaveEdit = async () => {
    if (!editingNoti?._id || isEditing) return;
    setIsEditing(true);
    try {
      const res = await fetch(`${BASE_URL}/notify/notifications/${editingNoti._id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: editTitle, content: editContent }),
      });
      if (!res.ok) throw new Error('Failed to update');
      handleCloseEdit();
      await fetchNotifications();
    } catch (error) {
      console.error(error);
    } finally {
      setIsEditing(false);
    }
  };

  // --- Delete handlers ---
  const handleOpenDelete = (noti: NotificationItem) => {
    setDeletingNoti(noti);
  };

  const handleCloseDelete = () => {
    setDeletingNoti(null);
  };

  const handleConfirmDelete = async () => {
    if (!deletingNoti?._id || isDeleting) return;
    setIsDeleting(true);
    try {
      const res = await fetch(`${BASE_URL}/notify/notifications/${deletingNoti._id}`, {
        method: 'DELETE',
      });
      if (!res.ok) throw new Error('Failed to delete');
      handleCloseDelete();
      await fetchNotifications();
    } catch (error) {
      console.error(error);
    } finally {
      setIsDeleting(false);
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
          <Tab icon={<CampaignRoundedIcon sx={{ fontSize: 15 }} />} iconPosition="start" label="Class Message" />
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
              filterOptions={filterOptions}
              loading={studentsLoading}
              value={selectedStudent}
              onChange={(_, value) => {
                setSelectedStudent(value)
                if (value) setDmTitle(`Message to ${value.name}`)
              }}
              getOptionLabel={(o) => `${o.name} (#${o.id})`}
              renderOption={(props, option) => (
                <li {...props} key={option.id}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                    <Avatar sx={{ width: 24, height: 24, fontSize: 11, bgcolor: 'primary.main' }}>
                      {option.name.charAt(0).toUpperCase()}
                    </Avatar>
                    <Box sx={{ flex: 1, minWidth: 0 }}>
                      <Typography variant="body2" sx={{ fontSize: 13, fontWeight: 500, lineHeight: 1.2 }} noWrap>
                        {option.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: 11 }}>
                        ID: #{option.id}
                      </Typography>
                    </Box>
                  </Box>
                </li>
              )}
              renderInput={(params) => (
                <TextField {...params} label="Select student" placeholder="Search by name or ID..."
                  InputProps={{ ...params.InputProps, endAdornment: (<>{studentsLoading ? <CircularProgress size={14} /> : null}{params.InputProps.endAdornment}</>) }}
                />
              )}
              noOptionsText={
                !module || !presentation
                  ? "Please select a course first"
                  : studentsLoading
                  ? "Loading students..."
                  : "No students found"
              }
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
                <ListItem
                  alignItems="flex-start"
                  sx={{
                    px: 2, py: 1,
                    '&:hover': { bgcolor: 'action.hover' },
                    '&:hover .noti-actions': { opacity: 1 },
                    bgcolor: noti.senderRole === 'Admin' ? 'error.50' : 'transparent',
                    position: 'relative',
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 32, mt: 0.5 }}>{getTypeUI(noti.type).icon}</ListItemIcon>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', pr: 1, mb: 0.25 }}>
                        <Typography variant="body2" fontWeight={600}>{noti.title}</Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <Typography variant="caption" color="text.secondary" sx={{ whiteSpace: 'nowrap' }}>{new Date(noti.createdAt).toLocaleString()}</Typography>
                          {noti._id && (
                            <Box
                              className="noti-actions"
                              sx={{
                                display: 'flex', gap: 0, opacity: 0,
                                transition: 'opacity 0.2s ease',
                              }}
                            >
                              <Tooltip title="Edit" arrow>
                                <IconButton size="small" onClick={(e) => { e.stopPropagation(); handleOpenEdit(noti); }} sx={{ p: 0.25 }}>
                                  <EditRoundedIcon sx={{ fontSize: 14, color: 'primary.main' }} />
                                </IconButton>
                              </Tooltip>
                              <Tooltip title="Delete" arrow>
                                <IconButton size="small" onClick={(e) => { e.stopPropagation(); handleOpenDelete(noti); }} sx={{ p: 0.25 }}>
                                  <DeleteRoundedIcon sx={{ fontSize: 14, color: 'error.main' }} />
                                </IconButton>
                              </Tooltip>
                            </Box>
                          )}
                        </Box>
                      </Box>
                    }
                    secondary={
                      <Box component="span" sx={{ display: 'flex', flexDirection: 'column' }}>
                        <Typography variant="caption" sx={{ color: noti.senderRole === 'Admin' ? 'error.main' : 'primary.main', fontWeight: 600, mb: 0.25 }}>
                          [{noti.type}] From: {noti.senderRole}
                          {noti.receiverName && ` ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ ${noti.receiverName}`}
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

      {/* Edit Dialog */}
      <Dialog open={Boolean(editingNoti)} onClose={handleCloseEdit} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ fontSize: 16, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 1 }}>
          <EditRoundedIcon sx={{ fontSize: 20, color: 'primary.main' }} />
          Edit Notification
        </DialogTitle>
        <DialogContent dividers>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <TextField
              fullWidth size="small" label="Title"
              value={editTitle} onChange={(e) => setEditTitle(e.target.value)}
              required InputLabelProps={{ shrink: true }}
            />
            <TextField
              fullWidth size="small" multiline rows={4} label="Content"
              value={editContent} onChange={(e) => setEditContent(e.target.value)}
              required InputLabelProps={{ shrink: true }}
            />
          </Box>
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={handleCloseEdit} color="inherit" disabled={isEditing} sx={{ textTransform: 'none', fontSize: 13 }}>
            Cancel
          </Button>
          <Button
            onClick={handleSaveEdit} variant="contained" disableElevation
            disabled={!editTitle.trim() || !editContent.trim() || isEditing}
            startIcon={isEditing ? <CircularProgress size={14} color="inherit" /> : null}
            sx={{ textTransform: 'none', fontSize: 13, boxShadow: 'none' }}
          >
            {isEditing ? 'Saving...' : 'Save Changes'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={Boolean(deletingNoti)} onClose={handleCloseDelete} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontSize: 16, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 1, color: 'error.main' }}>
          <DeleteRoundedIcon sx={{ fontSize: 20 }} />
          Delete Notification
        </DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ fontSize: 13 }}>
            Are you sure you want to delete "<strong>{deletingNoti?.title}</strong>"? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={handleCloseDelete} color="inherit" disabled={isDeleting} sx={{ textTransform: 'none', fontSize: 13 }}>
            Cancel
          </Button>
          <Button
            onClick={handleConfirmDelete} variant="contained" color="error" disableElevation
            disabled={isDeleting}
            startIcon={isDeleting ? <CircularProgress size={14} color="inherit" /> : null}
            sx={{ textTransform: 'none', fontSize: 13, boxShadow: 'none' }}
          >
            {isDeleting ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Card>
  );
}
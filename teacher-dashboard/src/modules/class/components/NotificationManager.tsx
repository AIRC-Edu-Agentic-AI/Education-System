import React, { useState, useEffect } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000/api';
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

import {
  Box, Card, Typography, TextField, Button, Chip, Divider,
  Avatar, CircularProgress, Tab, Tabs, IconButton, Tooltip, Dialog, DialogTitle,
  DialogContent, DialogActions, DialogContentText, Badge, InputAdornment,
  Paper, Alert
} from '@mui/material';
import CampaignRoundedIcon from '@mui/icons-material/CampaignRounded';
import SendRoundedIcon from '@mui/icons-material/SendRounded';
import InfoRoundedIcon from '@mui/icons-material/InfoRounded';
import EventNoteRoundedIcon from '@mui/icons-material/EventNoteRounded';
import UpdateRoundedIcon from '@mui/icons-material/UpdateRounded';
import ReportRoundedIcon from '@mui/icons-material/ReportRounded';
import ChatRoundedIcon from '@mui/icons-material/ChatRounded';
import EditRoundedIcon from '@mui/icons-material/EditRounded';
import DeleteRoundedIcon from '@mui/icons-material/DeleteRounded';
import InboxRoundedIcon from '@mui/icons-material/InboxRounded';
import AddRoundedIcon from '@mui/icons-material/AddRounded';
import SearchRoundedIcon from '@mui/icons-material/SearchRounded';
import ArrowBackRoundedIcon from '@mui/icons-material/ArrowBackRounded';

interface NotificationItem {
  _id?: string;
  senderRole?: 'Admin' | 'Instructor' | string;
  receiverRole?: 'Instructor' | 'Student' | string;
  receiverId?: number;
  receiverName?: string;
  type: 'General Notice' | 'Exam Schedule' | 'Makeup Class' | 'Academic Warning' | 'Direct Message' | string;
  title: string;
  content: string;
  createdAt: string;
  target_count?: number;
  course_code?: string;
}

interface StudentOption {
  id: number;
  name: string;
  tier?: number;
}

interface NotificationManagerProps {
  module?: string;
  presentation?: string;
}

export default function NotificationManager({ module, presentation }: NotificationManagerProps) {
  // 0: System Inbox, 1: Send Broadcast
  const [activeTab, setActiveTab] = useState(0);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [targetAudience, setTargetAudience] = useState<'all' | 'tier3' | 'tier2' | 'tier1'>('all');
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [type, setType] = useState<string>('General Notice');
  const [isSending, setIsSending] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Search and filter for Inbox
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [inboxFilter, setInboxFilter] = useState<'all' | 'academic_warning' | 'study_reminder' | 'exam_schedule' | 'other'>('all');

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
    }, 150);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Success toast feedback
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Students count & list
  const [students, setStudents] = useState<StudentOption[]>([]);

  // Edit state
  const [editingNoti, setEditingNoti] = useState<NotificationItem | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editContent, setEditContent] = useState('');
  const [isEditing, setIsEditing] = useState(false);

  // Delete state
  const [deletingNoti, setDeletingNoti] = useState<NotificationItem | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const sortByNewest = (list: NotificationItem[]) => {
    return [...list].sort((a, b) => {
      const timeA = new Date(a.createdAt || (a as Record<string, any>).created_at || 0).getTime();
      const timeB = new Date(b.createdAt || (b as Record<string, any>).created_at || 0).getTime();
      return timeB - timeA;
    });
  };

  const fetchNotifications = async () => {
    try {
      setIsLoading(true);
      const url = module ? `${BASE_URL}/notify/notifications?module=${module}${presentation ? `&presentation=${presentation}` : ''}` : `${BASE_URL}/notify/notifications`;
      const res = await fetch(url);
      const data = await res.json();
      if (Array.isArray(data)) {
        const seen = new Set<string>();
        const unique: NotificationItem[] = [];
        for (const item of data) {
          const key = `${item._id}_${item.title}_${item.content}`;
          if (!seen.has(key)) {
            seen.add(key);
            unique.push(item);
          }
        }
        setNotifications(sortByNewest(unique));
      } else {
        setNotifications([]);
      }
    } catch (error) {
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchStudents = async () => {
    if (!module || !presentation) return;
    try {
      const res = await fetch(`${API_BASE}/course/${module}/${presentation}/students-lite`);
      const data = await res.json();
      const list: StudentOption[] = (data.students ?? []).map((s: { id_student: number; name?: string; full_name?: string; tier?: number }) => ({
        id: s.id_student,
        name: s.full_name || s.name || `Student #${s.id_student}`,
        tier: s.tier,
      }));
      setStudents(list);
    } catch (error) {
      console.error(error);
    }
  };

  useEffect(() => {
    fetchNotifications();
    fetchStudents();
    if ('Notification' in window && Notification.permission !== 'granted') {
      Notification.requestPermission();
    }
  }, [module, presentation]);

  useEffect(() => {
    const wsUrl = BASE_URL.replace('http', 'ws');
    const socket = new WebSocket(`${wsUrl}/realtime-chat/ws/teacher_admin`);

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'new_notification' && data.notification) {
          setNotifications(prev => sortByNewest([data.notification, ...prev.filter(n => n._id !== data.notification._id)]));
        } else if (data.type === 'notification_updated' && data.notification) {
          setNotifications(prev => sortByNewest(prev.map(n => n._id === data.notification._id ? { ...n, ...data.notification } : n)));
        } else if (data.type === 'notification_deleted') {
          setNotifications(prev => prev.filter(n => n._id !== data.notification_id && n.title !== data.title && n.content !== data.content));
        }
      } catch (e) {
        console.error("Notification WS parse error", e);
      }
    };

    return () => {
      socket.close();
    };
  }, []);

  const handleSendBroadcast = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !content.trim() || isSending) return;
    setIsSending(true);
    try {
      const targetList = 
        targetAudience === 'tier3' ? students.filter(s => (s.tier || 1) === 3) :
        targetAudience === 'tier2' ? students.filter(s => (s.tier || 1) === 2) :
        targetAudience === 'tier1' ? students.filter(s => (s.tier || 1) === 1) :
        students;
      const studentIds = targetList.map(s => s.id);
      const courseCode = module && presentation ? `${module} ${presentation}` : (module || 'ALL');
      const res = await fetch(`${BASE_URL}/notify/broadcast`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_ids: studentIds.length > 0 ? studentIds : undefined,
          type: type.toLowerCase().replace(/ /g, '_'),
          title,
          content,
          sender_role: 'instructor',
          course_code: courseCode,
        }),
      });
      const data = await res.json();
      if (data?.log) {
        setNotifications(prev => [data.log, ...prev.filter(n => n._id !== data.log._id)]);
      }
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(`[${type}] ${title}`, { body: content });
      }
      setSuccessMsg(`Broadcast successfully sent to ${targetAudience === 'all' ? 'Entire Course' : `Tier ${targetAudience.replace('tier', '')}`}!`);
      setTitle('');
      setContent('');
      setType('General Notice');
      await fetchNotifications();
      setActiveTab(0); // Return to Inbox to view the sent notification
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (error) {
      console.error(error);
    } finally {
      setIsSending(false);
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

  const getTypeUI = (notiType: string) => {
    const lower = (notiType || '').toLowerCase();
    if (lower.includes('warning')) {
      return { label: 'Academic Warning', color: 'error' as const, bg: '#FEF2F2', border: '#FCA5A5', icon: <ReportRoundedIcon sx={{ fontSize: 18, color: '#DC2626' }} /> };
    }
    if (lower.includes('reminder') || lower.includes('makeup')) {
      return { label: 'Progress Reminder', color: 'warning' as const, bg: '#FFFBEB', border: '#FCD34D', icon: <UpdateRoundedIcon sx={{ fontSize: 18, color: '#D97706' }} /> };
    }
    if (lower.includes('exam')) {
      return { label: 'Exam Schedule', color: 'info' as const, bg: '#EFF6FF', border: '#93C5FD', icon: <EventNoteRoundedIcon sx={{ fontSize: 18, color: '#2563EB' }} /> };
    }
    if (lower.includes('direct') || lower.includes('message')) {
      return { label: 'Direct Message', color: 'secondary' as const, bg: '#FAF5FF', border: '#D8B4FE', icon: <ChatRoundedIcon sx={{ fontSize: 18, color: '#9333EA' }} /> };
    }
    return { label: 'General Notice', color: 'primary' as const, bg: '#F8FAFC', border: '#CBD5E1', icon: <InfoRoundedIcon sx={{ fontSize: 18, color: '#475569' }} /> };
  };

  const tier3Count = students.filter(s => (s.tier || 1) === 3).length;
  const tier2Count = students.filter(s => (s.tier || 1) === 2).length;
  const tier1Count = students.filter(s => (s.tier || 1) === 1).length;

  // Filtered notifications for search & category
  const filteredNotifications = React.useMemo(() => {
    return notifications.filter(n => {
      const matchesSearch = !debouncedSearch.trim() || 
        (n.title && n.title.toLowerCase().includes(debouncedSearch.toLowerCase())) ||
        (n.content && n.content.toLowerCase().includes(debouncedSearch.toLowerCase()));
      
      if (!matchesSearch) return false;

      const lowerType = (n.type || '').toLowerCase();
      if (inboxFilter === 'academic_warning') return lowerType.includes('warning');
      if (inboxFilter === 'study_reminder') return lowerType.includes('reminder') || lowerType.includes('makeup');
      if (inboxFilter === 'exam_schedule') return lowerType.includes('exam');
      return true;
    });
  }, [notifications, debouncedSearch, inboxFilter]);

  return (
    <Card elevation={0} sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 2.5, height: '100%', display: 'flex', flexDirection: 'column', bgcolor: 'background.paper', overflow: 'hidden' }}>
      {/* Top Header & View Switcher */}
      <Box sx={{ px: 2.5, pt: 2, pb: 1.5, borderBottom: '1px solid', borderColor: 'divider', bgcolor: 'background.paper' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1.5 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Avatar sx={{ bgcolor: 'primary.main', color: '#fff', width: 34, height: 34, boxShadow: '0 2px 6px rgba(37,99,235,0.25)' }}>
              <CampaignRoundedIcon fontSize="small" />
            </Avatar>
            <Box>
              <Typography variant="subtitle1" fontWeight={700} lineHeight={1.2}>
                System Notifications & Broadcasts
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {module} ({presentation}) — {students.length} Enrolled Students
              </Typography>
            </Box>
          </Box>

          {activeTab === 0 ? (
            <Button
              variant="contained"
              size="small"
              startIcon={<AddRoundedIcon sx={{ fontSize: 16 }} />}
              onClick={() => setActiveTab(1)}
              sx={{
                textTransform: 'none',
                fontWeight: 600,
                fontSize: '0.8rem',
                borderRadius: 2,
                px: 1.75,
                py: 0.5,
                boxShadow: '0 2px 6px rgba(37,99,235,0.25)'
              }}
            >
              Compose Broadcast
            </Button>
          ) : (
            <Button
              variant="outlined"
              size="small"
              startIcon={<ArrowBackRoundedIcon sx={{ fontSize: 16 }} />}
              onClick={() => setActiveTab(0)}
              sx={{
                textTransform: 'none',
                fontWeight: 600,
                fontSize: '0.8rem',
                borderRadius: 2,
                px: 1.5,
                py: 0.5,
              }}
            >
              Back to Inbox
            </Button>
          )}
        </Box>

        {/* Segmented Navigation Tabs */}
        <Tabs
          value={activeTab}
          onChange={(_, v) => setActiveTab(v)}
          sx={{
            minHeight: 38,
            '& .MuiTab-root': {
              minHeight: 38,
              py: 0.5,
              px: 1.75,
              fontSize: '0.8125rem',
              textTransform: 'none',
              fontWeight: 600,
              borderRadius: 1.5,
            },
            '& .Mui-selected': {
              color: 'primary.main',
              fontWeight: 700,
            }
          }}
        >
          <Tab
            icon={
              <Badge badgeContent={notifications.length} color="primary" sx={{ '& .MuiBadge-badge': { fontSize: '0.65rem', height: 16, minWidth: 16 } }}>
                <InboxRoundedIcon sx={{ fontSize: 18 }} />
              </Badge>
            }
            iconPosition="start"
            label="System Inbox"
          />
          <Tab
            icon={<CampaignRoundedIcon sx={{ fontSize: 18 }} />}
            iconPosition="start"
            label="Send Broadcast"
          />
        </Tabs>
      </Box>

      {/* Success Notification Alert */}
      {successMsg && (
        <Alert severity="success" sx={{ py: 0.5, px: 2, fontSize: '0.8125rem', borderRadius: 0 }} onClose={() => setSuccessMsg(null)}>
          {successMsg}
        </Alert>
      )}

      {/* TAB 0: SYSTEM INBOX (Full Height, Spacious, Rich Details) */}
      {activeTab === 0 && (
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', bgcolor: '#F8FAFC' }}>
          {/* Filter Bar & Search Box */}
          <Box sx={{ px: 2, py: 1.25, bgcolor: 'background.paper', borderBottom: '1px solid', borderColor: 'divider', display: 'flex', flexDirection: 'column', gap: 1 }}>
            <TextField
              size="small"
              placeholder="Search notifications by title, keyword, or content..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchRoundedIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
                  </InputAdornment>
                ),
              }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 2,
                  bgcolor: '#F8FAFC',
                  fontSize: '0.8125rem',
                  height: 36,
                }
              }}
            />

            <Box sx={{ display: 'flex', gap: 0.75, overflowX: 'auto', pb: 0.25 }}>
              <Chip
                label={`All (${notifications.length})`}
                size="small"
                onClick={() => setInboxFilter('all')}
                color={inboxFilter === 'all' ? 'primary' : 'default'}
                variant={inboxFilter === 'all' ? 'filled' : 'outlined'}
                sx={{ fontWeight: 600, fontSize: '0.725rem', height: 24 }}
              />
              <Chip
                label="Academic Warnings"
                size="small"
                onClick={() => setInboxFilter('academic_warning')}
                color={inboxFilter === 'academic_warning' ? 'error' : 'default'}
                variant={inboxFilter === 'academic_warning' ? 'filled' : 'outlined'}
                sx={{ fontWeight: 600, fontSize: '0.725rem', height: 24 }}
              />
              <Chip
                label="Progress Reminders"
                size="small"
                onClick={() => setInboxFilter('study_reminder')}
                color={inboxFilter === 'study_reminder' ? 'warning' : 'default'}
                variant={inboxFilter === 'study_reminder' ? 'filled' : 'outlined'}
                sx={{ fontWeight: 600, fontSize: '0.725rem', height: 24 }}
              />
              <Chip
                label="Exam Notices"
                size="small"
                onClick={() => setInboxFilter('exam_schedule')}
                color={inboxFilter === 'exam_schedule' ? 'info' : 'default'}
                variant={inboxFilter === 'exam_schedule' ? 'filled' : 'outlined'}
                sx={{ fontWeight: 600, fontSize: '0.725rem', height: 24 }}
              />
            </Box>
          </Box>

          {/* Notification List (Full Height Scrollable) */}
          <Box sx={{ flex: 1, overflowY: 'auto', p: 2, display: 'flex', flexDirection: 'column', gap: 1.5 }}>
            {isLoading ? (
              <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', py: 6, gap: 1.5 }}>
                <CircularProgress size={28} />
                <Typography variant="caption" color="text.secondary">Loading class notifications...</Typography>
              </Box>
            ) : filteredNotifications.length === 0 ? (
              <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', py: 8, textAlign: 'center' }}>
                <Avatar sx={{ width: 48, height: 48, bgcolor: 'action.hover', color: 'text.secondary', mb: 1.5 }}>
                  <InboxRoundedIcon />
                </Avatar>
                <Typography variant="subtitle2" fontWeight={600} color="text.primary">
                  {searchQuery ? 'No matching notifications found' : 'No notifications yet'}
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ maxWidth: 280, mt: 0.5, mb: 2 }}>
                  {searchQuery ? 'Try adjusting your search keywords or active filter tags.' : 'Send announcements, risk alerts, or study reminders to students in this course.'}
                </Typography>
                {!searchQuery && (
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<AddRoundedIcon />}
                    onClick={() => setActiveTab(1)}
                    sx={{ textTransform: 'none', fontWeight: 600, fontSize: '0.75rem', borderRadius: 2 }}
                  >
                    Send First Notification
                  </Button>
                )}
              </Box>
            ) : (
              filteredNotifications.map((noti, index) => {
                const ui = getTypeUI(noti.type);
                const createdDate = new Date(noti.createdAt || (noti as any).created_at || Date.now());
                const dateStr = !isNaN(createdDate.getTime()) ? createdDate.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'Recently';

                return (
                  <Paper
                    key={noti._id || index}
                    elevation={0}
                    sx={{
                      p: 2,
                      borderRadius: 2,
                      border: '1px solid',
                      borderColor: 'divider',
                      bgcolor: '#FFFFFF',
                      transition: 'all 0.2s ease',
                      '&:hover': {
                        borderColor: 'primary.main',
                        boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
                        '& .noti-actions': { opacity: 1 },
                      }
                    }}
                  >
                    {/* Header Row */}
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 1.5, mb: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75, px: 1, py: 0.35, bgcolor: ui.bg, border: `1px solid ${ui.border}`, borderRadius: 1.5 }}>
                          {ui.icon}
                          <Typography variant="caption" fontWeight={700} color={`${ui.color}.main`} sx={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: 0.5 }}>
                            {ui.label}
                          </Typography>
                        </Box>

                        {noti.target_count && (
                          <Chip
                            label={`📢 ${noti.target_count} Recipients`}
                            size="small"
                            sx={{ height: 20, fontSize: '0.675rem', fontWeight: 600, bgcolor: 'action.hover' }}
                          />
                        )}
                      </Box>

                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.725rem', whiteSpace: 'nowrap' }}>
                          {dateStr}
                        </Typography>

                        {noti._id && (
                          <Box className="noti-actions" sx={{ display: 'flex', opacity: 0.6, transition: 'opacity 0.2s ease' }}>
                            <Tooltip title="Edit Notification" arrow>
                              <IconButton size="small" onClick={() => handleOpenEdit(noti)} sx={{ p: 0.5, color: 'text.secondary', '&:hover': { color: 'primary.main' } }}>
                                <EditRoundedIcon sx={{ fontSize: 16 }} />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Delete Notification" arrow>
                              <IconButton size="small" onClick={() => handleOpenDelete(noti)} sx={{ p: 0.5, color: 'text.secondary', '&:hover': { color: 'error.main' } }}>
                                <DeleteRoundedIcon sx={{ fontSize: 16 }} />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        )}
                      </Box>
                    </Box>

                    {/* Title */}
                    <Typography variant="subtitle2" fontWeight={700} color="text.primary" sx={{ mb: 0.75, lineHeight: 1.35, fontSize: '0.875rem' }}>
                      {noti.title}
                    </Typography>

                    {/* Content */}
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{
                        fontSize: '0.8125rem',
                        lineHeight: 1.5,
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                        bgcolor: '#F8FAFC',
                        p: 1.25,
                        borderRadius: 1.5,
                        border: '1px solid',
                        borderColor: 'divider',
                      }}
                    >
                      {noti.content}
                    </Typography>
                  </Paper>
                );
              })
            )}
          </Box>
        </Box>
      )}

      {/* TAB 1: SEND BROADCAST COMPOSER */}
      {activeTab === 1 && (
        <Box sx={{ flex: 1, overflowY: 'auto', p: 2.5, bgcolor: '#F8FAFC' }}>
          <Box component="form" onSubmit={handleSendBroadcast} sx={{ display: 'flex', flexDirection: 'column', gap: 2.25 }}>
            {/* Target Audience Selector */}
            <Box>
              <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 700, display: 'block', mb: 1, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                1. Select Target Audience & Risk Tier:
              </Typography>
              <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 1.25 }}>
                {/* Entire Course */}
                <Paper
                  elevation={0}
                  onClick={() => {
                    setTargetAudience('all');
                    setType('General Notice');
                  }}
                  sx={{
                    p: 1.5,
                    cursor: 'pointer',
                    borderRadius: 2,
                    border: '2px solid',
                    borderColor: targetAudience === 'all' ? 'primary.main' : 'divider',
                    bgcolor: targetAudience === 'all' ? 'primary.50' : '#FFFFFF',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <Typography variant="subtitle2" fontWeight={700} color={targetAudience === 'all' ? 'primary.main' : 'text.primary'} sx={{ fontSize: '0.8125rem' }}>
                    🌐 Entire Course
                  </Typography>
                  <Typography variant="caption" color="text.secondary" display="block">
                    {students.length} Enrolled Students
                  </Typography>
                </Paper>

                {/* Tier 3 High Risk */}
                <Paper
                  elevation={0}
                  onClick={() => {
                    setTargetAudience('tier3');
                    setType('Academic Warning');
                    setTitle('[ACADEMIC WARNING] Support & Academic Improvement Guidance');
                    setContent('Dear Tier 3 students,\n\nThe instructor noticed that your course progress and activity may put your outcome at risk. Please contact your Instructor or Academic Advisor this week for personalized learning assistance and review sessions!\n\nBest regards,\nCourse Teaching Team');
                  }}
                  sx={{
                    p: 1.5,
                    cursor: 'pointer',
                    borderRadius: 2,
                    border: '2px solid',
                    borderColor: targetAudience === 'tier3' ? 'error.main' : 'divider',
                    bgcolor: targetAudience === 'tier3' ? '#FEF2F2' : '#FFFFFF',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <Typography variant="subtitle2" fontWeight={700} color={targetAudience === 'tier3' ? 'error.main' : 'text.primary'} sx={{ fontSize: '0.8125rem' }}>
                    🚨 Tier 3 — High Risk
                  </Typography>
                  <Typography variant="caption" color="text.secondary" display="block">
                    {tier3Count} High-Risk Students
                  </Typography>
                </Paper>

                {/* Tier 2 Moderate Risk */}
                <Paper
                  elevation={0}
                  onClick={() => {
                    setTargetAudience('tier2');
                    setType('General Notice');
                    setTitle('[PROGRESS REMINDER] Review Schedule & Assessment Submissions');
                    setContent('Dear Tier 2 students,\n\nPlease check upcoming assessment deadlines and dedicate time to review key lecture topics. If you encounter any difficulties, feel free to ask in the Discussion forum!\n\nBest of luck!');
                  }}
                  sx={{
                    p: 1.5,
                    cursor: 'pointer',
                    borderRadius: 2,
                    border: '2px solid',
                    borderColor: targetAudience === 'tier2' ? 'warning.main' : 'divider',
                    bgcolor: targetAudience === 'tier2' ? '#FFFBEB' : '#FFFFFF',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <Typography variant="subtitle2" fontWeight={700} color={targetAudience === 'tier2' ? 'warning.dark' : 'text.primary'} sx={{ fontSize: '0.8125rem' }}>
                    ⚠️ Tier 2 — Moderate
                  </Typography>
                  <Typography variant="caption" color="text.secondary" display="block">
                    {tier2Count} Moderate-Risk Students
                  </Typography>
                </Paper>

                {/* Tier 1 Low Risk */}
                <Paper
                  elevation={0}
                  onClick={() => {
                    setTargetAudience('tier1');
                    setType('General Notice');
                    setTitle('[COMMENDATION] Outstanding Performance & Advanced Resources');
                    setContent('Dear Tier 1 students,\n\nThe Teaching Team commends your active participation and strong performance. In-depth materials and extension exercises have been published on the portal for your further study.\n\nKeep up the great work!');
                  }}
                  sx={{
                    p: 1.5,
                    cursor: 'pointer',
                    borderRadius: 2,
                    border: '2px solid',
                    borderColor: targetAudience === 'tier1' ? 'success.main' : 'divider',
                    bgcolor: targetAudience === 'tier1' ? '#F0FDF4' : '#FFFFFF',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <Typography variant="subtitle2" fontWeight={700} color={targetAudience === 'tier1' ? 'success.main' : 'text.primary'} sx={{ fontSize: '0.8125rem' }}>
                    🌟 Tier 1 — Low Risk
                  </Typography>
                  <Typography variant="caption" color="text.secondary" display="block">
                    {tier1Count} Good Progress Students
                  </Typography>
                </Paper>
              </Box>
            </Box>

            {/* Notification Category */}
            <Box>
              <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 700, display: 'block', mb: 1, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                2. Notification Category:
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {(['General Notice', 'Exam Schedule', 'Makeup Class', 'Academic Warning'] as const).map((t) => {
                  const isSel = type === t;
                  return (
                    <Chip
                      key={t}
                      label={t}
                      size="small"
                      onClick={() => setType(t)}
                      color={isSel ? getTypeUI(t).color : 'default'}
                      variant={isSel ? 'filled' : 'outlined'}
                      sx={{ fontWeight: isSel ? 700 : 500, fontSize: '0.75rem', px: 0.5 }}
                    />
                  );
                })}
              </Box>
            </Box>

            {/* Title & Content */}
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.75 }}>
              <TextField
                fullWidth
                size="small"
                label="Notification Title"
                placeholder="e.g., [ACADEMIC WARNING] Support Guidance..."
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                InputLabelProps={{ shrink: true }}
                sx={{ '& .MuiOutlinedInput-root': { bgcolor: '#FFFFFF', borderRadius: 1.5 } }}
              />

              <TextField
                fullWidth
                size="small"
                multiline
                rows={4}
                label="Broadcast Message Content"
                placeholder="Enter detailed message for students..."
                value={content}
                onChange={(e) => setContent(e.target.value)}
                required
                InputLabelProps={{ shrink: true }}
                sx={{ '& .MuiOutlinedInput-root': { bgcolor: '#FFFFFF', borderRadius: 1.5 } }}
              />
            </Box>

            {/* Action Bar */}
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pt: 1 }}>
              <Button
                variant="text"
                size="small"
                onClick={() => setActiveTab(0)}
                sx={{ textTransform: 'none', fontWeight: 600, color: 'text.secondary' }}
              >
                Cancel
              </Button>

              <Button
                type="submit"
                variant="contained"
                disableElevation
                size="medium"
                endIcon={isSending ? <CircularProgress size={16} color="inherit" /> : <SendRoundedIcon fontSize="small" />}
                disabled={!title.trim() || !content.trim() || isSending}
                sx={{
                  px: 3,
                  py: 0.75,
                  borderRadius: 2,
                  fontWeight: 700,
                  fontSize: '0.85rem',
                  textTransform: 'none',
                  boxShadow: '0 4px 12px rgba(37,99,235,0.25)'
                }}
              >
                {isSending ? 'Sending Broadcast...' : `Send to ${targetAudience === 'all' ? 'Entire Course' : `Tier ${targetAudience.replace('tier', '')}`}`}
              </Button>
            </Box>
          </Box>
        </Box>
      )}

      {/* Edit Notification Dialog */}
      <Dialog open={!!editingNoti} onClose={handleCloseEdit} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ fontWeight: 700 }}>Edit Notification</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
          <TextField
            fullWidth
            size="small"
            label="Title"
            value={editTitle}
            onChange={(e) => setEditTitle(e.target.value)}
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            fullWidth
            size="small"
            multiline
            rows={4}
            label="Content"
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            InputLabelProps={{ shrink: true }}
          />
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={handleCloseEdit} sx={{ textTransform: 'none', fontWeight: 600 }}>Cancel</Button>
          <Button
            onClick={handleSaveEdit}
            variant="contained"
            disabled={!editTitle.trim() || !editContent.trim() || isEditing}
            sx={{ textTransform: 'none', fontWeight: 600, borderRadius: 1.5 }}
          >
            {isEditing ? 'Saving...' : 'Save Changes'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Notification Confirmation Dialog */}
      <Dialog open={!!deletingNoti} onClose={handleCloseDelete} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontWeight: 700, color: 'error.main' }}>Delete Notification</DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ fontSize: '0.875rem' }}>
            Are you sure you want to delete notification <strong>"{deletingNoti?.title}"</strong>? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={handleCloseDelete} sx={{ textTransform: 'none', fontWeight: 600 }}>Cancel</Button>
          <Button
            onClick={handleConfirmDelete}
            color="error"
            variant="contained"
            disabled={isDeleting}
            sx={{ textTransform: 'none', fontWeight: 600, borderRadius: 1.5 }}
          >
            {isDeleting ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Card>
  );
}
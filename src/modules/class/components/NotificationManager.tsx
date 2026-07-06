import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  Typography,
  TextField,
  Button,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Avatar,
  CircularProgress
} from '@mui/material';
import CampaignRoundedIcon from '@mui/icons-material/CampaignRounded';
import SendRoundedIcon from '@mui/icons-material/SendRounded';
import InfoRoundedIcon from '@mui/icons-material/InfoRounded';
import EventNoteRoundedIcon from '@mui/icons-material/EventNoteRounded';
import UpdateRoundedIcon from '@mui/icons-material/UpdateRounded';

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
  const [isSending, setIsSending] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const fetchNotifications = async () => {
    try {
      setIsLoading(true);
      const res = await fetch('http://localhost:8000/api/notifications');
      const data = await res.json();
      setNotifications(data);
    } catch (error) {
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
    if (Notification.permission !== 'granted') {
      Notification.requestPermission();
    }
  }, []);

  const handleSendNotification = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !content.trim() || isSending) return;

    setIsSending(true);
    const payload = {
      senderRole: 'Instructor',
      receiverRole: 'Student',
      type,
      title,
      content
    };

    try {
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
      setType('General Notice');
      await fetchNotifications();
    } catch (error) {
      console.error(error);
    } finally {
      setIsSending(false);
    }
  };

  const getTypeUI = (notiType: NotificationItem['type']) => {
    switch (notiType) {
      case 'Exam Schedule':
        return { color: 'error' as const, icon: <EventNoteRoundedIcon color="error" fontSize="small" /> };
      case 'Makeup Class':
        return { color: 'warning' as const, icon: <UpdateRoundedIcon color="warning" fontSize="small" /> };
      case 'General Notice':
      default:
        return { color: 'info' as const, icon: <InfoRoundedIcon color="info" fontSize="small" /> };
    }
  };

  return (
    <Card elevation={0} sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box component="form" onSubmit={handleSendNotification} sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1.5 }}>
          <Avatar sx={{ bgcolor: 'primary.50', color: 'primary.main', width: 32, height: 32 }}>
            <CampaignRoundedIcon fontSize="small" />
          </Avatar>
          <Box>
            <Typography variant="subtitle1" fontWeight={700} lineHeight={1.2}>
              Broadcast Notification
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Send instant messages to all students in the class
            </Typography>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', gap: 1, mb: 1.5, flexWrap: 'wrap' }}>
          {(['General Notice', 'Exam Schedule', 'Makeup Class'] as const).map((t) => (
            <Chip
              key={t}
              label={t}
              size="small"
              onClick={() => setType(t)}
              color={type === t ? getTypeUI(t).color : 'default'}
              variant={type === t ? 'filled' : 'outlined'}
              sx={{
                fontWeight: type === t ? 600 : 400,
                fontSize: '0.75rem'
              }}
            />
          ))}
        </Box>

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
          <TextField
            fullWidth
            size="small"
            label="Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            fullWidth
            size="small"
            multiline
            rows={2}
            label="Detailed Content"
            placeholder="Enter the detailed content..."
            value={content}
            onChange={(e) => setContent(e.target.value)}
            required
            InputLabelProps={{ shrink: true }}
          />
          <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              type="submit"
              variant="contained"
              disableElevation
              size="small"
              endIcon={isSending ? <CircularProgress size={14} color="inherit" /> : <SendRoundedIcon fontSize="small" />}
              disabled={!title.trim() || !content.trim() || isSending}
              sx={{ px: 2, py: 0.5, borderRadius: 1, fontWeight: 600, textTransform: 'none' }}
            >
              {isSending ? 'Sending...' : 'Send'}
            </Button>
          </Box>
        </Box>
      </Box>

      <Divider />

      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', bgcolor: 'background.default', borderBottomLeftRadius: 8, borderBottomRightRadius: 8, overflow: 'hidden' }}>
        <Box sx={{ px: 2, py: 1, borderBottom: '1px solid', borderColor: 'divider' }}>
          <Typography variant="caption" fontWeight={700} color="text.secondary" textTransform="uppercase">
            System Inbox
          </Typography>
        </Box>

        <List sx={{ p: 0, flex: 1, overflowY: 'auto', maxHeight: 220 }}>
          {isLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
              <CircularProgress size={20} />
            </Box>
          ) : notifications.length === 0 ? (
            <Typography variant="caption" color="text.secondary" sx={{ p: 2, display: 'block', textAlign: 'center' }}>
              No notifications yet.
            </Typography>
          ) : (
            notifications.map((noti, index) => (
              <React.Fragment key={noti._id || index}>
                <ListItem
                  alignItems="flex-start"
                  sx={{
                    px: 2, py: 1,
                    '&:hover': { bgcolor: 'action.hover' },
                    bgcolor: noti.senderRole === 'Admin' ? 'error.50' : 'transparent'
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 32, mt: 0.5 }}>
                    {getTypeUI(noti.type).icon}
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', pr: 1, mb: 0.25 }}>
                        <Typography variant="body2" fontWeight={600}>
                          {noti.title}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ whiteSpace: 'nowrap' }}>
                          {new Date(noti.createdAt).toLocaleString()}
                        </Typography>
                      </Box>
                    }
                    secondary={
                      <Box component="span" sx={{ display: 'flex', flexDirection: 'column' }}>
                        <Typography variant="caption" sx={{ color: noti.senderRole === 'Admin' ? 'error.main' : 'primary.main', fontWeight: 600, mb: 0.25 }}>
                          [{noti.type}] From: {noti.senderRole}
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
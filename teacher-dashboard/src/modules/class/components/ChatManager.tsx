import React, { useState, useEffect, useRef } from 'react';
import {
  Box, Card, Typography, TextField, IconButton, List, ListItem,
  ListItemText, ListItemAvatar, Avatar, Divider, CircularProgress,
  Dialog, DialogTitle, DialogContent, DialogActions, Button,
  Autocomplete, Tooltip, Chip
} from '@mui/material';
import SendRoundedIcon from '@mui/icons-material/SendRounded';
import AddRoundedIcon from '@mui/icons-material/AddRounded';
import GroupRoundedIcon from '@mui/icons-material/GroupRounded';
import PersonRoundedIcon from '@mui/icons-material/PersonRounded';
import CampaignRoundedIcon from '@mui/icons-material/CampaignRounded';
import ForumRoundedIcon from '@mui/icons-material/ForumRounded';
import { getUetCourseInfo } from '../utils/courseMapping';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000/api';
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
const WS_URL = BASE_URL.replace('http', 'ws');

interface ChatManagerProps {
  module?: string;
  presentation?: string;
}

interface Channel {
  _id: string;
  course_code: string;
  type: string;
  name: string;
  members?: string[];
  created_at: string;
}

interface Message {
  _id: string;
  channel_id: string;
  sender_id: string;
  sender_role: string;
  content: string;
  created_at: string;
}

interface ClassGroup {
  class_name: string;
  members: number[];
}

export default function ChatManager({ module, presentation }: ChatManagerProps) {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [activeChannel, setActiveChannel] = useState<Channel | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loadingChannels, setLoadingChannels] = useState(false);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [inputMessage, setInputMessage] = useState('');

  const [isCreating, setIsCreating] = useState(false);
  const [classGroups, setClassGroups] = useState<ClassGroup[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<ClassGroup | null>(null);

  const ws = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const TEACHER_ID = "teacher_admin";
  const courseCode = module ? getUetCourseInfo(module).code : '';

  useEffect(() => {
    if (courseCode) {
      fetchChannels();
      setupWebSocket();
    }
    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [courseCode]);

  useEffect(() => {
    if (activeChannel) {
      fetchMessages(activeChannel._id);
    }
  }, [activeChannel]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const setupWebSocket = () => {
    if (ws.current) ws.current.close();
    const socket = new WebSocket(`${WS_URL}/realtime-chat/ws/${TEACHER_ID}`);

    socket.onopen = () => console.log("Chat WS Connected");

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'new_message') {
          const newMsg = data.message as Message;
          setMessages(prev => {
            if (activeChannel && newMsg.channel_id === activeChannel._id) {
              if (!prev.find(m => m._id === newMsg._id)) {
                return [...prev, newMsg];
              }
            }
            return prev;
          });
        } else if (data.type === 'channel_created') {
          fetchChannels();
        }
      } catch (e) {
        console.error("WS Parse error", e);
      }
    };

    socket.onclose = () => {
      setTimeout(setupWebSocket, 3000);
    };

    ws.current = socket;
  };

  const fetchChannels = async () => {
    setLoadingChannels(true);
    try {
      const res = await fetch(`${BASE_URL}/realtime-chat/channels?user_id=${TEACHER_ID}&course_code=${courseCode}`);
      const data = await res.json();
      setChannels(data);
      if (data.length > 0 && !activeChannel) {
        setActiveChannel(data[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingChannels(false);
    }
  };

  const fetchMessages = async (channelId: string) => {
    setLoadingMessages(true);
    try {
      const res = await fetch(`${BASE_URL}/realtime-chat/channels/${channelId}/messages`);
      const data = await res.json();
      setMessages(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingMessages(false);
    }
  };

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || !activeChannel || !ws.current) return;

    const payload = {
      channel_id: activeChannel._id,
      content: inputMessage.trim(),
      sender_role: 'instructor'
    };

    ws.current.send(JSON.stringify(payload));
    setInputMessage('');
  };

  const handleOpenCreate = async () => {
    setIsCreating(true);
    if (!module || !presentation) return;
    try {
      const res = await fetch(`${API_BASE}/course/${module}/${presentation}/classes`);
      const data = await res.json();
      setClassGroups(data.classes ?? []);
    } catch (e) {
      console.error(e);
    }
  };

  const handleConfirmCreate = async () => {
    if (!selectedGroup) return;
    try {
      const members = selectedGroup.members.map(String);
      if (!members.includes(TEACHER_ID)) members.push(TEACHER_ID);

      const res = await fetch(`${BASE_URL}/realtime-chat/channels`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          course_code: courseCode,
          name: `Lớp ${selectedGroup.class_name}`,
          members: members,
          type: 'class_group'
        })
      });
      if (res.ok) {
        setIsCreating(false);
        setSelectedGroup(null);
        fetchChannels();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const getChannelIcon = (type: string) => {
    switch (type) {
      case 'announcement': return <CampaignRoundedIcon />;
      case 'discussion': return <ForumRoundedIcon />;
      case 'class_group': return <GroupRoundedIcon />;
      default: return <PersonRoundedIcon />;
    }
  };
  const getChannelColor = (type: string) => {
    switch (type) {
      case 'announcement': return 'error.main';
      case 'discussion': return 'success.main';
      case 'class_group': return 'primary.main';
      default: return 'secondary.main';
    }
  };

  return (
    <Card sx={{ display: 'flex', height: 'calc(100vh - 160px)', minHeight: 500, borderRadius: 2, boxShadow: '0 4px 20px rgba(0,0,0,0.05)', overflow: 'hidden' }}>
      {/* Sidebar */}
      <Box sx={{ width: 320, borderRight: '1px solid', borderColor: 'divider', display: 'flex', flexDirection: 'column', bgcolor: 'background.paper' }}>
        <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid', borderColor: 'divider' }}>
          <Typography variant="subtitle1" fontWeight={700}>Unified Messages</Typography>
          <Tooltip title="Create Class Group Chat">
            <IconButton size="small" onClick={handleOpenCreate} sx={{ bgcolor: 'primary.50', color: 'primary.main', '&:hover': { bgcolor: 'primary.100' } }}>
              <AddRoundedIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
        <List sx={{ flex: 1, overflowY: 'auto', p: 0 }}>
          {loadingChannels ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}><CircularProgress size={24} /></Box>
          ) : channels.length === 0 ? (
            <Typography variant="body2" color="text.secondary" sx={{ p: 2, textAlign: 'center' }}>No conversations yet.</Typography>
          ) : (
            channels.map(channel => (
              <React.Fragment key={channel._id}>
                <ListItem
                  button
                  selected={activeChannel?._id === channel._id}
                  onClick={() => setActiveChannel(channel)}
                  sx={{
                    py: 1.5,
                    '&.Mui-selected': { bgcolor: 'primary.50', '&:hover': { bgcolor: 'primary.100' } }
                  }}
                >
                  <ListItemAvatar>
                    <Avatar sx={{ bgcolor: getChannelColor(channel.type), width: 40, height: 40 }}>
                      {getChannelIcon(channel.type)}
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={<Typography variant="subtitle2" fontWeight={activeChannel?._id === channel._id ? 700 : 500}>{channel.name}</Typography>}
                    secondary={<Typography variant="caption" color="text.secondary" sx={{ textTransform: 'capitalize' }}>
                      {channel.type.replace('_', ' ')} • {channel.members ? `${channel.members.length} members` : 'Course Global'}
                    </Typography>}
                  />
                </ListItem>
                <Divider component="li" />
              </React.Fragment>
            ))
          )}
        </List>
      </Box>

      {/* Chat Window */}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', bgcolor: '#f8fafc' }}>
        {activeChannel ? (
          <>
            <Box sx={{ p: 2, bgcolor: 'background.paper', borderBottom: '1px solid', borderColor: 'divider', display: 'flex', alignItems: 'center', gap: 2 }}>
              <Avatar sx={{ bgcolor: getChannelColor(activeChannel.type) }}>
                {getChannelIcon(activeChannel.type)}
              </Avatar>
              <Box>
                <Typography variant="subtitle1" fontWeight={700}>{activeChannel.name}</Typography>
                <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'capitalize' }}>
                  {activeChannel.type.replace('_', ' ')}
                </Typography>
              </Box>
            </Box>

            <Box sx={{ flex: 1, overflowY: 'auto', p: 3, display: 'flex', flexDirection: 'column', gap: 2 }}>
              {loadingMessages ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', flex: 1, alignItems: 'center' }}><CircularProgress /></Box>
              ) : messages.length === 0 ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', flex: 1, alignItems: 'center' }}>
                  <Typography variant="body2" color="text.secondary">No messages yet.</Typography>
                </Box>
              ) : (
                messages.map((msg) => {
                  const isMe = String(msg.sender_id) === TEACHER_ID || msg.sender_role === 'instructor';
                  return (
                    <Box key={msg._id} sx={{ display: 'flex', flexDirection: 'column', alignItems: isMe ? 'flex-end' : 'flex-start' }}>
                      {!isMe && (
                        <Typography variant="caption" color="text.secondary" sx={{ ml: 1, mb: 0.5 }}>
                          {msg.sender_role === 'student' ? `Student ${msg.sender_id}` : msg.sender_role}
                        </Typography>
                      )}
                      <Box
                        sx={{
                          maxWidth: '70%',
                          p: 1.5,
                          borderRadius: 2,
                          bgcolor: isMe ? 'primary.main' : 'background.paper',
                          color: isMe ? 'primary.contrastText' : 'text.primary',
                          boxShadow: '0 1px 2px rgba(0,0,0,0.1)'
                        }}
                      >
                        <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{msg.content}</Typography>
                      </Box>
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, px: 1 }}>
                        {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </Typography>
                    </Box>
                  );
                })
              )}
              <div ref={messagesEndRef} />
            </Box>

            <Box sx={{ p: 2, bgcolor: 'background.paper', borderTop: '1px solid', borderColor: 'divider' }}>
              <form onSubmit={handleSendMessage} style={{ display: 'flex', gap: 12 }}>
                <TextField
                  fullWidth
                  placeholder="Type a message..."
                  variant="outlined"
                  size="small"
                  value={inputMessage}
                  onChange={e => setInputMessage(e.target.value)}
                  sx={{ '& .MuiOutlinedInput-root': { borderRadius: 3 } }}
                />
                <IconButton
                  type="submit"
                  color="primary"
                  disabled={!inputMessage.trim()}
                  sx={{ bgcolor: 'primary.50', '&:hover': { bgcolor: 'primary.100' } }}
                >
                  <SendRoundedIcon />
                </IconButton>
              </form>
            </Box>
          </>
        ) : (
          <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Typography color="text.secondary">Select a conversation to start chatting.</Typography>
          </Box>
        )}
      </Box>

      <Dialog open={isCreating} onClose={() => setIsCreating(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create Class Group Chat</DialogTitle>
        <DialogContent dividers>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Select a class to create a real-time group chat.
          </Typography>
          <Autocomplete
            options={classGroups}
            getOptionLabel={(option) => `Class ${option.class_name} (${option.members.length} students)`}
            value={selectedGroup}
            onChange={(_, val) => setSelectedGroup(val)}
            renderInput={(params) => <TextField {...params} label="Select Class" size="small" />}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setIsCreating(false)} color="inherit">Cancel</Button>
          <Button onClick={handleConfirmCreate} variant="contained" disabled={!selectedGroup}>Create Group</Button>
        </DialogActions>
      </Dialog>
    </Card>
  );
}
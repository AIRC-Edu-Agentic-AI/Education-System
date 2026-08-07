import React, { useState, useEffect, useRef } from 'react';
import {
  Box, Card, Typography, TextField, IconButton, List, ListItem,
  ListItemText, ListItemAvatar, Avatar, Divider, CircularProgress,
  Dialog, DialogTitle, DialogContent, DialogActions, Button,
  Autocomplete, Tooltip, Chip, Checkbox, Tabs, Tab
} from '@mui/material';
import SendRoundedIcon from '@mui/icons-material/SendRounded';
import AddRoundedIcon from '@mui/icons-material/AddRounded';
import GroupRoundedIcon from '@mui/icons-material/GroupRounded';
import PersonRoundedIcon from '@mui/icons-material/PersonRounded';
import CampaignRoundedIcon from '@mui/icons-material/CampaignRounded';
import ForumRoundedIcon from '@mui/icons-material/ForumRounded';

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
  
  const [openNewChatDialog, setOpenNewChatDialog] = useState(false);
  const [students, setStudents] = useState<{ id_student: number; name: string }[]>([]);
  const [loadingStudents, setLoadingStudents] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStudentIds, setSelectedStudentIds] = useState<(string | number)[]>([]);
  const [groupName, setGroupName] = useState('');
  const [dialogMode, setDialogMode] = useState<'private' | 'group'>('private');
  
  const ws = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const activeChannelRef = useRef<Channel | null>(null);

  const TEACHER_ID = "teacher_admin";
  const courseCode = module && presentation ? `${module} ${presentation}` : '';

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
    activeChannelRef.current = activeChannel;
    if (activeChannel) {
      fetchMessages(activeChannel._id);
      const pollTimer = setInterval(() => {
        if (activeChannelRef.current?._id === activeChannel._id) {
          fetchMessages(activeChannel._id);
        }
      }, 4000);
      return () => clearInterval(pollTimer);
    }
  }, [activeChannel]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (openNewChatDialog && courseCode) {
      const fetchStudents = async () => {
        setLoadingStudents(true);
        try {
          const [m, p] = courseCode.split(' ');
          const res = await fetch(`${API_BASE}/course/${m}/${p}/students-lite`);
          const data = await res.json();
          setStudents(data.students || []);
        } catch (e) {
          console.error("Error fetching students list", e);
        } finally {
          setLoadingStudents(false);
        }
      };
      fetchStudents();
    }
  }, [openNewChatDialog, courseCode]);

  const getChannelDisplayName = (c: Channel) => {
    if (c.type === 'private_message' && c.members) {
      const studentId = c.members.find(m => String(m) !== TEACHER_ID);
      if (studentId && !c.name.includes('#')) {
        return `${c.name} (#${studentId})`;
      }
    }
    return c.name;
  };

  const handleStartPrivateChat = async (studentId: string | number, studentName: string) => {
    const sidStr = String(studentId);
    const existing = channels.find(c => 
      c.type === 'private_message' && 
      c.members?.some(m => String(m) === sidStr)
    );
    if (existing) {
      setActiveChannel(existing);
      setOpenNewChatDialog(false);
      return;
    }
    
    try {
      const displayName = `${studentName} (#${sidStr})`;
      const res = await fetch(`${BASE_URL}/realtime-chat/channels`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: displayName,
          course_code: courseCode,
          members: [TEACHER_ID, sidStr],
          type: 'private_message'
        })
      });
      if (res.ok) {
        const newChan = await res.json();
        setChannels(prev => {
          if (prev.some(c => c._id === newChan._id)) return prev;
          return [newChan, ...prev];
        });
        setActiveChannel(newChan);
        setOpenNewChatDialog(false);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleCreateGroupChat = async () => {
    if (!groupName.trim() || selectedStudentIds.length === 0) return;
    try {
      const res = await fetch(`${BASE_URL}/realtime-chat/channels`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: groupName.trim(),
          course_code: courseCode,
          members: [TEACHER_ID, ...selectedStudentIds.map(String)],
          type: 'private_group'
        })
      });
      if (res.ok) {
        const newChan = await res.json();
        setChannels(prev => [newChan, ...prev]);
        setActiveChannel(newChan);
        setOpenNewChatDialog(false);
        setGroupName('');
        setSelectedStudentIds([]);
      }
    } catch (e) {
      console.error(e);
    }
  };

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
            const currentChannel = activeChannelRef.current;
            if (currentChannel && newMsg.channel_id === currentChannel._id) {
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
      const data: Channel[] = await res.json();
      
      const uniqueChannels: Channel[] = [];
      const seenIds = new Set<string>();
      const seenPrivateKeys = new Set<string>();
      
      for (const c of data) {
        if (seenIds.has(c._id)) continue;
        seenIds.add(c._id);
        
        if (c.type === 'private_message' || c.type === 'private_group') {
          const memsKey = (c.members || []).map(String).sort().join('|');
          if (memsKey && seenPrivateKeys.has(memsKey)) continue;
          if (memsKey) seenPrivateKeys.add(memsKey);
        }
        
        uniqueChannels.push(c);
      }

      setChannels(uniqueChannels);
      if (uniqueChannels.length > 0 && !activeChannel) {
        setActiveChannel(uniqueChannels[0]);
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



  const getChannelIcon = (type: string) => {
    switch (type) {
      case 'announcement': return <CampaignRoundedIcon />;
      case 'discussion': return <ForumRoundedIcon />;
      case 'class_group': return <GroupRoundedIcon />;
      case 'private_group': return <GroupRoundedIcon />;
      case 'private_message': return <PersonRoundedIcon />;
      default: return <PersonRoundedIcon />;
    }
  };
  const getChannelColor = (type: string) => {
    switch (type) {
      case 'announcement': return 'error.main';
      case 'discussion': return 'success.main';
      case 'class_group': return 'primary.main';
      case 'private_group': return 'info.main';
      case 'private_message': return 'secondary.main';
      default: return 'secondary.main';
    }
  };

  return (
    <Card sx={{ display: 'flex', height: 'calc(100vh - 160px)', minHeight: 500, borderRadius: 2, boxShadow: '0 4px 20px rgba(0,0,0,0.05)', overflow: 'hidden' }}>
      {/* Sidebar */}
      <Box sx={{ width: 320, borderRight: '1px solid', borderColor: 'divider', display: 'flex', flexDirection: 'column', bgcolor: 'background.paper' }}>
        <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid', borderColor: 'divider' }}>
          <Typography variant="subtitle1" fontWeight={700}>Unified Messages</Typography>
          <Tooltip title="New Chat / Group">
            <IconButton size="small" onClick={() => setOpenNewChatDialog(true)}>
              <AddRoundedIcon />
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
                    primary={<Typography variant="subtitle2" fontWeight={activeChannel?._id === channel._id ? 700 : 500}>{getChannelDisplayName(channel)}</Typography>}
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
                <Typography variant="subtitle1" fontWeight={700}>{getChannelDisplayName(activeChannel)}</Typography>
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

      {/* Dialog for New Chat / Group */}
      <Dialog 
        open={openNewChatDialog} 
        onClose={() => {
          setOpenNewChatDialog(false);
          setSearchQuery('');
          setSelectedStudentIds([]);
          setGroupName('');
        }}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ pb: 1 }}>
          <Typography variant="h6" fontWeight={700}>New Conversation</Typography>
          <Tabs 
            value={dialogMode === 'private' ? 0 : 1} 
            onChange={(_, v) => {
              setDialogMode(v === 0 ? 'private' : 'group');
              setSearchQuery('');
              setSelectedStudentIds([]);
            }}
            sx={{ mt: 1, borderBottom: 1, borderColor: 'divider' }}
          >
            <Tab label="Private Message" />
            <Tab label="Group Chat" />
          </Tabs>
        </DialogTitle>
        <DialogContent sx={{ p: 2, maxHeight: 400, overflowY: 'auto' }}>
          {dialogMode === 'group' && (
            <TextField
              fullWidth
              label="Group Name"
              placeholder="Enter group name..."
              size="small"
              value={groupName}
              onChange={e => setGroupName(e.target.value)}
              sx={{ mb: 2, mt: 1 }}
            />
          )}

          <TextField
            fullWidth
            placeholder="Search students by name or ID..."
            size="small"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            sx={{ mb: 2, mt: dialogMode === 'private' ? 1 : 0 }}
          />

          {loadingStudents ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress size={24} />
            </Box>
          ) : (
            <List>
              {students
                .filter(s => 
                  s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                  String(s.id_student).includes(searchQuery)
                )
                .map(student => {
                  const isSelected = selectedStudentIds.includes(student.id_student);
                  return (
                    <ListItem 
                      key={student.id_student}
                      button
                      onClick={() => {
                        if (dialogMode === 'private') {
                          handleStartPrivateChat(student.id_student, student.name);
                        } else {
                          setSelectedStudentIds(prev => 
                            prev.includes(student.id_student)
                              ? prev.filter(id => id !== student.id_student)
                              : [...prev, student.id_student]
                          );
                        }
                      }}
                      sx={{ borderRadius: 1, mb: 0.5 }}
                    >
                      {dialogMode === 'group' && (
                        <Checkbox 
                          checked={isSelected}
                          edge="start"
                          disableRipple
                        />
                      )}
                      <ListItemAvatar>
                        <Avatar sx={{ bgcolor: 'secondary.main', width: 32, height: 32, fontSize: 13 }}>
                          <PersonRoundedIcon sx={{ fontSize: 18 }} />
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText 
                        primary={student.name} 
                        secondary={`ID: ${student.id_student}`}
                      />
                    </ListItem>
                  );
                })}
            </List>
          )}
        </DialogContent>
        <DialogActions sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
          <Button 
            onClick={() => {
              setOpenNewChatDialog(false);
              setSearchQuery('');
              setSelectedStudentIds([]);
              setGroupName('');
            }}
          >
            Cancel
          </Button>
          {dialogMode === 'group' && (
            <Button 
              variant="contained" 
              color="primary"
              disabled={!groupName.trim() || selectedStudentIds.length === 0}
              onClick={handleCreateGroupChat}
            >
              Create Group ({selectedStudentIds.length})
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Card>
  );
}

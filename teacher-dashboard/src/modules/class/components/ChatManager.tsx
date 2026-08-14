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
  const [students, setStudents] = useState<{ id_student: number; name: string; tier?: number; age?: string; imd_band?: string }[]>([]);
  const [loadingStudents, setLoadingStudents] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStudentIds, setSelectedStudentIds] = useState<(string | number)[]>([]);
  const [groupName, setGroupName] = useState('');
  const [dialogMode, setDialogMode] = useState<'private' | 'group' | 'tier_broadcast'>('private');
  const [tierFilter, setTierFilter] = useState<'all' | '1' | '2' | '3'>('all');
  const [broadcastTier, setBroadcastTier] = useState<'1' | '2' | '3'>('3');
  const [broadcastTitle, setBroadcastTitle] = useState('');
  const [broadcastContent, setBroadcastContent] = useState('');
  const [isBroadcasting, setIsBroadcasting] = useState(false);
  
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
      // Fallback polling only when WebSocket is disconnected
      const pollTimer = setInterval(() => {
        if (activeChannelRef.current?._id === activeChannel._id && (!ws.current || ws.current.readyState !== WebSocket.OPEN)) {
          fetchMessages(activeChannel._id);
        }
      }, 15000);
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
          <Typography variant="h6" fontWeight={700}>Conversations & Study Groups</Typography>
          <Tabs 
            value={dialogMode === 'private' ? 0 : dialogMode === 'group' ? 1 : 2} 
            onChange={(_, v) => {
              setDialogMode(v === 0 ? 'private' : v === 1 ? 'group' : 'tier_broadcast');
              setSearchQuery('');
              setSelectedStudentIds([]);
            }}
            sx={{ mt: 1, borderBottom: 1, borderColor: 'divider' }}
          >
            <Tab label="Direct Message" sx={{ textTransform: 'none', fontSize: 13, fontWeight: 600 }} />
            <Tab label="Group Chat by Tier" sx={{ textTransform: 'none', fontSize: 13, fontWeight: 600 }} />
            <Tab label="📢 Broadcast to Tier" sx={{ textTransform: 'none', fontSize: 13, fontWeight: 600 }} />
          </Tabs>
        </DialogTitle>
        <DialogContent sx={{ p: 2, maxHeight: 450, overflowY: 'auto' }}>
          {dialogMode === 'tier_broadcast' ? (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
              <Box>
                <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600, display: 'block', mb: 0.75 }}>
                  SELECT TARGET RISK TIER:
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  <Chip
                    label={`Tier 3 — High Risk (${students.filter(s => (s.tier || 1) === 3).length} Students)`}
                    size="small"
                    onClick={() => {
                      setBroadcastTier('3');
                      setBroadcastTitle('[ACADEMIC WARNING] Support & Academic Improvement Guidance');
                      setBroadcastContent('Dear Tier 3 students,\n\nThe instructor noticed that your course progress needs improvement. Please reach out to your Instructor or Academic Advisor this week for personalized learning assistance!\n\nBest regards,\nTeaching Team');
                    }}
                    color={broadcastTier === '3' ? 'error' : 'default'}
                    variant={broadcastTier === '3' ? 'filled' : 'outlined'}
                    sx={{ fontWeight: 600, fontSize: 11 }}
                  />
                  <Chip
                    label={`Tier 2 — Moderate (${students.filter(s => (s.tier || 1) === 2).length} Students)`}
                    size="small"
                    onClick={() => {
                      setBroadcastTier('2');
                      setBroadcastTitle('[PROGRESS REMINDER] Review Schedule & Assessment Submissions');
                      setBroadcastContent('Dear Tier 2 students,\n\nPlease check upcoming assessment deadlines and dedicate time to review key lecture topics. If you encounter any difficulties, feel free to ask in the Discussion forum!\n\nBest of luck!');
                    }}
                    color={broadcastTier === '2' ? 'warning' : 'default'}
                    variant={broadcastTier === '2' ? 'filled' : 'outlined'}
                    sx={{ fontWeight: 600, fontSize: 11 }}
                  />
                  <Chip
                    label={`Tier 1 — Low Risk (${students.filter(s => (s.tier || 1) === 1).length} Students)`}
                    size="small"
                    onClick={() => {
                      setBroadcastTier('1');
                      setBroadcastTitle('[COMMENDATION] Outstanding Performance & Advanced Resources');
                      setBroadcastContent('Dear Tier 1 students,\n\nThe Teaching Team commends your active participation and strong performance. In-depth materials and extension exercises have been published on the portal for your further study.\n\nKeep up the great work!');
                    }}
                    color={broadcastTier === '1' ? 'success' : 'default'}
                    variant={broadcastTier === '1' ? 'filled' : 'outlined'}
                    sx={{ fontWeight: 600, fontSize: 11 }}
                  />
                </Box>
              </Box>

              <TextField
                fullWidth
                size="small"
                label="Message Title"
                value={broadcastTitle}
                onChange={e => setBroadcastTitle(e.target.value)}
                placeholder="Enter title..."
              />
              <TextField
                fullWidth
                multiline
                rows={5}
                size="small"
                label="Detailed Message Content"
                value={broadcastContent}
                onChange={e => setBroadcastContent(e.target.value)}
                placeholder="Enter message body..."
              />
            </Box>
          ) : (
            <>
              {dialogMode === 'group' && (
                <Box sx={{ mb: 2, mt: 1, display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                  <TextField
                    fullWidth
                    label="Group Name"
                    placeholder="Enter group name..."
                    size="small"
                    value={groupName}
                    onChange={e => setGroupName(e.target.value)}
                  />

                  {/* Quick Tier Group Preset Selection */}
                  <Box sx={{ bgcolor: 'action.hover', p: 1.25, borderRadius: 1.5 }}>
                    <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600, display: 'block', mb: 0.75 }}>
                      ⚡ QUICK GROUPING BY TIER:
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 0.75, flexWrap: 'wrap' }}>
                      <Button
                        size="small"
                        variant="outlined"
                        color="error"
                        onClick={() => {
                          const t3 = students.filter(s => (s.tier || 1) === 3);
                          setSelectedStudentIds(t3.map(s => s.id_student));
                          setGroupName(`Academic Support Group — Tier 3 (${courseCode})`);
                        }}
                        sx={{ fontSize: 11, textTransform: 'none', py: 0.25 }}
                      >
                        Select All Tier 3 ({students.filter(s => (s.tier || 1) === 3).length} Students)
                      </Button>
                      <Button
                        size="small"
                        variant="outlined"
                        color="warning"
                        onClick={() => {
                          const t2 = students.filter(s => (s.tier || 1) === 2);
                          setSelectedStudentIds(t2.map(s => s.id_student));
                          setGroupName(`Core Review Group — Tier 2 (${courseCode})`);
                        }}
                        sx={{ fontSize: 11, textTransform: 'none', py: 0.25 }}
                      >
                        Select All Tier 2 ({students.filter(s => (s.tier || 1) === 2).length} Students)
                      </Button>
                      <Button
                        size="small"
                        variant="outlined"
                        color="success"
                        onClick={() => {
                          const t1 = students.filter(s => (s.tier || 1) === 1);
                          setSelectedStudentIds(t1.map(s => s.id_student));
                          setGroupName(`Advanced Research Group — Tier 1 (${courseCode})`);
                        }}
                        sx={{ fontSize: 11, textTransform: 'none', py: 0.25 }}
                      >
                        Select All Tier 1 ({students.filter(s => (s.tier || 1) === 1).length} Students)
                      </Button>
                    </Box>
                  </Box>
                </Box>
              )}

              {/* Filter bar by Tier */}
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5, flexWrap: 'wrap' }}>
                <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600 }}>Filter Tier:</Typography>
                <Chip label="All" size="small" onClick={() => setTierFilter('all')} color={tierFilter === 'all' ? 'primary' : 'default'} variant={tierFilter === 'all' ? 'filled' : 'outlined'} sx={{ height: 22, fontSize: 10, fontWeight: 600 }} />
                <Chip label="Tier 3 (High)" size="small" onClick={() => setTierFilter('3')} color={tierFilter === '3' ? 'error' : 'default'} variant={tierFilter === '3' ? 'filled' : 'outlined'} sx={{ height: 22, fontSize: 10, fontWeight: 600 }} />
                <Chip label="Tier 2 (Moderate)" size="small" onClick={() => setTierFilter('2')} color={tierFilter === '2' ? 'warning' : 'default'} variant={tierFilter === '2' ? 'filled' : 'outlined'} sx={{ height: 22, fontSize: 10, fontWeight: 600 }} />
                <Chip label="Tier 1 (Low)" size="small" onClick={() => setTierFilter('1')} color={tierFilter === '1' ? 'success' : 'default'} variant={tierFilter === '1' ? 'filled' : 'outlined'} sx={{ height: 22, fontSize: 10, fontWeight: 600 }} />
              </Box>

              <TextField
                fullWidth
                placeholder="Search by student name or ID..."
                size="small"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                sx={{ mb: 1 }}
              />

              {loadingStudents ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                  <CircularProgress size={24} />
                </Box>
              ) : (
                <List sx={{ maxHeight: 260, overflowY: 'auto' }}>
                  {students
                    .filter(s => {
                      if (tierFilter !== 'all' && String(s.tier || 1) !== tierFilter) return false;
                      if (!searchQuery) return true;
                      return (
                        s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                        String(s.id_student).includes(searchQuery)
                      );
                    })
                    .map(student => {
                      const isSelected = selectedStudentIds.includes(student.id_student);
                      const sTier = student.tier || 1;
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
                          sx={{ borderRadius: 1, mb: 0.5, border: '1px solid', borderColor: 'divider' }}
                        >
                          {dialogMode === 'group' && (
                            <Checkbox 
                              checked={isSelected}
                              edge="start"
                              disableRipple
                              size="small"
                            />
                          )}
                          <ListItemAvatar sx={{ minWidth: 40 }}>
                            <Avatar sx={{ bgcolor: sTier === 3 ? 'error.main' : sTier === 2 ? 'warning.main' : 'primary.main', width: 28, height: 28, fontSize: 11 }}>
                              <PersonRoundedIcon sx={{ fontSize: 16 }} />
                            </Avatar>
                          </ListItemAvatar>
                          <ListItemText 
                            primary={
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Typography variant="body2" fontWeight={600}>{student.name}</Typography>
                                <Chip
                                  label={`Tier ${sTier}`}
                                  size="small"
                                  color={sTier === 3 ? 'error' : sTier === 2 ? 'warning' : 'success'}
                                  sx={{ height: 18, fontSize: 9, fontWeight: 700 }}
                                />
                              </Box>
                            } 
                            secondary={`ID: #${student.id_student} • Age: ${student.age || '21'} • IMD: ${student.imd_band || '20-30%'}`}
                            secondaryTypographyProps={{ fontSize: 11 }}
                          />
                        </ListItem>
                      );
                    })}
                </List>
              )}
            </>
          )}
        </DialogContent>
        <DialogActions sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
          <Button 
            onClick={() => {
              setOpenNewChatDialog(false);
              setSearchQuery('');
              setSelectedStudentIds([]);
              setGroupName('');
              setBroadcastTitle('');
              setBroadcastContent('');
            }}
            color="inherit"
          >
            Cancel
          </Button>

          {dialogMode === 'tier_broadcast' && (
            <Button
              variant="contained"
              color={broadcastTier === '3' ? 'error' : broadcastTier === '2' ? 'warning' : 'primary'}
              disabled={!broadcastTitle.trim() || !broadcastContent.trim() || isBroadcasting}
              onClick={async () => {
                setIsBroadcasting(true);
                try {
                  const tNum = parseInt(broadcastTier);
                  const targetList = students.filter(s => (s.tier || 1) === tNum);
                  const targetIds = targetList.map(s => s.id_student);
                  
                  const res = await fetch(`${BASE_URL}/notify/broadcast`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                      student_ids: targetIds,
                      type: tNum === 3 ? 'academic_warning' : tNum === 2 ? 'study_reminder' : 'general_notice',
                      title: broadcastTitle,
                      content: broadcastContent,
                      sender_role: 'instructor',
                      course_code: courseCode,
                    })
                  });
                  if (res.ok) {
                    alert(`Successfully sent message to all ${targetIds.length} students in Tier ${broadcastTier}!`);
                    setOpenNewChatDialog(false);
                    setBroadcastTitle('');
                    setBroadcastContent('');
                    fetchChannels();
                  }
                } catch (e) {
                  console.error(e);
                  alert("Failed to send message broadcast.");
                } finally {
                  setIsBroadcasting(false);
                }
              }}
              startIcon={isBroadcasting ? <CircularProgress size={14} color="inherit" /> : <SendRoundedIcon fontSize="small" />}
              sx={{ fontWeight: 600, textTransform: 'none' }}
            >
              {isBroadcasting ? 'Sending...' : `Send to all Tier ${broadcastTier} (${students.filter(s => (s.tier || 1) === parseInt(broadcastTier)).length} Students)`}
            </Button>
          )}

          {dialogMode === 'group' && (
            <Button 
              variant="contained" 
              color="primary"
              disabled={!groupName.trim() || selectedStudentIds.length === 0}
              onClick={handleCreateGroupChat}
              sx={{ fontWeight: 600, textTransform: 'none' }}
            >
              Create Group ({selectedStudentIds.length} Students)
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Card>
  );
}

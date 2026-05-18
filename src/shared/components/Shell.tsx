import React from 'react'
import {
  Box, Drawer, List, ListItemButton, ListItemIcon, ListItemText,
  Toolbar, Typography, Divider, Chip, Tooltip, IconButton,
} from '@mui/material'
import { useLocation, useNavigate } from 'react-router-dom'
import ChatIcon from '@mui/icons-material/ChatBubbleOutlineRounded'
import { moduleRegistry } from '../../modules/registry'
import { useContextStore } from '../stores/contextStore'
import { ChatPanel } from '../../modules/chat/components/ChatPanel'
import { ContextBar } from './ContextBar'

const DRAWER_WIDTH   = 220
const CHAT_WIDTH     = 360

export function Shell({ children }: { children: React.ReactNode }) {
  const location  = useLocation()
  const navigate  = useNavigate()
  const { selectedModule, selectedPresentation, currentWeek, activeStudent, chatPanelOpen, setChatPanelOpen } = useContextStore()

  const hasData = selectedModule && selectedPresentation

  return (
    <Box sx={{ display: 'flex', height: '100vh', bgcolor: '#F4F3F0' }}>
      {/* Left nav */}
      <Drawer
        variant="permanent"
        sx={{
          width: DRAWER_WIDTH,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: DRAWER_WIDTH,
            bgcolor: '#0A1628',
            color: '#C8C6BE',
            border: 'none',
            display: 'flex',
            flexDirection: 'column',
          },
        }}
      >
        <Toolbar sx={{ px: 2, py: 1.5, minHeight: '60px !important' }}>
          <Box>
            <Typography
              sx={{
                fontFamily: '"IBM Plex Mono", monospace',
                fontSize: 13,
                fontWeight: 500,
                color: '#fff',
                letterSpacing: '0.04em',
              }}
            >
              RTI / MTSS
            </Typography>
            <Typography sx={{ fontSize: 11, color: '#6B7280', fontFamily: '"IBM Plex Mono", monospace' }}>
              Teacher Dashboard
            </Typography>
          </Box>
        </Toolbar>

        <Divider sx={{ borderColor: '#1E2D45' }} />

        {/* Context badge */}
        {hasData && (
          <Box sx={{ px: 2, py: 1.5 }}>
            <Typography sx={{ fontSize: 10, color: '#4B5563', mb: 0.5, fontFamily: '"IBM Plex Mono", monospace', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              Active context
            </Typography>
            <Chip
              label={`${selectedModule} · ${selectedPresentation}`}
              size="small"
              sx={{ bgcolor: '#1D9E7522', color: '#5DCAA5', fontSize: 11, fontFamily: '"IBM Plex Mono", monospace', height: 22 }}
            />
            <Typography sx={{ fontSize: 11, color: '#6B7280', mt: 0.5, fontFamily: '"IBM Plex Mono", monospace' }}>
              Week {currentWeek}
            </Typography>
            {activeStudent && (
              <Chip
                label={`Student #${activeStudent.id_student}`}
                size="small"
                sx={{ mt: 0.5, bgcolor: '#BA751722', color: '#EF9F27', fontSize: 11, fontFamily: '"IBM Plex Mono", monospace', height: 22 }}
              />
            )}
          </Box>
        )}

        <Divider sx={{ borderColor: '#1E2D45' }} />

        {/* Navigation */}
        <List dense sx={{ px: 1, py: 1, flexGrow: 1 }}>
          {moduleRegistry.map((mod) => {
            const active = location.pathname === '/' ? mod.path === '/' : location.pathname.startsWith(mod.path) && mod.path !== '/'
            return (
              <Tooltip
                key={mod.id}
                title={!hasData && mod.id !== 'dashboard' ? 'Select a module first' : ''}
                placement="right"
              >
                <span>
                  <ListItemButton
                    disabled={!hasData && mod.id !== 'dashboard'}
                    onClick={() => navigate(mod.path)}
                    sx={{
                      borderRadius: 1.5,
                      mb: 0.5,
                      bgcolor: active ? '#1D9E7514' : 'transparent',
                      borderLeft: active ? '2px solid #1D9E75' : '2px solid transparent',
                      '&:hover': { bgcolor: '#1E2D45' },
                      '&.Mui-disabled': { opacity: 0.4 },
                    }}
                  >
                    <ListItemIcon sx={{ minWidth: 32, color: active ? '#5DCAA5' : '#6B7280' }}>
                      {mod.icon}
                    </ListItemIcon>
                    <ListItemText
                      primary={mod.label}
                      primaryTypographyProps={{
                        fontSize: 13,
                        fontFamily: '"IBM Plex Sans", sans-serif',
                        color: active ? '#fff' : '#9CA3AF',
                        fontWeight: active ? 500 : 400,
                      }}
                    />
                  </ListItemButton>
                </span>
              </Tooltip>
            )
          })}
        </List>

        <Divider sx={{ borderColor: '#1E2D45' }} />

        {/* AI Advisor toggle */}
        <Box sx={{ px: 1, py: 1 }}>
          <ListItemButton
            onClick={() => setChatPanelOpen(!chatPanelOpen)}
            sx={{
              borderRadius: 1.5,
              bgcolor: chatPanelOpen ? '#1D9E7514' : 'transparent',
              borderLeft: chatPanelOpen ? '2px solid #1D9E75' : '2px solid transparent',
              '&:hover': { bgcolor: '#1E2D45' },
            }}
          >
            <ListItemIcon sx={{ minWidth: 32, color: chatPanelOpen ? '#5DCAA5' : '#6B7280' }}>
              <ChatIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText
              primary="AI advisor"
              primaryTypographyProps={{
                fontSize: 13,
                fontFamily: '"IBM Plex Sans", sans-serif',
                color: chatPanelOpen ? '#fff' : '#9CA3AF',
                fontWeight: chatPanelOpen ? 500 : 400,
              }}
            />
          </ListItemButton>
        </Box>

        <Divider sx={{ borderColor: '#1E2D45' }} />
        <Box sx={{ px: 2, py: 1.5 }}>
          <Typography sx={{ fontSize: 10, color: '#374151', fontFamily: '"IBM Plex Mono", monospace' }}>
            OULAD · Pilot v0.1
          </Typography>
        </Box>
      </Drawer>

      {/* Main content */}
      <Box component="main" sx={{ flexGrow: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <ContextBar />

        <Box sx={{ flexGrow: 1, overflow: 'hidden', display: 'flex' }}>
          <Box sx={{ flexGrow: 1, overflow: 'auto', display: 'flex', flexDirection: 'column' }}>
            {children}
          </Box>

          {/* Chat panel — always mounted so messages and scroll persist */}
          <Box
            sx={{
              width: chatPanelOpen ? CHAT_WIDTH : 0,
              flexShrink: 0,
              overflow: 'hidden',
              transition: 'width 0.22s ease',
              borderLeft: chatPanelOpen ? '1px solid #E5E3DC' : 'none',
            }}
          >
            <Box sx={{ width: CHAT_WIDTH, height: '100%' }}>
              <ChatPanel />
            </Box>
          </Box>
        </Box>
      </Box>
    </Box>
  )
}

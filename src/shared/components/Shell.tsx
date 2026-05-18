import React from 'react'
import {
  Box, Drawer, List, ListItemButton, ListItemIcon, ListItemText,
  Toolbar, Typography, Divider, Chip, Tooltip,
} from '@mui/material'
import { useLocation, useNavigate } from 'react-router-dom'
import ChatIcon from '@mui/icons-material/ChatBubbleOutlineRounded'
import { tokens } from '../../theme'
import { useAuth0 } from '@auth0/auth0-react'
import { ChatPanel } from '../../modules/chat/components/ChatPanel'
import { ContextBar } from './ContextBar'

const DRAWER_WIDTH = 220
const CHAT_WIDTH   = 360

export function Shell({ children }: { children: React.ReactNode }) {
  const location = useLocation()
  const navigate = useNavigate()
  const { selectedModule, selectedPresentation, currentWeek, activeStudent, chatPanelOpen, setChatPanelOpen } = useContextStore()

  const hasData = selectedModule && selectedPresentation

  return (
    <Box sx={{ display: 'flex', height: '100vh', bgcolor: tokens.surface.default }}>
      <Drawer
        variant="permanent"
        sx={{
          width: DRAWER_WIDTH,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: DRAWER_WIDTH,
            bgcolor: tokens.nav.bg,
            color: tokens.text.onDark,
            border: 'none',
            display: 'flex',
            flexDirection: 'column',
          },
        }}
      >
        <Toolbar sx={{ px: 2, py: 1.5 }}>
          <Box>
            <Typography sx={{ fontFamily: tokens.font.mono, fontSize: 13, fontWeight: 500, color: '#fff', letterSpacing: '0.04em' }}>
              RTI / MTSS
            </Typography>
            <Typography sx={{ fontSize: 11, color: tokens.text.secondary, fontFamily: tokens.font.mono }}>
              Teacher Dashboard
            </Typography>
          </Box>
        </Toolbar>

        <Divider sx={{ borderColor: tokens.nav.divider }} />

        {hasData && (
          <Box sx={{ px: 2, py: 1.5 }}>
            <Typography sx={{ fontSize: 10, color: tokens.text.subdued, mb: 0.5, fontFamily: tokens.font.mono, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              Active context
            </Typography>
            <Chip
              label={`${selectedModule} · ${selectedPresentation}`}
              size="small"
              sx={{ bgcolor: `${tokens.brand.primaryLight}22`, color: tokens.brand.primaryMuted, fontSize: 11, fontFamily: tokens.font.mono, height: 22 }}
            />
            <Typography sx={{ fontSize: 11, color: tokens.text.secondary, mt: 0.5, fontFamily: tokens.font.mono }}>
              Week {currentWeek}
            </Typography>
            {activeStudent && (
              <Chip
                label={`Student #${activeStudent.id_student}`}
                size="small"
                sx={{ mt: 0.5, bgcolor: `${tokens.brand.secondary}22`, color: tokens.brand.secondary, fontSize: 11, fontFamily: tokens.font.mono, height: 22 }}
              />
            )}
          </Box>
        )}

        <Divider sx={{ borderColor: tokens.nav.divider }} />

        <List dense sx={{ px: 1, py: 1, flexGrow: 1 }}>
          {moduleRegistry.map((mod) => {
            const active = location.pathname === '/' ? mod.path === '/' : location.pathname.startsWith(mod.path) && mod.path !== '/'
            return (
              <Tooltip key={mod.id} title={!hasData && mod.id !== 'dashboard' ? 'Select a module first' : ''} placement="right">
                <span>
                  <ListItemButton
                    disabled={!hasData && mod.id !== 'dashboard'}
                    onClick={() => navigate(mod.path)}
                    sx={{
                      borderRadius: 1.5, mb: 0.5,
                      bgcolor: active ? `${tokens.brand.primaryLight}14` : 'transparent',
                      borderLeft: active ? `2px solid ${tokens.brand.primaryLight}` : '2px solid transparent',
                      '&:hover': { bgcolor: tokens.nav.hover },
                      '&.Mui-disabled': { opacity: 0.4 },
                    }}
                  >
                    <ListItemIcon sx={{ minWidth: 32, color: active ? tokens.brand.primaryMuted : tokens.text.secondary }}>
                      {mod.icon}
                    </ListItemIcon>
                    <ListItemText
                      primary={mod.label}
                      primaryTypographyProps={{
                        fontSize: 13,
                        color: active ? '#fff' : tokens.text.muted,
                        fontWeight: active ? 500 : 400,
                      }}
                    />
                  </ListItemButton>
                </span>
              </Tooltip>
            )
          })}
        </List>

        <Divider sx={{ borderColor: tokens.nav.divider }} />

        <Box sx={{ px: 1, py: 1 }}>
          <ListItemButton
            onClick={() => setChatPanelOpen(!chatPanelOpen)}
            sx={{
              borderRadius: 1.5,
              bgcolor: chatPanelOpen ? `${tokens.brand.primaryLight}14` : 'transparent',
              borderLeft: chatPanelOpen ? `2px solid ${tokens.brand.primaryLight}` : '2px solid transparent',
              '&:hover': { bgcolor: tokens.nav.hover },
            }}
          >
            <ListItemIcon sx={{ minWidth: 32, color: chatPanelOpen ? tokens.brand.primaryMuted : tokens.text.secondary }}>
              <ChatIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText
              primary="AI advisor"
              primaryTypographyProps={{
                fontSize: 13,
                color: chatPanelOpen ? '#fff' : tokens.text.muted,
                fontWeight: chatPanelOpen ? 500 : 400,
              }}
            />
          </ListItemButton>
        </Box>

        <Divider sx={{ borderColor: tokens.nav.divider }} />
        <Box sx={{ px: 2, py: 1.5 }}>
          <Typography sx={{ fontSize: 10, color: tokens.text.subdued, fontFamily: tokens.font.mono }}>
            OULAD · Pilot v0.1
          </Typography>
        </Box>
      </Drawer>

      <Box component="main" sx={{ flexGrow: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <ContextBar />

        <Box sx={{ flexGrow: 1, overflow: 'hidden', display: 'flex' }}>
          <Box sx={{ flexGrow: 1, overflow: 'auto', display: 'flex', flexDirection: 'column' }}>
            {children}
          </Box>

          <Box
            sx={{
              width: chatPanelOpen ? CHAT_WIDTH : 0,
              flexShrink: 0,
              overflow: 'hidden',
              transition: 'width 0.22s ease',
              borderLeft: chatPanelOpen ? `1px solid ${tokens.border.default}` : 'none',
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

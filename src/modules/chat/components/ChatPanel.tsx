import { useRef, useEffect, useState } from 'react'
import { Box, Typography, TextField, IconButton, Chip, CircularProgress, Alert, Paper } from '@mui/material'
import SendIcon from '@mui/icons-material/SendRounded'
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutlineRounded'
import CloseIcon from '@mui/icons-material/CloseRounded'
import { tokens } from '../../../theme'
import { container } from '../../../di/container'
import { useContextStore } from '../../../shared/stores/contextStore'
import { useChatStore } from '../../../shared/stores/chatStore'
import { MessageBubble } from './MessageBubble'
import { useQuery } from '@tanstack/react-query'
import type { AgentContext, ChatMessage, StudentProfile } from '../../../types/domain'

function buildContext(
  module: string, presentation: string, currentWeek: number, numWeeks: number,
  activeStudent: StudentProfile | null,
  students: { risk_by_week: (number | null)[]; tier_by_week: (1|2|3|null)[] }[]
): AgentContext {
  const weekIdx = Math.max(0, currentWeek - 1)
  const tierCounts = { tier1: 0, tier2: 0, tier3: 0 }
  for (const s of students) {
    const tier = s.tier_by_week[weekIdx] ?? 1
    if (tier === 1) tierCounts.tier1++
    else if (tier === 2) tierCounts.tier2++
    else tierCounts.tier3++
  }
  return { module, presentation, currentWeek, numWeeks, activeStudent, tierCounts }
}

const SUGGESTED_PROMPTS = [
  'Which Tier 3 students need immediate intervention?',
  'Recommend interventions for Tier 2 students.',
  'Summarise engagement patterns this week.',
  'Which students show improving trajectories?',
]

export function ChatPanel() {
  const { selectedModule, selectedPresentation, currentWeek, numWeeks, activeStudent, setChatPanelOpen } = useContextStore()
  const { messages, isStreaming, addMessage, appendToLast, setStreaming, clearMessages } = useChatStore()
  const [input, setInput] = useState('')
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  const { data: course } = useQuery({
    queryKey: ['course', selectedModule, selectedPresentation],
    queryFn: () => container.dataService.getCourse(selectedModule, selectedPresentation),
    enabled: !!selectedModule && !!selectedPresentation,
  })

  const students = course?.students ?? []

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async (text: string) => {
    if (!text.trim() || isStreaming) return
    setError(null)
    setInput('')

    const userMsg: ChatMessage = { id: crypto.randomUUID(), role: 'user', content: text.trim(), timestamp: new Date() }
    addMessage(userMsg)
    addMessage({ id: crypto.randomUUID(), role: 'assistant', content: '', timestamp: new Date() })
    setStreaming(true)

    try {
      const ctx = buildContext(selectedModule, selectedPresentation, currentWeek, numWeeks, activeStudent, students)
      for await (const chunk of container.agentService.stream([...messages, userMsg], ctx)) {
        appendToLast(chunk)
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
      appendToLast('\n\n[Error: Could not complete response]')
    } finally {
      setStreaming(false)
    }
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', bgcolor: tokens.surface.paper }}>
      {/* Header */}
      <Box sx={{
        px: 2, py: 1.5, borderBottom: `1px solid ${tokens.border.default}`,
        display: 'flex', alignItems: 'center', gap: 1, minHeight: 52, flexShrink: 0,
      }}>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Typography sx={{ fontSize: 13, fontWeight: 500, color: tokens.text.primary }}>
            AI Advisor
          </Typography>
          <Box sx={{ display: 'flex', gap: 0.5, mt: 0.25, flexWrap: 'wrap' }}>
            {selectedModule && (
              <Chip label={`${selectedModule} · Wk ${currentWeek}`} size="small"
                sx={{ bgcolor: tokens.brand.primarySubtle, color: tokens.brand.primary, fontSize: 10, height: 18 }} />
            )}
            {activeStudent && (
              <Chip label={`#${activeStudent.id_student}`} size="small"
                onDelete={() => useContextStore.getState().setActiveStudent(null)}
                sx={{ bgcolor: tokens.brand.secondarySubtle, color: tokens.brand.secondaryText, fontSize: 10, height: 18 }} />
            )}
          </Box>
        </Box>
        <IconButton size="small" onClick={clearMessages} title="Clear conversation" sx={{ color: tokens.text.muted }}>
          <DeleteOutlineIcon sx={{ fontSize: 16 }} />
        </IconButton>
        <IconButton size="small" onClick={() => setChatPanelOpen(false)} sx={{ color: tokens.text.muted }}>
          <CloseIcon sx={{ fontSize: 16 }} />
        </IconButton>
      </Box>

      {/* Messages */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 2, pb: 1 }}>
        {!selectedModule && (
          <Alert severity="info" sx={{ borderRadius: 2, mb: 2, fontSize: 12 }}>
            Select a module in Class Overview to give the AI course context.
          </Alert>
        )}
        {error && (
          <Alert severity="error" sx={{ borderRadius: 2, mb: 2 }} onClose={() => setError(null)}>{error}</Alert>
        )}

        {messages.length === 0 && (
          <Box sx={{ pt: 3 }}>
            <Typography sx={{ fontSize: 12, color: tokens.text.muted, mb: 2, textAlign: 'center' }}>
              Ask about risk, interventions, or engagement.
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.75 }}>
              {SUGGESTED_PROMPTS.map((p) => (
                <Box key={p} onClick={() => sendMessage(p)} sx={{
                  fontSize: 12, bgcolor: tokens.surface.raised, border: `1px solid ${tokens.border.default}`,
                  borderRadius: 1.5, px: 1.5, py: 1, cursor: 'pointer', color: tokens.text.primary,
                  '&:hover': { bgcolor: tokens.surface.subtle },
                }}>
                  {p}
                </Box>
              ))}
            </Box>
          </Box>
        )}

        {messages.map((msg, i) => (
          <MessageBubble key={msg.id} message={msg}
            isStreaming={isStreaming && i === messages.length - 1 && msg.role === 'assistant'} />
        ))}
        <div ref={bottomRef} />
      </Box>

      {/* Input */}
      <Paper elevation={0} sx={{ p: 1.5, borderTop: `1px solid ${tokens.border.default}`, display: 'flex', gap: 1, alignItems: 'flex-end', flexShrink: 0 }}>
        <TextField
          multiline maxRows={4} fullWidth size="small"
          placeholder="Ask about your students…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(input) } }}
          disabled={isStreaming}
          sx={{ '& .MuiOutlinedInput-root': { borderRadius: 1.5, fontSize: 12, fontFamily: tokens.font.sans } }}
        />
        <IconButton onClick={() => sendMessage(input)} disabled={isStreaming || !input.trim()}
          sx={{
            bgcolor: tokens.brand.primary, color: '#fff', borderRadius: 1.5, width: 36, height: 36, flexShrink: 0,
            '&:hover': { bgcolor: tokens.brand.primaryDark },
            '&.Mui-disabled': { bgcolor: tokens.border.default, color: tokens.text.muted },
          }}
        >
          {isStreaming ? <CircularProgress size={14} sx={{ color: '#fff' }} /> : <SendIcon sx={{ fontSize: 16 }} />}
        </IconButton>
      </Paper>
    </Box>
  )
}
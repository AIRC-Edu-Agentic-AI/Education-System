import { useRef, useEffect, useState } from 'react'
import {
  Box, Typography, TextField, IconButton, Chip,
  CircularProgress, Alert, Paper,
} from '@mui/material'
import SendIcon from '@mui/icons-material/SendRounded'
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutlineRounded'
import CloseIcon from '@mui/icons-material/CloseRounded'
import { container } from '../../../di/container'
import { useContextStore } from '../../../shared/stores/contextStore'
import { useChatStore } from '../../../shared/stores/chatStore'
import { MessageBubble } from './MessageBubble'
import { useQuery } from '@tanstack/react-query'
import type { AgentContext, ChatMessage, StudentProfile } from '../../../types/domain'

function buildContext(
  module: string, presentation: string, currentWeek: number, numWeeks: number,
  activeStudent: StudentProfile | null,
  students: { risk_by_week: number[]; tier_by_week: (1|2|3)[] }[]
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

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text.trim(),
      timestamp: new Date(),
    }
    addMessage(userMsg)

    const assistantMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    }
    addMessage(assistantMsg)
    setStreaming(true)

    try {
      const ctx = buildContext(selectedModule, selectedPresentation, currentWeek, numWeeks, activeStudent, students)
      const history = [...messages, userMsg]
      for await (const chunk of container.agentService.stream(history, ctx)) {
        appendToLast(chunk)
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
      appendToLast('\n\n[Error: Could not complete response]')
    } finally {
      setStreaming(false)
    }
  }

  const noData = !selectedModule || !selectedPresentation

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', bgcolor: '#fff' }}>
      {/* Header */}
      <Box sx={{
        px: 2, py: 1.5, borderBottom: '1px solid #E5E3DC', bgcolor: '#fff',
        display: 'flex', alignItems: 'center', gap: 1, minHeight: 60, flexShrink: 0,
      }}>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Typography sx={{ fontSize: 13, fontWeight: 500, color: '#0A1628', fontFamily: '"IBM Plex Sans", sans-serif' }}>
            AI Advisor
          </Typography>
          <Box sx={{ display: 'flex', gap: 0.5, mt: 0.25, flexWrap: 'wrap' }}>
            {selectedModule && (
              <Chip
                label={`${selectedModule} · Wk ${currentWeek}`}
                size="small"
                sx={{ bgcolor: '#E1F5EE', color: '#0F6E56', fontFamily: '"IBM Plex Mono", monospace', fontSize: 10, height: 18 }}
              />
            )}
            {activeStudent && (
              <Chip
                label={`#${activeStudent.id_student}`}
                size="small"
                onDelete={() => useContextStore.getState().setActiveStudent(null)}
                sx={{ bgcolor: '#FAEEDA', color: '#854F0B', fontFamily: '"IBM Plex Mono", monospace', fontSize: 10, height: 18 }}
              />
            )}
          </Box>
        </Box>
        <IconButton size="small" onClick={clearMessages} title="Clear conversation" sx={{ color: '#9CA3AF' }}>
          <DeleteOutlineIcon sx={{ fontSize: 16 }} />
        </IconButton>
        <IconButton size="small" onClick={() => setChatPanelOpen(false)} sx={{ color: '#9CA3AF' }}>
          <CloseIcon sx={{ fontSize: 16 }} />
        </IconButton>
      </Box>

      {/* Messages */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 2, pb: 1 }}>
        {noData && (
          <Alert severity="info" sx={{ borderRadius: 2, mb: 2, fontSize: 12 }}>
            Select a module in Class Overview to give the AI course context.
          </Alert>
        )}

        {error && (
          <Alert severity="error" sx={{ borderRadius: 2, mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {messages.length === 0 && (
          <Box sx={{ pt: 3 }}>
            <Typography sx={{ fontSize: 12, color: '#9CA3AF', fontFamily: '"IBM Plex Sans", sans-serif', mb: 2, textAlign: 'center' }}>
              Ask about risk, interventions, or engagement.
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.75 }}>
              {SUGGESTED_PROMPTS.map((p) => (
                <Box
                  key={p}
                  onClick={() => sendMessage(p)}
                  sx={{
                    fontSize: 12,
                    fontFamily: '"IBM Plex Sans", sans-serif',
                    bgcolor: '#F8F7F4',
                    border: '1px solid #E5E3DC',
                    borderRadius: 1.5,
                    px: 1.5,
                    py: 1,
                    cursor: 'pointer',
                    color: '#374151',
                    '&:hover': { bgcolor: '#F0EFE9' },
                  }}
                >
                  {p}
                </Box>
              ))}
            </Box>
          </Box>
        )}

        {messages.map((msg, i) => (
          <MessageBubble
            key={msg.id}
            message={msg}
            isStreaming={isStreaming && i === messages.length - 1 && msg.role === 'assistant'}
          />
        ))}
        <div ref={bottomRef} />
      </Box>

      {/* Input */}
      <Paper
        elevation={0}
        sx={{ p: 1.5, borderTop: '1px solid #E5E3DC', bgcolor: '#fff', display: 'flex', gap: 1, alignItems: 'flex-end', flexShrink: 0 }}
      >
        <TextField
          multiline
          maxRows={4}
          fullWidth
          placeholder="Ask about your students…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(input) }
          }}
          disabled={isStreaming}
          size="small"
          sx={{
            '& .MuiOutlinedInput-root': { borderRadius: 1.5, fontSize: 12, fontFamily: '"IBM Plex Sans", sans-serif' },
          }}
        />
        <IconButton
          onClick={() => sendMessage(input)}
          disabled={isStreaming || !input.trim()}
          sx={{
            bgcolor: '#0F6E56',
            color: '#fff',
            borderRadius: 1.5,
            width: 36,
            height: 36,
            flexShrink: 0,
            '&:hover': { bgcolor: '#085041' },
            '&.Mui-disabled': { bgcolor: '#E5E3DC', color: '#9CA3AF' },
          }}
        >
          {isStreaming
            ? <CircularProgress size={14} sx={{ color: '#fff' }} />
            : <SendIcon sx={{ fontSize: 16 }} />
          }
        </IconButton>
      </Paper>
    </Box>
  )
}

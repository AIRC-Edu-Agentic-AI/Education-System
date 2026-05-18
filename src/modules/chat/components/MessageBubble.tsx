import './MessageBubble.css'
import ReactMarkdown from 'react-markdown'
import { Box, Typography } from '@mui/material'
import { tokens } from '../../../theme'
import type { ChatMessage } from '../../../types/domain'

interface Props {
  message: ChatMessage
  isStreaming?: boolean
}

export function MessageBubble({ message, isStreaming }: Props) {
  const isUser = message.role === 'user'

  return (
    <Box sx={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start', mb: 2 }}>
      {!isUser && (
        <Box sx={{
          width: 28, height: 28, borderRadius: '50%',
          bgcolor: tokens.brand.primary,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          mr: 1, mt: 0.5, flexShrink: 0,
        }}>
          <Typography sx={{ fontSize: 12, color: '#fff', fontFamily: tokens.font.mono, fontWeight: 500 }}>
            AI
          </Typography>
        </Box>
      )}

      <Box sx={{
        maxWidth: '75%', px: 2, py: 1.5,
        borderRadius: isUser ? '16px 16px 4px 16px' : '4px 16px 16px 16px',
        bgcolor: isUser ? tokens.nav.bg : tokens.surface.paper,
        border: isUser ? 'none' : `1px solid ${tokens.border.default}`,
      }}>
        <Typography
          component="div"
          sx={{ fontSize: 13, lineHeight: 1.7, color: isUser ? '#fff' : 'text.primary', whiteSpace: 'pre-wrap' }}
        >
          {isUser ? message.content : (
            <div className="chat-bubble ai-message">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}
          {isStreaming && (
            <Box
              component="span"
              sx={{
                display: 'inline-block', width: 8, height: 14,
                bgcolor: tokens.brand.primaryLight,
                ml: 0.5, borderRadius: 0.5,
                animation: 'blink 1s step-end infinite',
                '@keyframes blink': { '0%, 100%': { opacity: 1 }, '50%': { opacity: 0 } },
              }}
            />
          )}
        </Typography>
        <Typography sx={{ fontSize: 10, color: isUser ? tokens.text.secondary : 'text.muted', mt: 0.5, fontFamily: tokens.font.mono }}>
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </Typography>
      </Box>
    </Box>
  )
}

import './MessageBubble.css'
import ReactMarkdown from 'react-markdown'
import { Box, Typography } from '@mui/material'
import type { ChatMessage } from '../../../types/domain'

interface Props {
  message: ChatMessage
  isStreaming?: boolean
}

export function MessageBubble({ message, isStreaming }: Props) {
  const isUser = message.role === 'user'

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        mb: 2,
      }}
    >
      {!isUser && (
        <Box
          sx={{
            width: 28,
            height: 28,
            borderRadius: '50%',
            bgcolor: '#0F6E56',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            mr: 1,
            mt: 0.5,
            flexShrink: 0,
          }}
        >
          <Typography sx={{ fontSize: 12, color: '#fff', fontFamily: '"IBM Plex Mono", monospace', fontWeight: 500 }}>
            AI
          </Typography>
        </Box>
      )}

      <Box
        sx={{
          maxWidth: '75%',
          px: 2,
          py: 1.5,
          borderRadius: isUser ? '16px 16px 4px 16px' : '4px 16px 16px 16px',
          bgcolor: isUser ? '#0A1628' : '#fff',
          border: isUser ? 'none' : '1px solid #E5E3DC',
        }}
      >
        <Typography
          component="div"
          sx={{
            fontSize: 13,
            lineHeight: 1.7,
            color: isUser ? '#fff' : '#0A1628',
            fontFamily: '"IBM Plex Sans", sans-serif',
            whiteSpace: 'pre-wrap',
          }}
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
                display: 'inline-block',
                width: 8,
                height: 14,
                bgcolor: '#1D9E75',
                ml: 0.5,
                borderRadius: 0.5,
                animation: 'blink 1s step-end infinite',
                '@keyframes blink': { '0%, 100%': { opacity: 1 }, '50%': { opacity: 0 } },
              }}
            />
          )}
        </Typography>
        <Typography sx={{ fontSize: 10, color: isUser ? '#4B5563' : '#9CA3AF', mt: 0.5, fontFamily: '"IBM Plex Mono", monospace' }}>
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </Typography>
      </Box>
    </Box>
  )
}

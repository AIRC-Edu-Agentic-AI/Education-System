import { useAuth0 } from '@auth0/auth0-react'
import { Box, Card, CardContent, Button, Typography } from '@mui/material'

export function LoginView() {
  const { loginWithRedirect } = useAuth0()

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', bgcolor: '#F4F3F0' }}>
      <Card elevation={0} sx={{ width: 400, border: '1px solid #E5E3DC', borderRadius: 3 }}>
        <CardContent sx={{ p: 4 }}>
          <Typography sx={{ fontFamily: '"IBM Plex Mono", monospace', fontSize: 13, color: '#1D9E75', mb: 0.5 }}>
            RTI / MTSS
          </Typography>
          <Typography sx={{ fontFamily: '"IBM Plex Sans", sans-serif', fontSize: 22, fontWeight: 600, color: '#0A1628', mb: 1 }}>
            Teacher Dashboard
          </Typography>
          <Typography sx={{ fontSize: 13, color: '#6B7280', mb: 3 }}>
            Sign in with your VNU account to access the dashboard
          </Typography>

          <Button
            fullWidth
            variant="contained"
            onClick={() => loginWithRedirect()}
            sx={{ bgcolor: '#0F6E56', '&:hover': { bgcolor: '#085041' }, py: 1.2 }}
          >
            Sign In
          </Button>
        </CardContent>
      </Card>
    </Box>
  )
}
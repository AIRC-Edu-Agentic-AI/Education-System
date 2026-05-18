import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider, CssBaseline } from '@mui/material'
import { theme } from './theme'
import { Shell } from './shared/components/Shell'
import { DashboardView } from './modules/dashboard/views/DashboardView'
import { StudentDetailView } from './modules/student/views/StudentDetailView'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider, createTheme, CssBaseline, Box, CircularProgress } from '@mui/material'
import { useAuth0 } from '@auth0/auth0-react'
import { Shell } from './shared/components/Shell'
import { DashboardView } from './modules/dashboard/views/DashboardView'
import { StudentDetailView } from './modules/student/views/StudentDetailView'
import { LoginView } from './modules/auth/views/LoginView'
import { useEffect } from 'react'
import { useAuthStore } from './shared/stores/authStore'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 5 * 60 * 1000, retry: 1 },
  },
})

const theme = createTheme({
  palette: {
    primary: { main: '#0F6E56', dark: '#085041' },
    secondary: { main: '#BA7517' },
    background: { default: '#F4F3F0', paper: '#ffffff' },
  },
  typography: {
    fontFamily: '"IBM Plex Sans", sans-serif',
  },
  shape: { borderRadius: 8 },
  components: {
    MuiButton: {
      styleOverrides: {
        root: { textTransform: 'none', fontFamily: '"IBM Plex Sans", sans-serif', fontWeight: 500 },
      },
    },
    MuiChip: {
      styleOverrides: { root: { fontFamily: '"IBM Plex Mono", monospace' } },
    },
    MuiTableCell: {
      styleOverrides: { root: { fontFamily: '"IBM Plex Sans", sans-serif' } },
    },
  },
})

function AppRoutes() {
  const { isLoading, isAuthenticated, user, getIdTokenClaims } = useAuth0()
  const { setUserFromAuth0, clearUser, user: storeUser } = useAuthStore()

  useEffect(() => {
    if (isAuthenticated && user) {
      getIdTokenClaims().then((claims) => {
        setUserFromAuth0(user, claims)
      })
    } else {
      clearUser()
    }
  }, [isAuthenticated, user])

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
        <CircularProgress sx={{ color: '#0F6E56' }} />
      </Box>
    )
  }

  if (!isAuthenticated) {
    return <LoginView />
  }

  if (!storeUser) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
        <CircularProgress sx={{ color: '#0F6E56' }} />
      </Box>
    )
  }

  return (
    <Shell>
      <Routes>
        <Route path="/" element={<DashboardView />} />
        <Route path="/student/:id" element={<StudentDetailView />} />
        <Route path="/student" element={<StudentDetailView />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Shell>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <BrowserRouter>
          <Shell>
            <Routes>
              <Route path="/" element={<DashboardView />} />
              <Route path="/student/:id" element={<StudentDetailView />} />
              <Route path="/student" element={<StudentDetailView />} />
            </Routes>
          </Shell>
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  )
}

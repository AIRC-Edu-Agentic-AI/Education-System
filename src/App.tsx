import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider, CssBaseline, Box, CircularProgress } from '@mui/material'
import { useAuth0 } from '@auth0/auth0-react'
import { theme, tokens } from './theme'
import { Shell } from './shared/components/Shell'
import { DashboardView } from './modules/dashboard/views/DashboardView'
import { StudentDetailView } from './modules/student/views/StudentDetailView'
import { LoginView } from './modules/auth/views/LoginView'
import { useAuthStore } from './shared/stores/authStore'
import { ClassView } from './modules/class/views/ClassView'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 5 * 60 * 1000, retry: 1 },
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

  if (isLoading || (isAuthenticated && !storeUser)) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
        <CircularProgress sx={{ color: tokens.brand.primary }} />
      </Box>
    )
  }

  if (!isAuthenticated) {
    return <LoginView />
  }

  return (
    <Shell>
      <Routes>
        <Route path="/" element={<DashboardView />} />
        <Route path="/student/:id" element={<StudentDetailView />} />
        <Route path="/student" element={<StudentDetailView />} />
        <Route path="/class" element={<ClassView />} />
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
          <AppRoutes />
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  )
}
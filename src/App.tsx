import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material'
import { Shell } from './shared/components/Shell'
import { DashboardView } from './modules/dashboard/views/DashboardView'
import { StudentDetailView } from './modules/student/views/StudentDetailView'

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

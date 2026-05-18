import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider, CssBaseline } from '@mui/material'
import { theme } from './theme'
import { Shell } from './shared/components/Shell'
import { DashboardView } from './modules/dashboard/views/DashboardView'
import { StudentDetailView } from './modules/student/views/StudentDetailView'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 5 * 60 * 1000, retry: 1 },
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

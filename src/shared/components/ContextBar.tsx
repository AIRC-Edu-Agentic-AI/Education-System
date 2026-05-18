import { useEffect } from 'react'
import {
  Box, FormControl, InputLabel, Select, MenuItem, Slider, Typography,
} from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { container } from '../../di/container'
import { useContextStore } from '../stores/contextStore'

export function ContextBar() {
  const {
    selectedModule, selectedPresentation, currentWeek,
    setModule, setPresentation, setCurrentWeek, setNumWeeks,
  } = useContextStore()

  const { data: index } = useQuery({
    queryKey: ['oulad-index'],
    queryFn: () => container.dataService.getIndex(),
    retry: false,
  })

  const { data: course } = useQuery({
    queryKey: ['course', selectedModule, selectedPresentation],
    queryFn: () => container.dataService.getCourse(selectedModule, selectedPresentation),
    enabled: !!selectedModule && !!selectedPresentation,
  })

  // Auto-select first course on first load
  useEffect(() => {
    if (index && !selectedModule && index.courses.length > 0) {
      const first = index.courses[0]
      setModule(first.module)
      setPresentation(first.presentation)
      setNumWeeks(first.num_weeks)
    }
  }, [index, selectedModule, setModule, setPresentation, setNumWeeks])

  useEffect(() => {
    if (course) setNumWeeks(course.num_weeks)
  }, [course, setNumWeeks])

  const numWeeks = course?.num_weeks ?? 39
  const moduleOptions = [...new Set(index?.courses.map((c) => c.module) ?? [])]
  const presentationOptions = index?.courses
    .filter((c) => c.module === selectedModule)
    .map((c) => c.presentation) ?? []

  return (
    <Box
      sx={{
        display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap',
        px: 3, py: 1, bgcolor: '#fff', borderBottom: '1px solid #E5E3DC',
        minHeight: 52, flexShrink: 0,
      }}
    >
      <FormControl size="small" sx={{ minWidth: 110 }}>
        <InputLabel sx={{ fontSize: 12 }}>Module</InputLabel>
        <Select
          value={selectedModule}
          label="Module"
          onChange={(e) => {
            const mod = e.target.value
            const firstPres = index?.courses.find((c) => c.module === mod)?.presentation ?? ''
            setModule(mod)
            setPresentation(firstPres)
          }}
          sx={{ fontSize: 12, fontFamily: '"IBM Plex Mono", monospace' }}
        >
          {moduleOptions.map((m) => (
            <MenuItem key={m} value={m} sx={{ fontSize: 12, fontFamily: '"IBM Plex Mono", monospace' }}>{m}</MenuItem>
          ))}
        </Select>
      </FormControl>

      <FormControl size="small" sx={{ minWidth: 110 }}>
        <InputLabel sx={{ fontSize: 12 }}>Presentation</InputLabel>
        <Select
          value={selectedPresentation}
          label="Presentation"
          onChange={(e) => setPresentation(e.target.value)}
          sx={{ fontSize: 12, fontFamily: '"IBM Plex Mono", monospace' }}
        >
          {presentationOptions.map((p) => (
            <MenuItem key={p} value={p} sx={{ fontSize: 12, fontFamily: '"IBM Plex Mono", monospace' }}>{p}</MenuItem>
          ))}
        </Select>
      </FormControl>

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, minWidth: 220, flex: 1, maxWidth: 360 }}>
        <Typography sx={{ fontSize: 11, color: '#6B7280', fontFamily: '"IBM Plex Mono", monospace', whiteSpace: 'nowrap' }}>
          Week
        </Typography>
        <Slider
          min={1}
          max={numWeeks}
          value={currentWeek}
          onChange={(_, v) => setCurrentWeek(v as number)}
          size="small"
          sx={{ color: '#1D9E75' }}
        />
        <Typography sx={{ fontSize: 12, fontFamily: '"IBM Plex Mono", monospace', color: '#0A1628', minWidth: 36 }}>
          {currentWeek}/{numWeeks}
        </Typography>
      </Box>
    </Box>
  )
}

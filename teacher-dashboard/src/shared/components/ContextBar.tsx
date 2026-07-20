import { useEffect } from 'react'
import { Box, FormControl, InputLabel, Select, MenuItem, Slider, Typography } from '@mui/material'
import { useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { tokens } from '../../theme'
import { container } from '../../di/container'
import { useContextStore } from '../stores/contextStore'

export function ContextBar() {
  const { selectedModule, selectedPresentation, currentWeek, setModule, setPresentation, setCurrentWeek, setNumWeeks } = useContextStore()

  const { data: index } = useQuery({
    queryKey: ['oulad-index'],
    queryFn: () => container.dataService.getIndex(),
    retry: false,
  })

  useEffect(() => {
    if (index && !selectedModule && index.courses.length > 0) {
      const first = index.courses[0]
      setModule(first.module)
      setPresentation(first.presentation)
      setNumWeeks(first.num_weeks)
    }
  }, [index, selectedModule, setModule, setPresentation, setNumWeeks])

  useEffect(() => {
    if (index && selectedModule && selectedPresentation) {
      const c = index.courses.find(x => x.module === selectedModule && x.presentation === selectedPresentation)
      if (c) setNumWeeks(c.num_weeks)
    }
  }, [index, selectedModule, selectedPresentation, setNumWeeks])

  const moduleOptions = [...new Set(index?.courses.map((c) => c.module) ?? [])]
  const presentationOptions = index?.courses.filter((c) => c.module === selectedModule).map((c) => c.presentation) ?? []
  
  const currentCourse = index?.courses.find(x => x.module === selectedModule && x.presentation === selectedPresentation)
  const numWeeks = currentCourse?.num_weeks ?? 39

  if (location.pathname === '/schedule') {
    return null
  }

  return (
    <Box sx={{
      display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap',
      px: 3, py: 1, bgcolor: tokens.surface.paper, borderBottom: `1px solid ${tokens.border.default}`,
      minHeight: 52, flexShrink: 0,
    }}>
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
          sx={{ fontSize: 12, fontFamily: tokens.font.mono }}
        >
          {moduleOptions.map((m) => (
            <MenuItem key={m} value={m} sx={{ fontSize: 12, fontFamily: tokens.font.mono }}>{m}</MenuItem>
          ))}
        </Select>
      </FormControl>

      <FormControl size="small" sx={{ minWidth: 110 }}>
        <InputLabel sx={{ fontSize: 12 }}>Presentation</InputLabel>
        <Select
          value={selectedPresentation}
          label="Presentation"
          onChange={(e) => setPresentation(e.target.value)}
          sx={{ fontSize: 12, fontFamily: tokens.font.mono }}
        >
          {presentationOptions.map((p) => (
            <MenuItem key={p} value={p} sx={{ fontSize: 12, fontFamily: tokens.font.mono }}>{p}</MenuItem>
          ))}
        </Select>
      </FormControl>

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, minWidth: 220, flex: 1, maxWidth: 360 }}>
        <Typography sx={{ fontSize: 11, color: tokens.text.secondary, fontFamily: tokens.font.mono, whiteSpace: 'nowrap' }}>
          Week
        </Typography>
        <Slider
          min={1} max={numWeeks} value={currentWeek}
          onChange={(_, v) => setCurrentWeek(v as number)}
          size="small"
          sx={{ color: tokens.brand.primaryLight }}
        />
        <Typography sx={{ fontSize: 12, fontFamily: tokens.font.mono, color: tokens.text.primary, minWidth: 36 }}>
          {currentWeek}/{numWeeks}
        </Typography>
      </Box>
    </Box>
  )
}

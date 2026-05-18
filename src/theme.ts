import { createTheme } from '@mui/material/styles'

export const tokens = {
  brand: {
    primary:          '#0F6E56',
    primaryDark:      '#085041',
    primaryLight:     '#1D9E75',
    primarySubtle:    '#E1F5EE',
    primaryMuted:     '#5DCAA5',
    secondary:        '#BA7517',
    secondarySubtle:  '#FAEEDA',
    secondaryText:    '#854F0B',
    danger:           '#E24B4A',
    dangerSubtle:     '#FCEBEB',
    dangerText:       '#A32D2D',
  },
  text: {
    primary:   '#0A1628',
    secondary: '#6B7280',
    muted:     '#9CA3AF',
    onDark:    '#C8C6BE',
  },
  surface: {
    default: '#F4F3F0',
    paper:   '#FFFFFF',
    raised:  '#F8F7F4',
    subtle:  '#F0EFE9',
  },
  border: {
    default: '#E5E3DC',
  },
  nav: {
    bg:      '#0A1628',
    hover:   '#1E2D45',
    divider: '#1E2D45',
  },
  chart: {
    indigo: '#6366F1',
  },
  font: {
    sans: '"IBM Plex Sans", sans-serif',
    mono: '"IBM Plex Mono", monospace',
  },
} as const

export const theme = createTheme({
  palette: {
    primary:    { main: tokens.brand.primary, dark: tokens.brand.primaryDark },
    secondary:  { main: tokens.brand.secondary },
    background: { default: tokens.surface.default, paper: tokens.surface.paper },
  },
  typography: {
    fontFamily: tokens.font.sans,
  },
  shape: { borderRadius: 8 },
  components: {
    MuiButton: {
      styleOverrides: {
        root: { textTransform: 'none', fontWeight: 500 },
      },
    },
    MuiChip: {
      styleOverrides: { root: { fontFamily: tokens.font.mono } },
    },
    MuiTableCell: {
      styleOverrides: { root: { fontFamily: tokens.font.sans } },
    },
    MuiToolbar: {
      styleOverrides: { root: { minHeight: '52px !important' } },
    },
    MuiCard: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: { border: `1px solid ${tokens.border.default}`, borderRadius: 8 },
      },
    },
  },
})

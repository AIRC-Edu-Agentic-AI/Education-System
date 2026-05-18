import React from 'react'
import DashboardIcon from '@mui/icons-material/GridViewRounded'
import PersonIcon from '@mui/icons-material/PersonRounded'

export interface ModuleConfig {
  id: string
  label: string
  path: string
  icon: React.ReactNode
}

export const moduleRegistry: ModuleConfig[] = [
  {
    id: 'dashboard',
    label: 'Class overview',
    path: '/',
    icon: <DashboardIcon fontSize="small" />,
  },
  {
    id: 'student',
    label: 'Student detail',
    path: '/student',
    icon: <PersonIcon fontSize="small" />,
  },
]

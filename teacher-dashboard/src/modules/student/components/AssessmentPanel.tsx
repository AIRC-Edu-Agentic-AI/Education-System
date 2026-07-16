import { useState } from 'react'
import {
  Card, CardContent, Typography, Table, TableBody, TableCell,
  TableHead, TableRow, Chip, Box, ToggleButtonGroup, ToggleButton, Collapse,
} from '@mui/material'
import { tokens } from '../../../theme'
import type { AssessmentRecord, StudentProfile } from '../../../types/domain'
import { useStudentStore, type AssessmentFilter, type AssessmentSort } from '../stores/studentStore'

interface Props {
  student: StudentProfile
  currentWeek: number
}

function submissionStatus(a: AssessmentRecord, currentDay: number): 'on-time' | 'late' | 'missing' | 'upcoming' {
  if (a.date_due == null || a.date_due > currentDay) return 'upcoming'
  if (a.date_submitted == null) return 'missing'
  if (a.date_submitted > a.date_due) return 'late'
  return 'on-time'
}

const STATUS_CHIP: Record<string, { bg: string; text: string }> = {
  'on-time':  { bg: tokens.brand.primarySubtle, text: tokens.brand.primary },
  'late':     { bg: tokens.brand.secondarySubtle, text: tokens.brand.secondaryText },
  'missing':  { bg: tokens.brand.dangerSubtle, text: tokens.brand.dangerText },
  'upcoming': { bg: tokens.surface.neutral, text: tokens.text.secondary },
}

function sortAssessments(
  assessments: AssessmentRecord[],
  sortBy: AssessmentSort,
): AssessmentRecord[] {
  return [...assessments].sort((a, b) => {
    if (sortBy === 'score') {
      if (a.score == null && b.score == null) return 0
      if (a.score == null) return 1
      if (b.score == null) return -1
      return b.score - a.score
    }
    if (sortBy === 'weight') {
      if (a.weight == null && b.weight == null) return 0
      if (a.weight == null) return 1
      if (b.weight == null) return -1
      return b.weight - a.weight
    }
    return (a.date_due ?? 0) - (b.date_due ?? 0)
  })
}

function filterAssessments(
  assessments: AssessmentRecord[],
  filter: AssessmentFilter,
  currentDay: number,
): AssessmentRecord[] {
  if (filter === 'all') return assessments
  return assessments.filter((a) => {
    const status = submissionStatus(a, currentDay)
    if (filter === 'submitted') return status === 'on-time'
    if (filter === 'late')      return status === 'late'
    if (filter === 'missing')   return status === 'missing'
    return true
  })
}

export function AssessmentPanel({ student, currentWeek }: Props) {
  const { assessmentFilter, assessmentSort, setAssessmentFilter, setAssessmentSort } = useStudentStore()
  const [expandedId, setExpandedId] = useState<number | null>(null)

  const currentDay = currentWeek * 7
  const realAssessments = (student.assessments ?? []).filter(
    (a) => !(a.weight === 100 && a.score === null),
  )
  const assessments = sortAssessments(
    filterAssessments(realAssessments, assessmentFilter, currentDay),
    assessmentSort,
  )

  const toggleExpand = (id: number) =>
    setExpandedId((prev) => (prev === id ? null : id))

  return (
    <Card elevation={0} sx={{ borderRadius: 2 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1.5, flexWrap: 'wrap', gap: 1 }}>
          <Typography sx={{ fontSize: 12, fontWeight: 500, color: tokens.text.primary }}>
            Assessments
          </Typography>

          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <ToggleButtonGroup
              size="small"
              exclusive
              value={assessmentFilter}
              onChange={(_, v) => v && setAssessmentFilter(v)}
              sx={{ '& .MuiToggleButton-root': { fontSize: 10, py: 0.25, px: 1, textTransform: 'none' } }}
            >
              {(['all', 'submitted', 'late', 'missing'] as AssessmentFilter[]).map((f) => (
                <ToggleButton key={f} value={f}>{f}</ToggleButton>
              ))}
            </ToggleButtonGroup>

            <ToggleButtonGroup
              size="small"
              exclusive
              value={assessmentSort}
              onChange={(_, v) => v && setAssessmentSort(v)}
              sx={{ '& .MuiToggleButton-root': { fontSize: 10, py: 0.25, px: 1, textTransform: 'none' } }}
            >
              {(['date', 'score', 'weight'] as AssessmentSort[]).map((s) => (
                <ToggleButton key={s} value={s}>{s}</ToggleButton>
              ))}
            </ToggleButtonGroup>
          </Box>
        </Box>

        <Table size="small">
          <TableHead>
            <TableRow>
              {['Type', 'Due (day)', 'Weight', 'Score', 'Status', 'Submitted'].map((h) => (
                <TableCell key={h} sx={{ fontSize: 11, color: tokens.text.secondary, bgcolor: tokens.surface.raised }}>
                  {h}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {assessments.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} sx={{ fontSize: 12, color: tokens.text.muted, textAlign: 'center', py: 3 }}>
                  No assessments match this filter.
                </TableCell>
              </TableRow>
            ) : assessments.map((a) => {
              const status = submissionStatus(a, currentDay)
              const sc     = STATUS_CHIP[status]
              const expanded = expandedId === a.id_assessment

              return (
                <>
                  <TableRow
                    key={a.id_assessment}
                    onClick={() => toggleExpand(a.id_assessment)}
                    sx={{ cursor: 'pointer', '&:hover': { bgcolor: tokens.surface.raised } }}
                  >
                    <TableCell sx={{ fontSize: 11 }}>{a.assessment_type}</TableCell>
                    <TableCell sx={{ fontSize: 11 }}>{a.date_due ?? '—'}</TableCell>
                    <TableCell sx={{ fontSize: 11 }}>{a.weight != null ? `${a.weight}%` : '—'}</TableCell>
                    <TableCell sx={{ fontSize: 11 }}>
                      {a.score != null
                        ? <Chip label={`${a.score}%`} size="small" sx={{ fontSize: 11, height: 20, bgcolor: a.score >= 50 ? tokens.brand.primarySubtle : tokens.brand.dangerSubtle, color: a.score >= 50 ? tokens.brand.primary : tokens.brand.dangerText }} />
                        : <Typography sx={{ fontSize: 11, color: tokens.text.muted }}>—</Typography>
                      }
                    </TableCell>
                    <TableCell>
                      <Chip label={status} size="small" sx={{ fontSize: 10, height: 18, bgcolor: sc.bg, color: sc.text, '& .MuiChip-label': { px: 0.75 } }} />
                    </TableCell>
                    <TableCell sx={{ fontSize: 11, color: a.date_submitted ? tokens.brand.primary : tokens.text.muted }}>
                      {a.date_submitted != null ? `Day ${a.date_submitted}` : '—'}
                    </TableCell>
                  </TableRow>

                  {expanded && (
                    <TableRow key={`${a.id_assessment}-detail`} sx={{ bgcolor: tokens.surface.raised }}>
                      <TableCell colSpan={6} sx={{ py: 1, px: 2 }}>
                        <Collapse in={expanded}>
                          <Typography sx={{ fontSize: 11, color: tokens.text.secondary, fontFamily: tokens.font.mono }}>
                            {status === 'on-time' && a.date_due != null && a.date_submitted != null &&
                              `Submitted ${a.date_due - a.date_submitted} day(s) before the deadline.`}
                            {status === 'late' && a.date_due != null && a.date_submitted != null &&
                              `Submitted ${a.date_submitted - a.date_due} day(s) after the deadline.`}
                            {status === 'missing' &&
                              `Not submitted. Assessment was due on day ${a.date_due}.`}
                            {status === 'upcoming' &&
                              `Due on day ${a.date_due ?? '?'} — not yet reached.`}
                          </Typography>
                        </Collapse>
                      </TableCell>
                    </TableRow>
                  )}
                </>
              )
            })}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}

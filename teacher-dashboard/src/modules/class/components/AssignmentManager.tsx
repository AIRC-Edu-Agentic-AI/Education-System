import React, { useEffect, useState } from 'react'
import {
  Box,
  Button,
  Card,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
  Chip,
  Stack,
  Paper,
  Alert,
  IconButton,
} from '@mui/material'
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined'
import { useAuthStore } from '../../../shared/stores/authStore'

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000/api'
const FILE_BASE = API_BASE.replace(/\/api\/?$/, '')

interface AssignmentManagerProps {
  module: string
  presentation: string
}

interface AssignmentRecord {
  _id: string
  id_assessment: number
  code_module: string
  title?: string
  description?: string
  type: string
  status: string
  due_date: number
  weight: number
  max_file_size_mb: number
  allowed_formats: string[]
  created_at: string
  updated_at: string
}

interface SubmissionRecord {
  _id: string
  student_id: number
  id_assessment: number
  content?: string
  file_name?: string
  file_url?: string
  file_type?: string
  submitted_at: string
  submitted_day: number
  status: string
  score?: number
  feedback?: string
}

export default function AssignmentManager({ module, presentation }: AssignmentManagerProps) {
  const authUser = useAuthStore((state) => state.user)
  const [assignments, setAssignments] = useState<AssignmentRecord[]>([])
  const [submissions, setSubmissions] = useState<SubmissionRecord[]>([])
  const [selectedAssignment, setSelectedAssignment] = useState<AssignmentRecord | null>(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [grading, setGrading] = useState(false)
  const [submissionLoading, setSubmissionLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [type, setType] = useState('TMA')
  const [weight, setWeight] = useState(10)
  const [dueDate, setDueDate] = useState(1)
  const [maxFileSizeMb, setMaxFileSizeMb] = useState(25)
  const [allowedFormats, setAllowedFormats] = useState('pdf, docx')
  const [gradeScore, setGradeScore] = useState<number | ''>('')
  const [gradeFeedback, setGradeFeedback] = useState('')
  const [submissionDialogOpen, setSubmissionDialogOpen] = useState(false)

  const teacherId = authUser?.email || authUser?.name || 'teacher_admin'
  const courseCode = `${module} ${presentation}`

  useEffect(() => {
    if (!module || !presentation) {
      setAssignments([])
      return
    }

    const loadAssignments = async () => {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch(`${API_BASE}/assignments/${encodeURIComponent(module)}/${encodeURIComponent(presentation)}`)
        if (!res.ok) throw new Error('Failed to load assignments')
        const data = await res.json()
        setAssignments(Array.isArray(data) ? data : [])
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error loading assignments')
      } finally {
        setLoading(false)
      }
    }

    loadAssignments()
  }, [module, presentation])

  const handleSaveAssignment = async () => {
    if (!title.trim() || !description.trim()) {
      setError('Please enter assignment title and description.')
      return
    }

    setSaving(true)
    setError(null)
    try {
      const payload = {
        code_module: module,
        title,
        description,
        type,
        weight,
        due_date: dueDate,
        allowed_formats: allowedFormats.split(',').map((item) => item.trim()).filter(Boolean),
        max_file_size_mb: maxFileSizeMb,
        teacher_id: teacherId,
      }

      const res = await fetch(`${API_BASE}/assignments/${encodeURIComponent(module)}/${encodeURIComponent(presentation)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || 'Failed to create assignment')
      }

      setType('TMA')
      setWeight(10)
      setDueDate(1)
      setMaxFileSizeMb(25)
      setTitle('')
      setDescription('')
      setAllowedFormats('pdf, docx')
      await fetchAssignments()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error creating assignment')
    } finally {
      setSaving(false)
    }
  }

  const fetchAssignments = async () => {
    try {
      const res = await fetch(`${API_BASE}/assignments/${encodeURIComponent(module)}/${encodeURIComponent(presentation)}`)
      if (!res.ok) throw new Error('Failed to load assignments')
      const data = await res.json()
      setAssignments(Array.isArray(data) ? data : [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error loading assignments')
    }
  }

  const fetchSubmissions = async (assignmentId: number) => {
    setSubmissionLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/assignments/${assignmentId}/all-submissions`)
      if (!res.ok) throw new Error('Failed to load submission list')
      const data = await res.json()
      setSubmissions(Array.isArray(data) ? data : [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error loading submissions')
      setSubmissions([])
    } finally {
      setSubmissionLoading(false)
    }
  }

  const handleOpenSubmissions = async (assignment: AssignmentRecord) => {
    setSelectedAssignment(assignment)
    await fetchSubmissions(assignment.id_assessment)
    setSubmissionDialogOpen(true)
  }

  const handleCloseSubmissions = () => {
    setSelectedAssignment(null)
    setSubmissions([])
    setGradeScore('')
    setGradeFeedback('')
    setSubmissionDialogOpen(false)
  }

  const handleGradeSubmission = async (submission: SubmissionRecord) => {
    if (gradeScore === '' || Number(gradeScore) < 0 || Number(gradeScore) > 100) {
      setError('Score must be between 0 and 100')
      return
    }
    setGrading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/assignments/${submission.id_assessment}/grade/${submission.student_id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ score: Number(gradeScore), feedback: gradeFeedback }),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || 'Failed to submit grade')
      }
      await fetchSubmissions(submission.id_assessment)
      setGradeScore('')
      setGradeFeedback('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error submitting grade')
    } finally {
      setGrading(false)
    }
  }

  const handleDeleteAssignment = async (assignment: AssignmentRecord) => {
    setSaving(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/assignments/${assignment.id_assessment}`, {
        method: 'DELETE',
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || 'Failed to delete assignment')
      }
      await fetchAssignments()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error deleting assignment')
    } finally {
      setSaving(false)
    }
  }

  if (!module || !presentation) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="info">Select module and presentation to view assignments.</Alert>
      </Box>
    )
  }

  return (
    <Box sx={{ p: 2, display: 'flex', flexDirection: 'column', gap: 2, minHeight: '100%' }}>
      <Box>
        <Typography variant="h6" fontWeight={700} sx={{ mb: 1 }}>
          Assignments
        </Typography>
        <Typography color="text.secondary" sx={{ maxWidth: 680 }}>
          Manage assignments for {courseCode}. Enter assignment title and description to create an assignment for this presentation.
        </Typography>
      </Box>

      {error && <Alert severity="error">{error}</Alert>}

      <Card sx={{ p: 2, bgcolor: 'background.paper', border: '1px solid', borderColor: 'divider' }}>
        <Typography variant="subtitle1" fontWeight={600} sx={{ mb: 2 }}>
          Create new assignment
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel id="assignment-type-label">Type</InputLabel>
              <Select
                labelId="assignment-type-label"
                value={type}
                label="Type"
                size="small"
                onChange={(event) => setType(event.target.value)}
              >
                <MenuItem value="TMA">TMA</MenuItem>
                <MenuItem value="CMA">CMA</MenuItem>
                <MenuItem value="Exam">Exam</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              label="Weight"
              type="number"
              size="small"
              fullWidth
              value={weight}
              onChange={(event) => setWeight(Number(event.target.value))}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              label="Due date (day offset)"
              type="number"
              size="small"
              fullWidth
              value={dueDate}
              onChange={(event) => setDueDate(Number(event.target.value))}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              label="Max file size (MB)"
              type="number"
              size="small"
              fullWidth
              value={maxFileSizeMb}
              onChange={(event) => setMaxFileSizeMb(Number(event.target.value))}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              label="Assignment title"
              size="small"
              fullWidth
              value={title}
              onChange={(event) => setTitle(event.target.value)}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              label="Assignment description"
              size="small"
              fullWidth
              multiline
              minRows={4}
              value={description}
              onChange={(event) => setDescription(event.target.value)}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              label="Allowed formats"
              size="small"
              fullWidth
              value={allowedFormats}
              onChange={(event) => setAllowedFormats(event.target.value)}
              helperText="Comma-separated list, e.g. pdf, docx"
            />
          </Grid>
          <Grid item xs={12}>
            <Button variant="contained" onClick={handleSaveAssignment} disabled={saving}>
              {saving ? 'Saving…' : 'Create assignment'}
            </Button>
          </Grid>
        </Grid>
      </Card>

      <Card sx={{ p: 2, bgcolor: 'background.paper', border: '1px solid', borderColor: 'divider' }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" fontWeight={600}>
              Assignment metadata
            </Typography>
            <Typography color="text.secondary" sx={{ mt: 1 }}>
              Teacher: {teacherId} · Course: {courseCode}
            </Typography>
          </Grid>
          <Grid item xs={12} md={6}>
            <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" justifyContent="flex-end">
              <Chip label={`Assignments: ${assignments.length}`} color="primary" />
            </Stack>
          </Grid>
        </Grid>
      </Card>

      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
        <Typography variant="subtitle1" fontWeight={600}>
          Assignments
        </Typography>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : assignments.length === 0 ? (
          <Alert severity="info">No assignments found for this class.</Alert>
        ) : (
          <TableContainer component={Paper} sx={{ borderRadius: 2 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>ID</TableCell>
                  <TableCell>Title</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Weight</TableCell>
                  <TableCell>Due offset</TableCell>
                  <TableCell>Formats</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {assignments.map((item) => (
                  <TableRow key={item._id}>
                    <TableCell>{item.id_assessment}</TableCell>
                    <TableCell>{item.title || '—'}</TableCell>
                    <TableCell>{item.type}</TableCell>
                    <TableCell>{item.weight}</TableCell>
                    <TableCell>{item.due_date}</TableCell>
                    <TableCell>{item.allowed_formats?.join(', ')}</TableCell>
                    <TableCell>{item.status}</TableCell>
                    <TableCell>{new Date(item.created_at).toLocaleString()}</TableCell>
                    <TableCell align="right" sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
                      <Button size="small" variant="outlined" onClick={() => handleOpenSubmissions(item)}>
                        View submissions
                      </Button>
                      <IconButton size="small" color="error" onClick={() => handleDeleteAssignment(item)}>
                        <DeleteOutlinedIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Box>

      <Dialog open={submissionDialogOpen} onClose={handleCloseSubmissions} fullWidth maxWidth="md">
        <DialogTitle>
          Submissions for assignment {selectedAssignment?.title ? `- ${selectedAssignment.title}` : ''}
        </DialogTitle>
        <DialogContent dividers>
          {submissionLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : submissions.length === 0 ? (
            <Alert severity="info">No submissions found for this assignment.</Alert>
          ) : (
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Student ID</TableCell>
                  <TableCell>Submitted at</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Score</TableCell>
                  <TableCell>Feedback</TableCell>
                  <TableCell>File / Content</TableCell>
                  <TableCell align="right">Grade</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {submissions.map((submission) => (
                  <TableRow key={submission._id}>
                    <TableCell>{submission.student_id}</TableCell>
                    <TableCell>{new Date(submission.submitted_at).toLocaleString()}</TableCell>
                    <TableCell>{submission.status}</TableCell>
                    <TableCell>{submission.score != null ? `${submission.score}%` : '—'}</TableCell>
                    <TableCell>{submission.feedback || '—'}</TableCell>
                    <TableCell sx={{ maxWidth: 280, whiteSpace: 'pre-wrap', overflowWrap: 'break-word' }}>
                      {submission.file_name ? (
                        <Button
                          component="a"
                          href={`${FILE_BASE}${submission.file_url}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          size="small"
                          variant="outlined"
                        >
                          {submission.file_name}
                        </Button>
                      ) : (
                        submission.content || '—'
                      )}
                    </TableCell>
                    <TableCell align="right">
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, minWidth: 180 }}>
                        <TextField
                          label="Score"
                          type="number"
                          size="small"
                          value={gradeScore}
                          onChange={(event) => setGradeScore(event.target.value === '' ? '' : Number(event.target.value))}
                          inputProps={{ min: 0, max: 100 }}
                        />
                        <TextField
                          label="Feedback"
                          size="small"
                          multiline
                          minRows={2}
                          value={gradeFeedback}
                          onChange={(event) => setGradeFeedback(event.target.value)}
                        />
                        <Button
                          size="small"
                          variant="contained"
                          onClick={() => handleGradeSubmission(submission)}
                          disabled={grading}
                        >
                          {grading ? 'Grading…' : 'Grade'}
                        </Button>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseSubmissions}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

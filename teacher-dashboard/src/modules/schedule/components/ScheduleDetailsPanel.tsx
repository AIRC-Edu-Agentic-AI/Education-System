import { Box, Button, Divider, FormControlLabel, MenuItem, Stack, Switch, TextField, Typography } from '@mui/material'
import type { ScheduleItem, ScheduleStatus } from '../../../types/domain'
import type { DeliveryMode } from './CalendarToolbar'

interface Props {
  schedule?: ScheduleItem
  canEdit: boolean
  onChange: (patch: Partial<ScheduleItem>) => void
  onClose: () => void
  onDelete: () => void
  onSave: () => void
}

export function ScheduleDetailsPanel({ schedule, canEdit, onChange, onClose, onDelete, onSave }: Props) {
  if (!schedule) {
    return (
      <Box sx={{ p: 2, border: '1px solid rgba(0,0,0,0.08)', borderRadius: 2, minWidth: 320 }}>
        <Typography sx={{ fontWeight: 700, mb: 1 }}>Session details</Typography>
        <Typography sx={{ color: 'text.secondary' }}>Select a session to view or edit full details.</Typography>
      </Box>
    )
  }

  return (
    <Box sx={{ p: 2, border: '1px solid rgba(0,0,0,0.08)', borderRadius: 2, minWidth: 320, display: 'flex', flexDirection: 'column', gap: 1.5 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <Typography sx={{ fontWeight: 700 }}>Session details</Typography>
        <Button size="small" onClick={onClose}>Close</Button>
      </Stack>

      <TextField
        size="small"
        label="Subject"
        value={schedule.subject ?? ''}
        onChange={(e) => onChange({ subject: e.target.value })}
        disabled={!canEdit}
      />
      <TextField
        size="small"
        label="Class"
        value={schedule.className ?? ''}
        onChange={(e) => onChange({ className: e.target.value })}
        disabled={!canEdit}
      />
      <TextField
        size="small"
        label="Teacher"
        value={schedule.teacher ?? ''}
        onChange={(e) => onChange({ teacher: e.target.value })}
        disabled={!canEdit}
      />
      <TextField
        size="small"
        type="date"
        label="Date"
        value={schedule.date ?? ''}
        onChange={(e) => onChange({ date: e.target.value })}
        InputLabelProps={{ shrink: true }}
        disabled={!canEdit}
      />
      <Stack direction="row" spacing={1}>
        <TextField
          size="small"
          type="time"
          label="Start"
          value={schedule.startTime ?? ''}
          onChange={(e) => onChange({ startTime: e.target.value })}
          InputLabelProps={{ shrink: true }}
          disabled={!canEdit}
          fullWidth
        />
        <TextField
          size="small"
          type="time"
          label="End"
          value={schedule.endTime ?? ''}
          onChange={(e) => onChange({ endTime: e.target.value })}
          InputLabelProps={{ shrink: true }}
          disabled={!canEdit}
          fullWidth
        />
      </Stack>
      <TextField
        size="small"
        label="Room"
        value={schedule.room ?? ''}
        onChange={(e) => onChange({ room: e.target.value })}
        disabled={!canEdit}
      />
      <TextField
        size="small"
        label="Meeting link"
        value={schedule.locationUrl ?? ''}
        onChange={(e) => onChange({ locationUrl: e.target.value })}
        disabled={!canEdit}
      />
      <TextField
        select
        size="small"
        label="Status"
        value={schedule.status ?? 'scheduled'}
        onChange={(e) => onChange({ status: e.target.value as ScheduleStatus })}
        disabled={!canEdit}
      >
        <MenuItem value="scheduled">Scheduled</MenuItem>
        <MenuItem value="completed">Completed</MenuItem>
        <MenuItem value="cancelled">Cancelled</MenuItem>
        <MenuItem value="rescheduled">Rescheduled</MenuItem>
      </TextField>
      <FormControlLabel
        control={<Switch checked={!!schedule.is_makeup} onChange={(e) => onChange({ is_makeup: e.target.checked })} disabled={!canEdit} />}
        label="Make-up session"
      />
      <TextField
        size="small"
        label="Note"
        value={schedule.note ?? ''}
        onChange={(e) => onChange({ note: e.target.value })}
        multiline
        minRows={3}
        disabled={!canEdit}
      />
      <Divider />
      <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
        <Button variant="contained" size="small" onClick={onSave} disabled={!canEdit}>
          Save
        </Button>
        <Button variant="outlined" size="small" color="error" onClick={onDelete} disabled={!canEdit}>
          Delete
        </Button>
      </Stack>
    </Box>
  )
}

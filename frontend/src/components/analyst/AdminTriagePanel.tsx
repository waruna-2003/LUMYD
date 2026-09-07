import { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  FormControl,
  Grid,
  InputLabel,
  LinearProgress,
  MenuItem,
  Paper,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import AutoFixHighOutlinedIcon from '@mui/icons-material/AutoFixHighOutlined';
import CheckCircleOutlinedIcon from '@mui/icons-material/CheckCircleOutlined';
import RefreshIcon from '@mui/icons-material/Refresh';
import ShieldOutlinedIcon from '@mui/icons-material/ShieldOutlined';
import WarningAmberOutlinedIcon from '@mui/icons-material/WarningAmberOutlined';

import { analystService } from '../../services/api';

interface EscalationItem {
  id: string;
  dataset_id: string;
  raw_query: string;
  confidence_score: number;
  predicted_task?: string | null;
  status: string;
  created_at: string;
}

interface QuotaStatus {
  date_utc: string;
  requests_used_today: number;
  daily_safety_limit: number;
  requests_remaining: number;
  total_all_time: number;
  percentage_used: number;
}

const ANALYTICAL_TASKS = [
  { value: 'root_cause', label: 'Root Cause Analysis (Why metrics changed / dropped / spiked)' },
  { value: 'ranking', label: 'Ranking / Top-K (Highest, lowest, best, worst)' },
  { value: 'comparison', label: 'Comparison (A vs B performance, multi-region / category)' },
  { value: 'trend', label: 'Trend / Time-Series (Over time, trajectory, monthly/quarterly)' },
  { value: 'distribution', label: 'Distribution (Spread, variance, breakdown across entities)' },
];

interface AdminTriagePanelProps {
  onEscalationCountChange?: (count: number) => void;
}

export function AdminTriagePanel({ onEscalationCountChange }: AdminTriagePanelProps) {
  const [escalations, setEscalations] = useState<EscalationItem[]>([]);
  const [quota, setQuota] = useState<QuotaStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [resolvingId, setResolvingId] = useState<string | null>(null);
  const [selectedTasks, setSelectedTasks] = useState<Record<string, string>>({});
  const [adminNotes, setAdminNotes] = useState<Record<string, string>>({});
  const [feedback, setFeedback] = useState<string | null>(null);

  const refreshData = async () => {
    setLoading(true);
    try {
      const [escRes, quotaRes] = await Promise.all([
        analystService.fetchPendingEscalations(),
        analystService.fetchQuotaStatus(),
      ]);
      setEscalations(escRes.data);
      setQuota(quotaRes.data);
      if (onEscalationCountChange) {
        onEscalationCountChange(escRes.data.length);
      }
    } catch {
      // Fallback silently if offline
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let isMounted = true;
    Promise.all([
      analystService.fetchPendingEscalations(),
      analystService.fetchQuotaStatus(),
    ])
      .then(([escRes, quotaRes]) => {
        if (!isMounted) return;
        setEscalations(escRes.data);
        setQuota(quotaRes.data);
        if (onEscalationCountChange) {
          onEscalationCountChange(escRes.data.length);
        }
      })
      .catch(() => {});

    return () => {
      isMounted = false;
    };
  }, [onEscalationCountChange]);

  const handleResolve = async (escalationId: string) => {
    const targetTask = selectedTasks[escalationId] || escalations.find((e) => e.id === escalationId)?.predicted_task || 'root_cause';
    const notes = adminNotes[escalationId] || 'Resolved via Admin Triage Panel';

    setResolvingId(escalationId);
    setFeedback(null);
    try {
      const response = await analystService.resolveEscalation({
        escalation_id: escalationId,
        target_task_name: targetTask,
        admin_notes: notes,
      });

      setFeedback(response.data?.message || 'Escalation resolved and added to active training samples.');
      // Refresh list
      await refreshData();
    } catch {
      setFeedback('Failed to resolve escalation. Please try again.');
    } finally {
      setResolvingId(null);
    }
  };

  return (
    <Paper
      variant="outlined"
      sx={{
        p: { xs: 2.5, md: 4 },
        my: 3,
        bgcolor: '#22201D',
        color: '#FAF7F2',
        borderColor: '#3D3833',
      }}
    >
      {/* Header */}
      <Stack direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Stack direction="row" spacing={1.5} sx={{ alignItems: 'center' }}>
          <Box
            sx={{
              width: 36,
              height: 36,
              borderRadius: 2,
              bgcolor: 'primary.main',
              display: 'grid',
              placeItems: 'center',
            }}
          >
            <ShieldOutlinedIcon fontSize="small" />
          </Box>
          <Box>
            <Typography variant="h5">Admin Triage & Active Learning</Typography>
            <Typography variant="body2" sx={{ color: '#BEB6AD' }}>
              Human-in-the-Loop workflow: Label novel queries to continuously train the neural router.
            </Typography>
          </Box>
        </Stack>

        <Button
          startIcon={<RefreshIcon />}
          size="small"
          variant="outlined"
          onClick={refreshData}
          disabled={loading}
          sx={{ borderColor: '#5C544C', color: '#D9D2CA' }}
        >
          {loading ? 'Refreshing...' : 'Refresh'}
        </Button>
      </Stack>

      {/* Quota Safeguard Card */}
      {quota && (
        <Card
          variant="outlined"
          sx={{
            mb: 4,
            bgcolor: '#2A2724',
            borderColor: '#423D37',
            color: '#FAF7F2',
          }}
        >
          <CardContent sx={{ p: 2.5 }}>
            <Stack direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
              <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 700, letterSpacing: '0.04em' }}>
                  GEMINI API FREE TIER SAFEGUARD
                </Typography>
                <Chip
                  label="15 RPM Throttle Active"
                  size="small"
                  sx={{ bgcolor: 'rgba(76, 175, 80, 0.15)', color: '#81C784', fontSize: '0.72rem' }}
                />
              </Stack>
              <Typography variant="body2" sx={{ color: '#BEB6AD' }}>
                {quota.requests_used_today} / {quota.daily_safety_limit} requests today ({quota.requests_remaining} remaining)
              </Typography>
            </Stack>

            <LinearProgress
              variant="determinate"
              value={Math.min(quota.percentage_used, 100)}
              sx={{
                height: 8,
                borderRadius: 4,
                bgcolor: '#3E3832',
                '& .MuiLinearProgress-bar': {
                  bgcolor: quota.percentage_used > 80 ? '#FF7043' : '#66BB6A',
                },
              }}
            />

            <Stack direction="row" spacing={3} sx={{ mt: 1.5, color: '#928A82', fontSize: '0.8rem' }}>
              <Typography variant="caption" sx={{ color: 'inherit' }}>
                Date (UTC): {quota.date_utc}
              </Typography>
              <Typography variant="caption" sx={{ color: 'inherit' }}>
                Total all-time requests: {quota.total_all_time}
              </Typography>
              <Typography variant="caption" sx={{ color: 'inherit' }}>
                Query Cache: Active (Zero API cost for repeats)
              </Typography>
            </Stack>
          </CardContent>
        </Card>
      )}

      {feedback && (
        <Alert
          severity="success"
          icon={<CheckCircleOutlinedIcon />}
          sx={{ mb: 3, bgcolor: 'rgba(76, 175, 80, 0.15)', color: '#FAF7F2', border: '1px solid #4CAF50' }}
          onClose={() => setFeedback(null)}
        >
          {feedback}
        </Alert>
      )}

      {/* Escalation Queue Section */}
      <Stack direction="row" spacing={1.5} sx={{ alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">Pending Escalation Queue</Typography>
        <Chip
          label={`${escalations.length} awaiting review`}
          size="small"
          color={escalations.length > 0 ? 'warning' : 'default'}
        />
      </Stack>

      {escalations.length === 0 ? (
        <Alert
          severity="info"
          sx={{
            bgcolor: '#2A2724',
            borderColor: '#3D3833',
            color: '#D9D2CA',
          }}
        >
          No pending escalations. All natural language queries are cleanly handled by the local router or auto-triaged!
        </Alert>
      ) : (
        <Stack spacing={2}>
          {escalations.map((item) => {
            const currentSelectedTask =
              selectedTasks[item.id] || item.predicted_task || 'root_cause';
            const isResolving = resolvingId === item.id;

            return (
              <Card
                key={item.id}
                variant="outlined"
                sx={{
                  bgcolor: '#2C2825',
                  borderColor: '#48423B',
                  color: '#FAF7F2',
                }}
              >
                <CardContent sx={{ p: 2.5 }}>
                  <Grid container spacing={2}>
                    {/* Left: Query Details */}
                    <Grid size={{ xs: 12, md: 7 }}>
                      <Stack direction="row" spacing={1} sx={{ alignItems: 'center', mb: 1 }}>
                        <WarningAmberOutlinedIcon sx={{ color: '#FFA726', fontSize: 20 }} />
                        <Typography variant="caption" sx={{ color: '#BEB6AD' }}>
                          Ticket #{item.id.slice(0, 8)} · Received {new Date(item.created_at).toLocaleString()}
                        </Typography>
                      </Stack>

                      <Typography
                        variant="body1"
                        sx={{
                          fontWeight: 600,
                          fontSize: '1.05rem',
                          color: '#FFFFFF',
                          mb: 1.5,
                          p: 1.5,
                          borderRadius: 1.5,
                          bgcolor: '#1E1C1A',
                          border: '1px solid #3A3530',
                        }}
                      >
                        "{item.raw_query}"
                      </Typography>

                      <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap' }}>
                        <Chip
                          label={`Initial Confidence: ${(item.confidence_score * 100).toFixed(1)}%`}
                          size="small"
                          sx={{ bgcolor: '#3D3833', color: '#D9D2CA' }}
                        />
                        {item.predicted_task && (
                          <Chip
                            label={`Predicted Guess: ${item.predicted_task}`}
                            size="small"
                            variant="outlined"
                            sx={{ borderColor: '#665E55', color: '#BEB6AD' }}
                          />
                        )}
                      </Stack>
                    </Grid>

                    {/* Right: Triage Action Form */}
                    <Grid size={{ xs: 12, md: 5 }}>
                      <Box sx={{ p: 2, borderRadius: 2, bgcolor: '#22201D', border: '1px solid #3D3833' }}>
                        <Typography variant="subtitle2" sx={{ mb: 1.5, color: '#D9D2CA' }}>
                          Assign Ground-Truth Intent:
                        </Typography>

                        <FormControl fullWidth size="small" sx={{ mb: 1.5 }}>
                          <InputLabel id={`task-select-${item.id}`} sx={{ color: '#BEB6AD' }}>
                            Analytical Intent
                          </InputLabel>
                          <Select
                            labelId={`task-select-${item.id}`}
                            value={currentSelectedTask}
                            label="Analytical Intent"
                            onChange={(e) =>
                              setSelectedTasks((prev) => ({
                                ...prev,
                                [item.id]: e.target.value,
                              }))
                            }
                            sx={{
                              bgcolor: '#2C2825',
                              color: '#FAF7F2',
                              '& .MuiOutlinedInput-notchedOutline': { borderColor: '#5C544C' },
                            }}
                          >
                            {ANALYTICAL_TASKS.map((t) => (
                              <MenuItem key={t.value} value={t.value}>
                                {t.label}
                              </MenuItem>
                            ))}
                          </Select>
                        </FormControl>

                        <TextField
                          placeholder="Optional notes (e.g., Sinhala slang phrasing)"
                          size="small"
                          fullWidth
                          value={adminNotes[item.id] || ''}
                          onChange={(e) =>
                            setAdminNotes((prev) => ({
                              ...prev,
                              [item.id]: e.target.value,
                            }))
                          }
                          sx={{
                            mb: 2,
                            '& .MuiOutlinedInput-root': {
                              bgcolor: '#2C2825',
                              color: '#FAF7F2',
                              '& fieldset': { borderColor: '#5C544C' },
                            },
                          }}
                        />

                        <Button
                          fullWidth
                          variant="contained"
                          startIcon={
                            isResolving ? (
                              <CircularProgress size={18} color="inherit" />
                            ) : (
                              <AutoFixHighOutlinedIcon />
                            )
                          }
                          disabled={isResolving}
                          onClick={() => handleResolve(item.id)}
                          sx={{
                            bgcolor: 'primary.main',
                            fontWeight: 600,
                            py: 1,
                          }}
                        >
                          {isResolving ? 'Training & Re-warming...' : 'Resolve & Add to Training'}
                        </Button>
                      </Box>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            );
          })}
        </Stack>
      )}

      <Divider sx={{ my: 4, borderColor: '#3D3833' }} />

      {/* Instructional Footer */}
      <Typography variant="caption" sx={{ color: '#8A827A' }}>
        * When you click "Resolve & Add to Training", this query is appended to the selected task in PostgreSQL and the SentenceTransformer prototype centroid cache is immediately re-warmed. Future identical or semantically similar queries will execute locally on CPU with zero Gemini API calls.
      </Typography>
    </Paper>
  );
}

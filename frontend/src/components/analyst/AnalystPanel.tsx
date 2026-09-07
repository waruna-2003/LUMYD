import { useState, type FormEvent } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  FormControl,
  Grid,
  InputLabel,
  LinearProgress,
  MenuItem,
  Paper,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';

import { datasetService } from '../../services/api';
import AutoAwesomeOutlinedIcon from '@mui/icons-material/AutoAwesomeOutlined';
import BoltOutlinedIcon from '@mui/icons-material/BoltOutlined';
import HourglassTopOutlinedIcon from '@mui/icons-material/HourglassTopOutlined';
import LightbulbOutlinedIcon from '@mui/icons-material/LightbulbOutlined';
import TranslateOutlinedIcon from '@mui/icons-material/TranslateOutlined';

interface DatasetOption {
  id: string;
  filename: string;
  status: string;
}

interface EvidenceObservation {
  fact_id: number;
  relationship_id: number;
  factor: string;
  metric_value: number;
  relationship_strength: number;
  contribution_score: number;
  relevance_score: number;
}

export interface RoutingInfo {
  route: 'AUTOMATED_EXECUTION' | 'HUMAN_ESCALATION';
  confidence: number;
  resolved_by: 'local_router' | 'gemini_triage' | 'pending_triage';
  escalated: boolean;
}

export interface NarrativeResponse {
  headline: string;
  narrative_text: string;
  key_takeaways: string[];
  language_detected: 'english' | 'singlish' | 'sinhala';
}

export interface RankingRow {
  rank: number;
  entity: string;
  metric_value: number;
  metric_mean: number;
  record_count: number;
  share_pct: number;
  cumulative_share_pct: number;
  diff_from_avg: number;
}

export interface TaskResultData {
  task: string;
  metric?: string;
  dimension?: string;
  total_value?: number;
  average_per_entity?: number;
  top_entity?: {
    entity: string;
    metric_value: number;
    share_pct: number;
  };
  bottom_entity?: {
    entity: string;
    metric_value: number;
  };
  table_data?: RankingRow[];
  total_entities_analyzed?: number;
  entity_a?: {
    name: string;
    value: number;
    record_count: number;
  };
  entity_b?: {
    name: string;
    value: number;
    record_count: number;
  };
  delta?: number;
  percentage_difference?: number;
  winner?: string;
  winner_margin?: number;
  primary_driver?: {
    dimension: string;
    underperforming_category: string;
    underperforming_mean: number;
    top_performing_category: string;
    top_performing_mean: number;
    variance_impact_score: number;
  };
  trajectory?: string;
  overall_growth_pct?: number;
  peak_period?: {
    period: string;
    value: number;
  };
  trough_period?: {
    period: string;
    value: number;
  };
  mean?: number;
  median?: number;
  iqr?: number;
  pareto_share_top_20pct?: number;
}

export interface AnalystResult {
  query_id: number;
  structured_query: {
    intent: string;
    target_metric: string;
    dimensions: string[];
    filters: Record<string, unknown>;
  };
  evidence_package: {
    status?: string;
    message?: string;
    escalation_id?: string;
    observations: EvidenceObservation[];
  };
  routing_info?: RoutingInfo;
  narrative?: NarrativeResponse;
  task_result?: TaskResultData;
}

interface AnalystPanelProps {
  datasets: DatasetOption[];
}

export function AnalystPanel({ datasets }: AnalystPanelProps) {
  const availableDatasets = datasets.filter((dataset) => dataset.status === 'processed');
  const [datasetId, setDatasetId] = useState('');
  const [question, setQuestion] = useState('');
  const [result, setResult] = useState<AnalystResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const activeDatasetId = availableDatasets.some(
    (dataset) => dataset.id === datasetId
  )
    ? datasetId
    : (availableDatasets[0]?.id ?? '');

  const submitQuestion = async (event: FormEvent) => {
    event.preventDefault();
    if (!activeDatasetId || !question.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const response = await datasetService.askAnalyst(activeDatasetId, question.trim());
      setResult(response.data);
    } catch {
      setError('LUMYD could not answer that question. Try naming a metric or dimension from the schema.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper variant="outlined" sx={{ p: { xs: 2.5, md: 4 }, my: 3, bgcolor: '#282522', color: '#FAF7F2', borderColor: '#282522' }}>
      <Stack direction="row" spacing={1.5} sx={{ alignItems: 'center', mb: 1 }}>
        <Box sx={{ width: 34, height: 34, borderRadius: 2, bgcolor: 'primary.main', display: 'grid', placeItems: 'center' }}>
          <AutoAwesomeOutlinedIcon fontSize="small" />
        </Box>
        <Typography variant="h5">Ask LUMYD</Typography>
      </Stack>
      <Typography sx={{ mb: 3, color: '#BEB6AD', maxWidth: 650 }}>
        Ask a focused business question. LUMYD will retrieve and rank the strongest evidence in your data.
      </Typography>

      {availableDatasets.length === 0 ? (
        <Alert severity="info">Upload and process a dataset before asking questions.</Alert>
      ) : (
        <Box component="form" onSubmit={submitQuestion}>
          <Stack spacing={2}>
            <FormControl fullWidth sx={{ '& .MuiOutlinedInput-root': { bgcolor: '#FCFAF6' } }}>
              <InputLabel id="analyst-dataset-label">Dataset</InputLabel>
              <Select
                labelId="analyst-dataset-label"
                value={activeDatasetId}
                label="Dataset"
                onChange={(event) => {
                  setDatasetId(event.target.value);
                  setResult(null);
                }}
              >
                {availableDatasets.map((dataset) => (
                  <MenuItem key={dataset.id} value={dataset.id}>
                    {dataset.filename}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              label="Business question"
              placeholder="What are the top regions by sales amount and why?"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              multiline
              minRows={2}
              fullWidth
              sx={{ '& .MuiOutlinedInput-root': { bgcolor: '#FCFAF6' } }}
            />
            <Button
              type="submit"
              variant="contained"
              disabled={loading || !activeDatasetId || !question.trim()}
              sx={{ alignSelf: 'flex-start', minWidth: 160 }}
            >
              {loading ? <CircularProgress size={24} color="inherit" /> : 'Analyze Question'}
            </Button>
          </Stack>
        </Box>
      )}

      {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
      {result && <AnalystAnswer result={result} />}
    </Paper>
  );
}

function AnalystAnswer({ result }: { result: AnalystResult }) {
  const isEscalated =
    result.routing_info?.escalated || result.evidence_package?.status === 'ESCALATED';

  if (isEscalated) {
    return (
      <Box sx={{ mt: 4, pt: 3, borderTop: '1px solid #48433E' }}>
        <Alert
          severity="warning"
          icon={<HourglassTopOutlinedIcon />}
          sx={{
            bgcolor: 'rgba(255, 179, 0, 0.12)',
            border: '1px solid rgba(255, 179, 0, 0.4)',
            color: '#FAF7F2',
            '& .MuiAlert-icon': { color: '#FFB300' },
          }}
        >
          <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
            {result.narrative?.headline || 'Query Diverted to Triage Queue'}
          </Typography>
          <Typography variant="body2" sx={{ mt: 0.5, color: '#E0D8D0' }}>
            {result.narrative?.narrative_text ||
              result.evidence_package?.message ||
              'This question was out of scope or below neural router confidence. It has been recorded for review.'}
          </Typography>
          {result.evidence_package?.escalation_id && (
            <Chip
              label={`Escalation Ticket #${result.evidence_package.escalation_id.slice(0, 8)}`}
              size="small"
              sx={{ mt: 1.5, bgcolor: '#48433E', color: '#FAF7F2' }}
            />
          )}
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ mt: 4, pt: 3, borderTop: '1px solid #48433E' }}>
      {/* Routing Chips */}
      <Stack direction="row" spacing={1} useFlexGap sx={{ mb: 2.5, flexWrap: 'wrap', alignItems: 'center' }}>
        {result.routing_info?.resolved_by === 'local_router' && (
          <Chip
            icon={<BoltOutlinedIcon />}
            label={`Local Router (${(result.routing_info.confidence * 100).toFixed(0)}% match · Zero Cost)`}
            color="success"
            variant="filled"
          />
        )}
        {result.routing_info?.resolved_by === 'gemini_triage' && (
          <Chip
            icon={<AutoAwesomeOutlinedIcon />}
            label="Gemini 3.6 Flash Fallback · Learned"
            color="secondary"
            variant="filled"
          />
        )}
        <Chip label={`Query #${result.query_id}`} variant="outlined" sx={{ color: '#D9D2CA', borderColor: '#625B54' }} />
        <Chip label={`Intent: ${result.structured_query.intent}`} color="primary" />
        <Chip label={`Metric: ${result.structured_query.target_metric}`} color="secondary" />
        {result.structured_query.dimensions.map((dimension) => (
          <Chip key={dimension} label={`Dimension: ${dimension}`} />
        ))}
      </Stack>

      {/* 1. Multilingual Human Narrative Card */}
      {result.narrative && (
        <Card
          variant="outlined"
          sx={{
            mb: 3.5,
            bgcolor: '#1E1C1A',
            borderColor: '#5C544C',
            color: '#FAF7F2',
            boxShadow: '0 4px 20px rgba(0,0,0,0.25)',
          }}
        >
          <CardContent sx={{ p: { xs: 2, md: 3 } }}>
            <Stack direction="row" spacing={1} sx={{ alignItems: 'center', mb: 1.5 }}>
              <TranslateOutlinedIcon sx={{ color: 'primary.main', fontSize: 20 }} />
              <Typography variant="overline" sx={{ fontWeight: 700, color: 'primary.light', letterSpacing: '0.08em' }}>
                AI EXECUTIVE NARRATIVE · {result.narrative.language_detected.toUpperCase()}
              </Typography>
            </Stack>

            <Typography variant="h6" sx={{ fontWeight: 700, color: '#FFFFFF', mb: 1.5 }}>
              {result.narrative.headline}
            </Typography>

            <Typography
              variant="body1"
              sx={{
                color: '#E0D8D0',
                lineHeight: 1.6,
                fontSize: '1rem',
                p: 2,
                borderRadius: 2,
                bgcolor: '#282522',
                border: '1px solid #3E3934',
                mb: 2,
              }}
            >
              {result.narrative.narrative_text}
            </Typography>

            {result.narrative.key_takeaways && result.narrative.key_takeaways.length > 0 && (
              <Box>
                <Typography variant="caption" sx={{ fontWeight: 700, color: '#BEB6AD', textTransform: 'uppercase' }}>
                  Key Findings
                </Typography>
                <Stack spacing={1} sx={{ mt: 1 }}>
                  {result.narrative.key_takeaways.map((takeaway, idx) => (
                    <Stack key={idx} direction="row" spacing={1} sx={{ alignItems: 'flex-start' }}>
                      <LightbulbOutlinedIcon sx={{ color: '#FFCA28', fontSize: 18, mt: 0.2 }} />
                      <Typography variant="body2" sx={{ color: '#FAF7F2' }}>
                        {takeaway}
                      </Typography>
                    </Stack>
                  ))}
                </Stack>
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {/* 2. Dedicated Analytical Task Visualizer */}
      {result.task_result && <TaskVisualizer taskResult={result.task_result} />}

      {/* 3. Deep Statistical Evidence Breakdown */}
      {result.evidence_package.observations.length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="subtitle2" sx={{ color: '#BEB6AD', mb: 1.5, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Statistical Evidence Points ({result.evidence_package.observations.length} observed)
          </Typography>
          <Stack spacing={1.5}>
            {result.evidence_package.observations.slice(0, 5).map((observation) => (
              <Card
                variant="outlined"
                key={`${observation.fact_id}-${observation.relationship_id}`}
                sx={{ bgcolor: '#2C2825', borderColor: '#48423B', color: '#FAF7F2' }}
              >
                <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                  <Typography sx={{ fontWeight: 'bold' }}>{observation.factor}</Typography>
                  <Typography variant="h6">
                    {observation.metric_value.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#BEB6AD' }}>
                    Contribution {(observation.contribution_score * 100).toFixed(1)}% · Relationship strength{' '}
                    {(observation.relationship_strength * 100).toFixed(1)}%
                  </Typography>
                </CardContent>
              </Card>
            ))}
          </Stack>
        </Box>
      )}
    </Box>
  );
}

function TaskVisualizer({ taskResult }: { taskResult: TaskResultData }) {
  const task = taskResult.task;

  if (task === 'ranking' && taskResult.table_data) {
    return (
      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1.5, color: '#FAF7F2' }}>
          Top {taskResult.table_data.length} Ranked by {taskResult.metric}
        </Typography>
        <TableContainer component={Paper} variant="outlined" sx={{ bgcolor: '#24211E', borderColor: '#48423B' }}>
          <Table size="small">
            <TableHead>
              <TableRow sx={{ '& th': { color: '#BEB6AD', borderColor: '#3D3833', fontWeight: 700 } }}>
                <TableCell>Rank</TableCell>
                <TableCell>{taskResult.dimension}</TableCell>
                <TableCell align="right">{taskResult.metric}</TableCell>
                <TableCell align="right">Share of Total</TableCell>
                <TableCell align="right">Gap from Average</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {taskResult.table_data.map((row: RankingRow) => (
                <TableRow key={row.rank} sx={{ '& td': { color: '#FAF7F2', borderColor: '#332F2B' } }}>
                  <TableCell>
                    <Chip
                      label={`#${row.rank}`}
                      size="small"
                      color={row.rank === 1 ? 'primary' : 'default'}
                      sx={{ fontWeight: 700, height: 22 }}
                    />
                  </TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>{row.entity}</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 700 }}>
                    {row.metric_value.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                  </TableCell>
                  <TableCell align="right">
                    <Stack direction="row" spacing={1} sx={{ alignItems: 'center', justifyContent: 'flex-end' }}>
                      <Box sx={{ width: 60 }}>
                        <LinearProgress
                          variant="determinate"
                          value={Math.min(row.share_pct, 100)}
                          sx={{ height: 6, borderRadius: 3, bgcolor: '#3D3833' }}
                        />
                      </Box>
                      <Typography variant="body2" sx={{ minWidth: 40, color: '#BEB6AD' }}>
                        {row.share_pct}%
                      </Typography>
                    </Stack>
                  </TableCell>
                  <TableCell align="right" sx={{ color: row.diff_from_avg >= 0 ? '#81C784' : '#FF8A65' }}>
                    {row.diff_from_avg >= 0 ? `+${row.diff_from_avg.toLocaleString()}` : row.diff_from_avg.toLocaleString()}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
    );
  }

  if (task === 'comparison' && taskResult.entity_a && taskResult.entity_b) {
    const ea = taskResult.entity_a;
    const eb = taskResult.entity_b;
    return (
      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1.5, color: '#FAF7F2' }}>
          Head-to-Head Comparison: {ea.name} vs {eb.name}
        </Typography>
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, sm: 6 }}>
            <Card
              variant="outlined"
              sx={{
                p: 2,
                bgcolor: taskResult.winner === ea.name ? 'rgba(76, 175, 80, 0.08)' : '#2A2724',
                borderColor: taskResult.winner === ea.name ? '#4CAF50' : '#48423B',
                color: '#FAF7F2',
              }}
            >
              <Stack direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h6">{ea.name}</Typography>
                {taskResult.winner === ea.name && (
                  <Chip label="Winner" size="small" color="success" sx={{ fontWeight: 700 }} />
                )}
              </Stack>
              <Typography variant="h4" sx={{ my: 1, fontWeight: 700 }}>
                {ea.value.toLocaleString()}
              </Typography>
              <Typography variant="caption" sx={{ color: '#BEB6AD' }}>
                {ea.record_count} records in dataset
              </Typography>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <Card
              variant="outlined"
              sx={{
                p: 2,
                bgcolor: taskResult.winner === eb.name ? 'rgba(76, 175, 80, 0.08)' : '#2A2724',
                borderColor: taskResult.winner === eb.name ? '#4CAF50' : '#48423B',
                color: '#FAF7F2',
              }}
            >
              <Stack direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h6">{eb.name}</Typography>
                {taskResult.winner === eb.name && (
                  <Chip label="Winner" size="small" color="success" sx={{ fontWeight: 700 }} />
                )}
              </Stack>
              <Typography variant="h4" sx={{ my: 1, fontWeight: 700 }}>
                {eb.value.toLocaleString()}
              </Typography>
              <Typography variant="caption" sx={{ color: '#BEB6AD' }}>
                {eb.record_count} records in dataset
              </Typography>
            </Card>
          </Grid>
        </Grid>
      </Box>
    );
  }

  if (task === 'root_cause' && taskResult.primary_driver) {
    const driver = taskResult.primary_driver;
    return (
      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1.5, color: '#FAF7F2' }}>
          Root Cause & Variance Decomposition
        </Typography>
        <Card variant="outlined" sx={{ bgcolor: '#2A2724', borderColor: '#48423B', p: 2, color: '#FAF7F2' }}>
          <Typography variant="subtitle2" sx={{ color: '#FFA726', fontWeight: 700 }}>
            PRIMARY DRIVER: {driver.dimension}
          </Typography>
          <Typography variant="body1" sx={{ mt: 1 }}>
            Underperforming category <strong>"{driver.underperforming_category}"</strong> averaged{' '}
            {driver.underperforming_mean.toLocaleString()} versus top performer{' '}
            <strong>"{driver.top_performing_category}"</strong> at {driver.top_performing_mean.toLocaleString()}.
          </Typography>
          <Chip
            label={`Variance Impact Score: ${driver.variance_impact_score}%`}
            size="small"
            color="warning"
            sx={{ mt: 1.5, fontWeight: 700 }}
          />
        </Card>
      </Box>
    );
  }

  if (task === 'trend') {
    return (
      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1.5, color: '#FAF7F2' }}>
          Time-Series Trajectory: {taskResult.trajectory} ({taskResult.overall_growth_pct}%)
        </Typography>
        <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
          {taskResult.peak_period && (
            <Chip
              label={`Peak: ${taskResult.peak_period.period} (${taskResult.peak_period.value.toLocaleString()})`}
              color="success"
              variant="outlined"
            />
          )}
          {taskResult.trough_period && (
            <Chip
              label={`Trough: ${taskResult.trough_period.period} (${taskResult.trough_period.value.toLocaleString()})`}
              color="error"
              variant="outlined"
            />
          )}
        </Stack>
      </Box>
    );
  }

  if (task === 'distribution' && taskResult.mean !== undefined && taskResult.median !== undefined) {
    return (
      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1.5, color: '#FAF7F2' }}>
          Statistical Distribution Overview
        </Typography>
        <Grid container spacing={1.5}>
          <Grid size={{ xs: 6, sm: 3 }}>
            <Card variant="outlined" sx={{ p: 1.5, bgcolor: '#2A2724', borderColor: '#48423B', color: '#FAF7F2' }}>
              <Typography variant="caption" sx={{ color: '#BEB6AD' }}>Mean</Typography>
              <Typography variant="h6">{taskResult.mean.toLocaleString()}</Typography>
            </Card>
          </Grid>
          <Grid size={{ xs: 6, sm: 3 }}>
            <Card variant="outlined" sx={{ p: 1.5, bgcolor: '#2A2724', borderColor: '#48423B', color: '#FAF7F2' }}>
              <Typography variant="caption" sx={{ color: '#BEB6AD' }}>Median</Typography>
              <Typography variant="h6">{taskResult.median.toLocaleString()}</Typography>
            </Card>
          </Grid>
          <Grid size={{ xs: 6, sm: 3 }}>
            <Card variant="outlined" sx={{ p: 1.5, bgcolor: '#2A2724', borderColor: '#48423B', color: '#FAF7F2' }}>
              <Typography variant="caption" sx={{ color: '#BEB6AD' }}>IQR</Typography>
              <Typography variant="h6">{(taskResult.iqr ?? 0).toLocaleString()}</Typography>
            </Card>
          </Grid>
          <Grid size={{ xs: 6, sm: 3 }}>
            <Card variant="outlined" sx={{ p: 1.5, bgcolor: '#2A2724', borderColor: '#48423B', color: '#FAF7F2' }}>
              <Typography variant="caption" sx={{ color: '#BEB6AD' }}>Top 20% Pareto Share</Typography>
              <Typography variant="h6">{taskResult.pareto_share_top_20pct}%</Typography>
            </Card>
          </Grid>
        </Grid>
      </Box>
    );
  }

  return null;
}

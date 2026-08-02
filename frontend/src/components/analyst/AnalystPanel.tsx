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
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material';

import { datasetService } from '../../services/api';

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

interface AnalystResult {
  query_id: number;
  structured_query: {
    intent: string;
    target_metric: string;
    dimensions: string[];
    filters: Record<string, unknown>;
  };
  evidence_package: {
    observations: EvidenceObservation[];
  };
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
    <Paper variant="outlined" sx={{ p: { xs: 2, md: 3 }, my: 4 }}>
      <Typography variant="h5" sx={{ fontWeight: 'bold' }} gutterBottom>
        Ask LUMYD
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 2 }}>
        Ask a business question and receive ranked evidence from the processed dataset.
      </Typography>

      {availableDatasets.length === 0 ? (
        <Alert severity="info">Upload and process a dataset before asking questions.</Alert>
      ) : (
        <Box component="form" onSubmit={submitQuestion}>
          <Stack spacing={2}>
            <FormControl fullWidth>
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
            />
            <Button
              type="submit"
              variant="contained"
              disabled={loading || !activeDatasetId || !question.trim()}
              sx={{ alignSelf: 'flex-start' }}
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
  return (
    <Box sx={{ mt: 3 }}>
      <Stack direction="row" spacing={1} useFlexGap sx={{ mb: 2, flexWrap: 'wrap' }}>
        <Chip label={`Query #${result.query_id}`} variant="outlined" />
        <Chip label={`Intent: ${result.structured_query.intent}`} color="primary" />
        <Chip label={`Metric: ${result.structured_query.target_metric}`} color="secondary" />
        {result.structured_query.dimensions.map((dimension) => (
          <Chip key={dimension} label={`Dimension: ${dimension}`} />
        ))}
      </Stack>

      <Typography variant="h6" gutterBottom>Ranked Evidence</Typography>
      {result.evidence_package.observations.length === 0 ? (
        <Alert severity="warning">
          No matching persisted evidence was found. Try another metric or dimension.
        </Alert>
      ) : (
        <Stack spacing={1.5}>
          {result.evidence_package.observations.map((observation) => (
            <Card variant="outlined" key={`${observation.fact_id}-${observation.relationship_id}`}>
              <CardContent>
                <Typography sx={{ fontWeight: 'bold' }}>{observation.factor}</Typography>
                <Typography variant="h6">
                  {observation.metric_value.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Contribution {(observation.contribution_score * 100).toFixed(1)}% · Relationship strength{' '}
                  {(observation.relationship_strength * 100).toFixed(1)}%
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Evidence: fact #{observation.fact_id}, relationship #{observation.relationship_id}
                </Typography>
              </CardContent>
            </Card>
          ))}
        </Stack>
      )}
    </Box>
  );
}

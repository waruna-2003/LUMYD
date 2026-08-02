import { Box, Card, CardContent, Chip, Divider, Grid, Typography } from '@mui/material';

export interface ColumnStats {
  mean: number | null;
  median: number | null;
  min_val: number | null;
  max_val: number | null;
  std_dev: number | null;
  unique_count: number;
  null_count: number;
  outlier_count: number;
  distribution: {
    labels: string[];
    values: number[];
  } | null;
}

interface ColumnProfileCardProps {
  name: string;
  type: string;
  stats: ColumnStats;
}

function formatNumber(value: number | null) {
  return value === null
    ? '—'
    : value.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

export function ColumnProfileCard({ name, type, stats }: ColumnProfileCardProps) {
  return (
    <Card sx={{ height: '100%', border: '1px solid', borderColor: 'divider', boxShadow: 'none' }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1, gap: 1 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }} noWrap>{name}</Typography>
          <Chip label={type} size="small" variant="outlined" color="primary" />
        </Box>
        <Divider />
        <Grid container spacing={1} sx={{ mt: 1 }}>
          <Grid size={6}>
            <Typography variant="caption" color="text.secondary">Unique Values</Typography>
            <Typography variant="body2">{stats.unique_count}</Typography>
          </Grid>
          <Grid size={6}>
            <Typography variant="caption" color="text.secondary">Nulls</Typography>
            <Typography variant="body2" color={stats.null_count > 0 ? 'error' : 'inherit'}>
              {stats.null_count}
            </Typography>
          </Grid>
          {stats.mean !== null && (
            <>
              <Grid size={6}>
                <Typography variant="caption" color="text.secondary">Mean</Typography>
                <Typography variant="body2">{formatNumber(stats.mean)}</Typography>
              </Grid>
              <Grid size={6}>
                <Typography variant="caption" color="text.secondary">Median</Typography>
                <Typography variant="body2">{formatNumber(stats.median)}</Typography>
              </Grid>
              <Grid size={6}>
                <Typography variant="caption" color="text.secondary">Range</Typography>
                <Typography variant="body2">
                  {formatNumber(stats.min_val)}–{formatNumber(stats.max_val)}
                </Typography>
              </Grid>
              <Grid size={6}>
                <Typography variant="caption" color="text.secondary">Outliers</Typography>
                <Typography variant="body2" color={stats.outlier_count > 0 ? 'warning.main' : 'inherit'}>
                  {stats.outlier_count}
                </Typography>
              </Grid>
            </>
          )}
        </Grid>
      </CardContent>
    </Card>
  );
}

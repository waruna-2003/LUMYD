import {
  Chip,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { ColumnProfileCard, type ColumnStats } from './ColumnProfileCard';

export interface ColumnMeta {
  id: number;
  name: string;
  data_type: string;
  python_type: string | null;
  is_nullable: boolean;
  technical_type: string | null;
  business_type: string | null;
  business_role: string | null;
  unit: string | null;
  aggregation: string[] | null;
  is_derived: boolean;
  is_redundant: boolean;
  stats: ColumnStats | null;
}

interface SchemaTableProps {
  columns: ColumnMeta[];
}

export function SchemaTable({ columns }: SchemaTableProps) {
  return (
    <Paper variant="outlined" sx={{ p: { xs: 2, md: 3 }, mt: 3 }}>
      <Typography variant="overline" color="text.secondary">Intelligence profile</Typography>
      <Typography variant="h5" sx={{ mb: 2 }}>Detected data structure</Typography>
      <Paper variant="outlined" sx={{ overflowX: 'auto' }}>
      <Table size="small" sx={{ minWidth: 920 }}>
        <TableHead>
          <TableRow>
            <TableCell>Column Name</TableCell>
            <TableCell>Business Type</TableCell>
            <TableCell>Business Role</TableCell>
            <TableCell>Unit</TableCell>
            <TableCell>Aggregations</TableCell>
            <TableCell>Python Type</TableCell>
            <TableCell>Nullable</TableCell>
            <TableCell>Derived</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {columns.map((column) => (
            <TableRow key={column.id}>
              <TableCell><strong>{column.name}</strong></TableCell>
              <TableCell>
                <Chip
                  label={column.data_type.toUpperCase()}
                  size="small"
                  color={column.data_type === 'numeric' ? 'primary' : 'secondary'}
                />
              </TableCell>
              <TableCell>{column.business_role ?? 'Unknown'}</TableCell>
              <TableCell>{column.unit ?? '—'}</TableCell>
              <TableCell>{column.aggregation?.join(', ') ?? '—'}</TableCell>
              <TableCell>{column.python_type ?? 'Unknown'}</TableCell>
              <TableCell>{column.is_nullable ? 'Yes' : 'No'}</TableCell>
              <TableCell>{column.is_derived ? 'Yes' : 'No'}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      </Paper>
      <Typography variant="h5" sx={{ mt: 4, mb: 2 }}>
        Column knowledge profiles
      </Typography>
      <Grid container spacing={2}>
        {columns.map((column) => (
          <Grid size={{ xs: 12, sm: 6, md: 4 }} key={column.id}>
            {column.stats ? (
              <ColumnProfileCard
                name={column.name}
                type={column.data_type}
                stats={column.stats}
              />
            ) : (
              <CardPlaceholder name={column.name} />
            )}
          </Grid>
        ))}
      </Grid>
    </Paper>
  );
}

function CardPlaceholder({ name }: { name: string }) {
  return (
    <Paper variant="outlined" sx={{ p: 2, height: '100%', boxSizing: 'border-box' }}>
      <Typography sx={{ fontWeight: 'bold' }}>{name}</Typography>
      <Typography variant="body2" color="text.secondary">Profile unavailable</Typography>
    </Paper>
  );
}

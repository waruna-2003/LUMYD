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
  stats: ColumnStats | null;
}

interface SchemaTableProps {
  columns: ColumnMeta[];
}

export function SchemaTable({ columns }: SchemaTableProps) {
  return (
    <Paper sx={{ p: 2, mt: 2 }}>
      <Typography variant="h6" gutterBottom>
        Detected Data Structure
      </Typography>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Column Name</TableCell>
            <TableCell>Business Type</TableCell>
            <TableCell>Python Type</TableCell>
            <TableCell>Nullable</TableCell>
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
              <TableCell>{column.python_type ?? 'Unknown'}</TableCell>
              <TableCell>{column.is_nullable ? 'Yes' : 'No'}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <Typography variant="h6" sx={{ mt: 3, mb: 2 }}>
        Column Knowledge Profiles
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

import { useEffect, useState } from 'react';
import { Box, Button, Container, Typography, Grid, Card, CardContent, Chip, Stack } from '@mui/material';
import DatasetOutlinedIcon from '@mui/icons-material/DatasetOutlined';
import { FileUpload } from './components/datasets/FileUpload';
import { SchemaTable, type ColumnMeta } from './components/datasets/SchemaTable';
import { datasetService } from './services/api';
import { AnalystPanel } from './components/analyst/AnalystPanel';

interface Dataset {
  id: string;
  filename: string;
  column_count: number;
  status: string;
}

function App() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [schema, setSchema] = useState<ColumnMeta[] | null>(null);
  const [selectedDataset, setSelectedDataset] = useState<string | null>(null);

  const loadDatasets = async () => {
    const res = await datasetService.fetchDatasets();
    setDatasets(res.data);
  };

  const loadSchema = async (datasetId: string) => {
    const response = await datasetService.fetchSchema(datasetId);
    setSelectedDataset(datasetId);
    setSchema(response.data);
    await loadDatasets();
  };

  useEffect(() => {
    datasetService.fetchDatasets().then((response) => {
      setDatasets(response.data);
    });
  }, []);

  useEffect(() => {
    if (!datasets.some((dataset) => dataset.status === 'processing')) return;

    const intervalId = window.setInterval(() => {
      datasetService.fetchDatasets().then((response) => {
        setDatasets(response.data);
      });
    }, 1000);

    return () => window.clearInterval(intervalId);
  }, [datasets]);

  return (
    <Container maxWidth="lg" sx={{ py: { xs: 3, md: 6 } }}>
      <Box component="header" sx={{ mb: { xs: 4, md: 6 } }}>
        <Stack direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 5 }}>
          <Stack direction="row" spacing={1.25} sx={{ alignItems: 'center' }}>
            <Box sx={{ width: 34, height: 34, borderRadius: 2, bgcolor: 'primary.main', display: 'grid', placeItems: 'center', color: 'primary.contrastText' }}>
              <Typography component="span" aria-label="Pickaxe" sx={{ color: 'inherit', fontSize: 21, lineHeight: 1 }}>
                ⛏
              </Typography>
            </Box>
            <Typography variant="h6">LUMYD</Typography>
          </Stack>
          <Chip label="Intelligence workspace" size="small" variant="outlined" />
        </Stack>
        <Typography variant="overline" color="primary.main" sx={{ fontWeight: 700, letterSpacing: '0.12em' }}>
          Let us mine your data
        </Typography>
        <Typography variant="h3" sx={{ maxWidth: 700, mt: 1 }}>
          Clear business evidence from complex datasets.
        </Typography>
        <Typography color="text.secondary" sx={{ maxWidth: 620, mt: 1.5, fontSize: '1.05rem' }}>
          Upload operational data, inspect its structure, and ask focused questions backed by traceable facts.
        </Typography>
      </Box>
      <FileUpload onUploadSuccess={loadDatasets} />
      <AnalystPanel datasets={datasets} />

      <Stack direction="row" sx={{ justifyContent: 'space-between', alignItems: 'end', mt: 6, mb: 2 }}>
        <Box>
          <Typography variant="overline" color="text.secondary">Library</Typography>
          <Typography variant="h5">Your datasets</Typography>
        </Box>
        <Typography variant="body2" color="text.secondary">{datasets.length} total</Typography>
      </Stack>
      <Grid container spacing={2}>
        {datasets.map((ds) => (
          <Grid size={{ xs: 12, sm: 6, md: 4 }} key={ds.id}>
            <Card variant="outlined" sx={{ height: '100%', transition: 'border-color 160ms ease', '&:hover': { borderColor: 'primary.light' } }}>
              <CardContent>
                <Stack direction="row" spacing={2} sx={{ justifyContent: 'space-between', alignItems: 'start' }}>
                  <Box sx={{ width: 36, height: 36, borderRadius: 2, bgcolor: 'rgba(201,111,59,0.10)', color: 'primary.main', display: 'grid', placeItems: 'center' }}>
                    <DatasetOutlinedIcon fontSize="small" />
                  </Box>
                  <Chip label={ds.status} size="small" color={ds.status === 'processed' ? 'success' : 'default'} variant="outlined" />
                </Stack>
                <Typography variant="h6" noWrap sx={{ mt: 2 }}>{ds.filename}</Typography>
                <Typography color="text.secondary" variant="body2">{ds.column_count} detected columns</Typography>
                <Button
                  size="small"
                  variant="text"
                  sx={{ mt: 1.5, px: 0 }}
                  disabled={ds.status === 'processing'}
                  onClick={() => loadSchema(ds.id)}
                >
                  View schema
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
      {selectedDataset && schema && <SchemaTable columns={schema} />}
    </Container>
  );
}

export default App;

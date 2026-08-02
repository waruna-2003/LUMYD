import { useEffect, useState } from 'react';
import { Button, Container, Typography, Grid, Card, CardContent } from '@mui/material';
import { FileUpload } from './components/datasets/FileUpload';
import { SchemaTable, type ColumnMeta } from './components/datasets/SchemaTable';
import { datasetService } from './services/api';

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
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Typography variant="h3" gutterBottom sx={{ fontWeight: 'bold' }}>LUMYD v1.0</Typography>
      <FileUpload onUploadSuccess={loadDatasets} />

      <Typography variant="h5" gutterBottom>Your Datasets</Typography>
      <Grid container spacing={2}>
        {datasets.map((ds) => (
          <Grid size={{ xs: 12, sm: 6, md: 4 }} key={ds.id}>
            <Card>
              <CardContent>
                <Typography variant="h6" noWrap>{ds.filename}</Typography>
                <Typography color="textSecondary">Columns: {ds.column_count}</Typography>
                <Typography variant="caption">Status: {ds.status}</Typography>
                <Button
                  size="small"
                  sx={{ display: 'block', mt: 1 }}
                  disabled={ds.status === 'processing'}
                  onClick={() => loadSchema(ds.id)}
                >
                  View Schema
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

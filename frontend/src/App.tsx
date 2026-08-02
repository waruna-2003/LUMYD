import { useEffect, useState } from 'react';
import { Container, Typography, Grid, Card, CardContent } from '@mui/material';
import { FileUpload } from './components/datasets/FileUpload';
import { datasetService } from './services/api';

interface Dataset {
  id: string;
  filename: string;
  column_count: number;
  status: string;
}

function App() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);

  const loadDatasets = async () => {
    const res = await datasetService.fetchDatasets();
    setDatasets(res.data);
  };

  useEffect(() => {
    datasetService.fetchDatasets().then((response) => {
      setDatasets(response.data);
    });
  }, []);

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
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Container>
  );
}

export default App;

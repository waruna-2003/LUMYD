import { useState, type ChangeEvent } from 'react';
import { Button, Box, Paper, LinearProgress, Typography } from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import { datasetService } from '../../services/api';

interface FileUploadProps {
  onUploadSuccess: () => void;
}

export function FileUpload({ onUploadSuccess }: FileUploadProps) {
  const [loading, setLoading] = useState(false);

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setLoading(true);
    try {
      await datasetService.upload(file);
      onUploadSuccess();
    } catch {
      alert('Upload failed. Please verify the file and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper variant="outlined" sx={{ p: { xs: 2.5, md: 3 }, mb: 3, position: 'relative', overflow: 'hidden', display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, alignItems: { xs: 'stretch', sm: 'center' }, justifyContent: 'space-between', gap: 2, borderStyle: 'dashed', bgcolor: 'rgba(252,250,246,0.7)' }}>
      <input
        accept=".csv,.xlsx,.xls"
        style={{ display: 'none' }}
        id="file-upload-input"
        type="file"
        onChange={handleFileChange}
      />
      <Box>
        <Typography variant="h6">Add a dataset</Typography>
        <Typography variant="body2" color="text.secondary">CSV or Excel · maximum 50 MB</Typography>
      </Box>
      <label htmlFor="file-upload-input">
        <Button variant="contained" component="span" startIcon={<UploadFileIcon />} disabled={loading}>
          {loading ? 'Processing…' : 'Choose file'}
        </Button>
      </label>
      {loading && <LinearProgress sx={{ position: 'absolute', left: 0, right: 0, bottom: 0 }} />}
    </Paper>
  );
}

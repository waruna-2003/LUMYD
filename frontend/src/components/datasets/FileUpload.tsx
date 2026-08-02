import { useState, type ChangeEvent } from 'react';
import { Button, Paper, LinearProgress } from '@mui/material';
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
    <Paper variant="outlined" sx={{ p: 4, textAlign: 'center', mb: 4 }}>
      <input
        accept=".csv,.xlsx,.xls"
        style={{ display: 'none' }}
        id="file-upload-input"
        type="file"
        onChange={handleFileChange}
      />
      <label htmlFor="file-upload-input">
        <Button variant="contained" component="span" startIcon={<UploadFileIcon />} disabled={loading}>
          {loading ? "Processing..." : "Upload Business Dataset"}
        </Button>
      </label>
      {loading && <LinearProgress sx={{ mt: 2 }} />}
    </Paper>
  );
}

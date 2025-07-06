import React from 'react';
import { DataGrid } from '@mui/x-data-grid';
import {
  Box,
  Paper,
  Typography,
  Button,
  Chip,
  Alert,
} from '@mui/material';
import { Download as DownloadIcon } from '@mui/icons-material';
import axios from 'axios';

function ResultsViewer({ results, title }) {
  if (!results) return null;

  const handleDownload = async () => {
    try {
      const response = await axios.get(`/api/download/${results.filename}`, {
        responseType: 'blob',
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', results.filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const columns = results.preview && results.preview.length > 0
    ? Object.keys(results.preview[0]).map((key) => ({
        field: key,
        headerName: key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' '),
        flex: 1,
        minWidth: 150,
      }))
    : [];

  return (
    <Paper sx={{ p: 3, mt: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box>
          <Typography variant="h6" gutterBottom>
            {title || 'Parse Results'}
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
            <Chip label={`${results.records} records`} color="primary" size="small" />
            {results.total_mb && (
              <Chip label={`${results.total_mb.toFixed(2)} MB total`} color="secondary" size="small" />
            )}
          </Box>
        </Box>
        <Button
          variant="contained"
          startIcon={<DownloadIcon />}
          onClick={handleDownload}
        >
          Download CSV
        </Button>
      </Box>

      {results.preview && results.preview.length > 0 ? (
        <Box sx={{ height: 400, width: '100%' }}>
          <DataGrid
            rows={results.preview.map((row, index) => ({ id: index, ...row }))}
            columns={columns}
            pageSize={10}
            rowsPerPageOptions={[10]}
            disableSelectionOnClick
            density="compact"
          />
        </Box>
      ) : (
        <Alert severity="info">No data found in the log file.</Alert>
      )}
    </Paper>
  );
}

export default ResultsViewer;
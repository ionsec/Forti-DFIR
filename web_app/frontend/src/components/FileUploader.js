import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Box, Typography, Paper } from '@mui/material';
import { CloudUpload as UploadIcon } from '@mui/icons-material';

function FileUploader({ onFileSelect, accept = '.txt,.log,.csv' }) {
  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      onFileSelect(acceptedFiles[0]);
    }
  }, [onFileSelect]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.txt', '.log'],
      'text/csv': ['.csv'],
    },
    maxFiles: 1,
  });

  return (
    <Paper
      {...getRootProps()}
      sx={{
        p: 4,
        textAlign: 'center',
        cursor: 'pointer',
        backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
        border: '2px dashed',
        borderColor: isDragActive ? 'primary.main' : 'divider',
        transition: 'all 0.2s',
        '&:hover': {
          backgroundColor: 'action.hover',
          borderColor: 'primary.main',
        },
      }}
    >
      <input {...getInputProps()} />
      <UploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
      <Typography variant="h6" gutterBottom>
        {isDragActive ? 'Drop the file here' : 'Drag & drop a log file here'}
      </Typography>
      <Typography variant="body2" color="text.secondary">
        or click to select a file
      </Typography>
      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
        Supported formats: .txt, .log, .csv
      </Typography>
    </Paper>
  );
}

export default FileUploader;
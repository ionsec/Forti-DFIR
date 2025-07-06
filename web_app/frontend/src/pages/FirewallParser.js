import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Stepper,
  Step,
  StepLabel,
  Alert,
  LinearProgress,
} from '@mui/material';
import FileUploader from '../components/FileUploader';
import ResultsViewer from '../components/ResultsViewer';
import axios from 'axios';

const steps = ['Upload Log File', 'Processing', 'View Results'];

function FirewallParser() {
  const [activeStep, setActiveStep] = useState(0);
  const [selectedFile, setSelectedFile] = useState(null);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFileSelect = async (file) => {
    setSelectedFile(file);
    setError(null);
    setActiveStep(1);
    setLoading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('/api/parse/firewall', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const taskId = response.data.task_id;
      pollTaskStatus(taskId);
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to upload file');
      setActiveStep(0);
      setLoading(false);
    }
  };

  const pollTaskStatus = async (taskId) => {
    const interval = setInterval(async () => {
      try {
        const response = await axios.get(`/api/task/${taskId}`);
        
        if (response.data.state === 'SUCCESS') {
          clearInterval(interval);
          setResults(response.data.result);
          setActiveStep(2);
          setLoading(false);
        } else if (response.data.state === 'FAILURE') {
          clearInterval(interval);
          setError(response.data.error || 'Processing failed');
          setActiveStep(0);
          setLoading(false);
        }
      } catch (error) {
        clearInterval(interval);
        setError('Failed to check task status');
        setActiveStep(0);
        setLoading(false);
      }
    }, 1000);
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 4 }}>
        Firewall Logs Aggregator
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="body1" color="text.secondary" gutterBottom>
          Aggregate firewall traffic data by destination IP address. This parser will:
        </Typography>
        <Box component="ul" sx={{ color: 'text.secondary', mt: 1 }}>
          <li>Extract destination IPs and sent bytes from logs</li>
          <li>Filter out private/local IP addresses</li>
          <li>Aggregate total bytes sent per destination</li>
          <li>Convert data sizes to megabytes</li>
          <li>Sort results by traffic volume</li>
        </Box>
      </Paper>

      <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {activeStep === 0 && (
        <FileUploader onFileSelect={handleFileSelect} />
      )}

      {activeStep === 1 && (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" gutterBottom>
            Processing {selectedFile?.name}...
          </Typography>
          <Box sx={{ width: '100%', mt: 3 }}>
            <LinearProgress />
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            Analyzing firewall traffic patterns...
          </Typography>
        </Paper>
      )}

      {activeStep === 2 && results && (
        <ResultsViewer results={results} title="Firewall Traffic Analysis Results" />
      )}
    </Box>
  );
}

export default FirewallParser;
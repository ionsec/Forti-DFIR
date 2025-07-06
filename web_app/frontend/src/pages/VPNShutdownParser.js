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
  TextField,
  Button,
} from '@mui/material';
import FileUploader from '../components/FileUploader';
import ResultsViewer from '../components/ResultsViewer';
import axios from 'axios';

const steps = ['Upload Log File', 'Enter Username', 'Processing', 'View Results'];

function VPNShutdownParser() {
  const [activeStep, setActiveStep] = useState(0);
  const [selectedFile, setSelectedFile] = useState(null);
  const [username, setUsername] = useState('');
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFileSelect = (file) => {
    setSelectedFile(file);
    setError(null);
    setActiveStep(1);
  };

  const handleUsernameSubmit = async () => {
    if (!username.trim()) {
      setError('Please enter a username');
      return;
    }

    setError(null);
    setActiveStep(2);
    setLoading(true);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('username', username);

    try {
      const response = await axios.post('/api/parse/vpn-shutdown', formData, {
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
          setActiveStep(3);
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
        VPN Shutdown Session Analyzer
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="body1" color="text.secondary" gutterBottom>
          Extract VPN session termination data for specific users. This parser will:
        </Typography>
        <Box component="ul" sx={{ color: 'text.secondary', mt: 1 }}>
          <li>Filter logs for SSL tunnel shutdown events</li>
          <li>Extract session data for the specified user</li>
          <li>Calculate sent bytes in megabytes</li>
          <li>Provide session termination timestamps</li>
          <li>Show total data usage across all sessions</li>
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
        <Paper sx={{ p: 4 }}>
          <Typography variant="h6" gutterBottom>
            Enter Username to Filter
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Enter the username to analyze their VPN shutdown sessions
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
            <TextField
              fullWidth
              label="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g., USER1"
              helperText="Case-insensitive search"
            />
            <Button
              variant="contained"
              onClick={handleUsernameSubmit}
              disabled={!username.trim()}
              sx={{ mt: 1 }}
            >
              Analyze
            </Button>
          </Box>
        </Paper>
      )}

      {activeStep === 2 && (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" gutterBottom>
            Processing {selectedFile?.name}...
          </Typography>
          <Box sx={{ width: '100%', mt: 3 }}>
            <LinearProgress />
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            Analyzing shutdown sessions for user: {username}
          </Typography>
        </Paper>
      )}

      {activeStep === 3 && results && (
        <ResultsViewer 
          results={results} 
          title={`VPN Shutdown Sessions - ${username}`}
        />
      )}
    </Box>
  );
}

export default VPNShutdownParser;
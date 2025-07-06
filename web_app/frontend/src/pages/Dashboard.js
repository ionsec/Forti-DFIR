import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Grid,
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  IconButton,
  Paper,
} from '@mui/material';
import {
  VpnKey as VpnIcon,
  Security as SecurityIcon,
  PowerSettingsNew as PowerIcon,
  ArrowForward as ArrowIcon,
  Description as FileIcon,
} from '@mui/icons-material';

const features = [
  {
    title: 'VPN Logs Parser',
    description: 'Extract successful VPN login details including date, time, user, tunnel type, and remote IP.',
    icon: <VpnIcon sx={{ fontSize: 48 }} />,
    color: '#4caf50',
    path: '/vpn-parser',
  },
  {
    title: 'Firewall Logs Aggregator',
    description: 'Aggregate firewall traffic by destination IP, filtering out private addresses and calculating data size.',
    icon: <SecurityIcon sx={{ fontSize: 48 }} />,
    color: '#2196f3',
    path: '/firewall-parser',
  },
  {
    title: 'VPN Shutdown Analyzer',
    description: 'Extract VPN session termination data with sent bytes statistics for specific users.',
    icon: <PowerIcon sx={{ fontSize: 48 }} />,
    color: '#ff9800',
    path: '/vpn-shutdown-parser',
  },
];

function Dashboard() {
  const navigate = useNavigate();

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 4 }}>
        Welcome to Forti-DFIR
      </Typography>
      
      <Paper sx={{ p: 3, mb: 4, bgcolor: 'background.paper' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <FileIcon sx={{ mr: 2, color: 'primary.main' }} />
          <Typography variant="h6">About This Tool</Typography>
        </Box>
        <Typography variant="body1" color="text.secondary">
          Forti-DFIR is a powerful web-based log parser designed for analyzing Fortinet VPN and firewall logs. 
          Upload your log files and get instant insights with CSV export capabilities for further analysis.
        </Typography>
      </Paper>

      <Grid container spacing={3}>
        {features.map((feature) => (
          <Grid item xs={12} md={4} key={feature.title}>
            <Card 
              sx={{ 
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                },
              }}
            >
              <CardContent sx={{ flexGrow: 1 }}>
                <Box 
                  sx={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    mb: 2,
                    color: feature.color,
                  }}
                >
                  {feature.icon}
                </Box>
                <Typography gutterBottom variant="h5" component="div">
                  {feature.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {feature.description}
                </Typography>
              </CardContent>
              <CardActions>
                <Button 
                  size="small" 
                  onClick={() => navigate(feature.path)}
                  endIcon={<ArrowIcon />}
                >
                  Open Parser
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Box sx={{ mt: 4, p: 2, bgcolor: 'background.paper', borderRadius: 1 }}>
        <Typography variant="body2" color="text.secondary" align="center">
          Developed by IONSec Research Team
        </Typography>
      </Box>
    </Box>
  );
}

export default Dashboard;
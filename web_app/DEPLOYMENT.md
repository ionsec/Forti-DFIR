# Deployment Guide - Forti-DFIR Web Application

This guide explains how to deploy the Forti-DFIR web application to Netlify and Vercel.

## Prerequisites

1. GitHub repository with the code
2. Netlify account
3. Vercel account

## Automatic Deployment with GitHub Actions

The project includes GitHub Actions workflows for automatic deployment on every push to the main branch.

### Setup Steps

1. **Fork or clone this repository** to your GitHub account

2. **Set up Netlify:**
   - Create a new site on Netlify
   - Get your Netlify Auth Token from Account Settings > Applications
   - Get your Site ID from Site Settings > General > Site details
   
3. **Set up Vercel:**
   - Install Vercel CLI: `npm i -g vercel`
   - Link your project: `vercel link`
   - Get your tokens: `vercel whoami --token`

4. **Add GitHub Secrets:**
   Go to your repository Settings > Secrets and variables > Actions, and add:
   - `NETLIFY_AUTH_TOKEN`: Your Netlify personal access token
   - `NETLIFY_SITE_ID`: Your Netlify site ID
   - `VERCEL_TOKEN`: Your Vercel token
   - `VERCEL_ORG_ID`: Your Vercel organization ID
   - `VERCEL_PROJECT_ID`: Your Vercel project ID for frontend
   - `VERCEL_BACKEND_PROJECT_ID`: Your Vercel project ID for backend

## Manual Deployment

### Deploy Frontend to Netlify

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Build the frontend
cd web_app/frontend
npm install
npm run build

# Deploy to Netlify
netlify deploy --dir=build --prod
```

### Deploy to Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy frontend
cd web_app
vercel --prod

# Deploy backend (in a separate project)
cd web_app/backend
vercel --prod
```

## Environment Configuration

### Frontend Environment Variables

Create a `.env` file in `web_app/frontend/` with:

```env
REACT_APP_API_URL=https://your-backend-api.vercel.app
```

### Backend Considerations

The backend requires a persistent file system for uploads and results. Consider using:

1. **Vercel with External Storage:**
   - Use AWS S3, Cloudinary, or similar for file storage
   - Modify the backend to use cloud storage instead of local filesystem

2. **Alternative Backend Hosting:**
   - **Heroku**: Supports Python apps with temporary file storage
   - **Railway**: Easy Python deployment with persistent volumes
   - **Render**: Free tier with disk storage
   - **DigitalOcean App Platform**: Supports Python with persistent storage

### Recommended Architecture for Production

```
Frontend (Netlify/Vercel)
    ↓
Backend API (Railway/Render)
    ↓
File Storage (S3/Cloudinary)
```

## Post-Deployment Steps

1. **Update CORS settings** in `backend/simple_app.py` to include your production frontend URL:
   ```python
   CORS(app, origins=['https://your-app.netlify.app', 'https://your-app.vercel.app'])
   ```

2. **Update API URL** in the frontend environment variables

3. **Test the deployment:**
   - Login functionality
   - File upload
   - All three parser types
   - CSV download

## Troubleshooting

### CORS Errors
- Ensure the backend CORS configuration includes your frontend domain
- Check that the API URL in frontend environment variables is correct

### File Upload Issues
- Verify file size limits on your hosting platform
- Check backend storage configuration

### Authentication Issues
- Ensure environment variables are properly set
- Verify the backend is accessible from the frontend

## Security Considerations

1. **Use HTTPS** for both frontend and backend
2. **Set secure headers** (already configured in deployment files)
3. **Use environment variables** for sensitive data
4. **Implement proper authentication** for production use
5. **Set up rate limiting** on the backend API

## Monitoring

Consider setting up:
- Error tracking (Sentry)
- Analytics (Google Analytics, Plausible)
- Uptime monitoring (UptimeRobot, Pingdom)
- Log aggregation (LogRocket, Datadog)
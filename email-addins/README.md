# Contentry.ai Email Add-ins

Real-time content analysis and compliance checking for Gmail and Outlook.

## Architecture

This is a monorepo containing:
- `shared/` - Shared React components, hooks, and API utilities
- `gmail/` - Gmail Add-on (iframe-based with Apps Script wrapper)
- `outlook/` - Outlook Add-in (Office.js based)

## Features

- **Real-time Analysis**: Analyzes email subject + body as you type
- **3-Pillar Scores**: Compliance, Cultural Sensitivity, and Accuracy
- **Strategic Profile Selection**: Choose your "Brand Brain" for analysis
- **Actionable Recommendations**: Get specific suggestions to improve your emails
- **Dashboard Integration**: All analyses are logged to your Contentry.ai history

## Development Setup

### Prerequisites
- Node.js 18+
- Yarn
- Google Workspace account (for Gmail development)
- Microsoft 365 account (for Outlook development)

### Installation

```bash
cd /app/email-addins
yarn install
```

### Gmail Add-on Development

```bash
# Start development server
yarn dev:gmail

# Build for production
yarn build:gmail
```

#### Gmail Deployment Steps:

1. Create a Google Apps Script project at https://script.google.com
2. Copy `gmail/Code.gs` and `gmail/appsscript.json` to the project
3. Update `CONTENTRY_APP_URL` in `Code.gs` with your deployed URL
4. Deploy the React app (`gmail/dist/`) to a hosting service
5. Test using "Test deployments" in Apps Script
6. Publish to Google Workspace Marketplace

### Outlook Add-in Development

```bash
# Start development server (HTTPS required)
yarn dev:outlook

# Build for production
yarn build:outlook
```

#### Outlook Deployment Steps:

1. Update `manifest.xml` URLs with your deployed URL
2. Deploy the React app (`outlook/dist/`) to a hosting service with HTTPS
3. Sideload the manifest for testing:
   - Outlook Web: Settings > Manage Integrations > My add-ins > Add custom add-in
   - Outlook Desktop: File > Manage Add-ins > Add custom add-in
4. Submit to Microsoft AppSource for public availability

## API Integration

Both add-ins use the same backend APIs:

- `POST /api/auth/extension/login` - Authentication
- `GET /api/profiles/strategic` - Get strategic profiles
- `POST /api/content/analyze` - Analyze content

## Configuration

Update the API URL in:
- `gmail/index.html` - Set `window.CONTENTRY_API_URL`
- `outlook/index.html` - Set `window.CONTENTRY_API_URL`
- `shared/lib/config.ts` - Default fallback URL

## Design System

- **Primary Color**: #6941C6
- **Secondary Color**: #7F56D9
- **Light Tint**: #F9F5FF
- **Text Color**: #101828
- **Font**: Inter, Segoe UI (fallback)

## Testing

### Gmail Testing
1. Install the add-on from test deployment
2. Compose a new email
3. Click the Contentry.ai icon in the sidebar
4. Sign in with your credentials
5. Start typing - analysis updates in real-time

### Outlook Testing
1. Sideload the manifest
2. Compose a new email
3. Click "Analyze Email" in the ribbon
4. Sign in with your credentials
5. Start typing - analysis updates in real-time

## Deployment Checklist

### Gmail
- [ ] Deploy React app to hosting (e.g., Vercel, Netlify)
- [ ] Update `CONTENTRY_APP_URL` in `Code.gs`
- [ ] Configure OAuth consent screen
- [ ] Submit to Google Workspace Marketplace

### Outlook
- [ ] Deploy React app to HTTPS hosting
- [ ] Update all URLs in `manifest.xml`
- [ ] Generate new GUID for production
- [ ] Test on Outlook Web and Desktop
- [ ] Submit to Microsoft AppSource

## Support

For issues or questions, contact support@contentry.ai

# Contentry.ai Browser Extension

Real-time content analysis and compliance checking for any webpage.

## Features

- **Real-time Analysis**: Get instant feedback on your content as you type
- **3-Pillar Scoring**: Compliance, Cultural Sensitivity, and Accuracy scores
- **Strategic Profile Selection**: Choose which "Brand Brain" to use for analysis
- **Smart Recommendations**: Get actionable suggestions to improve your content
- **Works Everywhere**: Analyze content on LinkedIn, Twitter, email, CMS, and more

## Installation

### Development Build

1. Navigate to the extension directory:
   ```bash
   cd /app/extension
   ```

2. Install dependencies:
   ```bash
   yarn install
   ```

3. Build the extension:
   ```bash
   yarn build
   ```

4. Load in Chrome:
   - Open `chrome://extensions`
   - Enable "Developer mode"
   - Click "Load unpacked"
   - Select the `build/chrome-mv3-prod` folder

### Production Build

```bash
yarn build:chrome  # For Chrome
yarn build:edge    # For Edge
yarn package       # Create distributable zip
```

## Usage

1. **Sign In**: Click the extension icon and sign in with your Contentry.ai account
2. **Open Side Panel**: Click the extension icon or use the "Open Analysis Panel" button
3. **Select Profile**: Choose your Strategic Profile (Brand Brain) from the dropdown
4. **Start Writing**: Type in any text field on any website
5. **Get Analysis**: See real-time scores and recommendations in the side panel

## Architecture

```
src/
├── popup.tsx              # Toolbar popup (quick actions)
├── sidepanel.tsx          # Main analysis UI (side panel)
├── contents/
│   └── content-detector.ts  # Content script for text detection
├── background/
│   └── index.ts           # Service worker
├── components/
│   ├── Header.tsx
│   ├── LoginPrompt.tsx
│   ├── ProfileSelector.tsx
│   ├── ScoreCard.tsx
│   ├── RecommendationList.tsx
│   └── LoadingState.tsx
├── lib/
│   ├── api.ts             # API client
│   ├── config.ts          # Configuration
│   └── messages.ts        # Message types
└── styles/
    └── globals.css        # Tailwind + custom styles
```

## API Endpoints Used

- `POST /api/auth/extension/login` - Authentication
- `GET /api/auth/extension/verify` - Session verification
- `GET /api/profiles/strategic` - Get user's strategic profiles
- `POST /api/content/analyze` - Analyze content

## Configuration

Environment variables (in `.env.development` or `.env.production`):

```env
PLASMO_PUBLIC_API_URL=http://localhost:8001  # Development
PLASMO_PUBLIC_API_URL=https://contentry.ai   # Production
```

## Design System

- **Primary Color**: #6941C6
- **Secondary Color**: #7F56D9
- **Light Tint**: #F9F5FF
- **Text Color**: #101828
- **Font**: Inter
- **Icons**: Lucide React (outline style)

## Browser Support

- Chrome (Manifest V3)
- Edge (Manifest V3)

## Phase 2 Features (Planned)

- In-field icon detection
- Quick actions context menu
- Keyboard shortcuts
- Dark mode support
- Multi-language support

## License

Proprietary - Contentry.ai

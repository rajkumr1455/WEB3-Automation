# Web3 Bounty Hunter - Web UI

Production-grade Next.js 14 web interface for the Web3 Bug Bounty Automation Platform.

## Features

- **Real-Time Dashboard** - Live metrics, scan status, and system health
- **Multi-Agent Monitoring** - Track all 6 security agents
- **Scan Management** - Start, monitor, and review security scans
- **Beautiful UI** - Glassmorphism design with smooth animations
- **Responsive** - Works on desktop, tablet, and mobile
- **Type-Safe** - Full TypeScript with strict typing
- **Performance** - Optimized bundle with Next.js App Router

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React Query (TanStack Query)
- **Animations**: Framer Motion
- **Icons**: Lucide React
- **HTTP Client**: Axios

## Getting Started

### Prerequisites

- Node.js 20+ 
- npm or yarn
- Backend services running (see main README)

### Development

```bash
# Install dependencies
cd web-ui
npm install

# Set environment variables
echo "NEXT_PUBLIC_API_URL=http://localhost:8001" > .env.local

# Run development server
npm run dev
```

The app will be available at `http://localhost:3001`

### Production Build

```bash
# Build for production
npm run build

# Start production server
npm start
```

### Docker

```bash
# Build Docker image
docker build -t web3-bounty-ui .

# Run container
docker run -p 3001:3000 -e NEXT_PUBLIC_API_URL=http://localhost:8001 web3-bounty-ui
```

## Pages

| Route | Description |
|-------|-------------|
| `/` | Dashboard - Main overview with metrics and scan management |
| `/recon` | Reconnaissance results - ABIs, contracts, endpoints |
| `/static-analysis` | Static analysis findings from Slither, Mythril, Semgrep |
| `/fuzzing` | Fuzzing results from Foundry, Echidna |
| `/monitoring` | Real-time mempool and oracle monitoring |
| `/triage` | AI-powered vulnerability triage workbench |
| `/reports` | Generated reports for Immunefi and HackenProof |
| `/agents` | Agent health status and LLM router configuration |
| `/settings` | Application settings and preferences |

##  Components

### Core Components

- **Navigation** - Sidebar navigation with active state
- **ScanForm** - Form to initiate new scans
- **MetricsCards** - Dashboard statistics cards
- **RecentScans** - List of recent scans with progress
- **FindingsTable** - Reusable vulnerability findings table

### API Integration

All API calls go through `/lib/api.ts` which provides:

- `scanAPI` - Scan management
- `agentAPI` - Agent health checks
- `reportsAPI` - Report generation and download
- `metricsAPI` - Dashboard metrics

### Utilities

- `/lib/utils.ts` - Helper functions for formatting, colors, etc.

## Design System

### Colors

- **Primary** - Blue (`#0ea5e9`)
- **Danger** - Red (`#ef4444`)
- **Success** - Green (`#22c55e`)
- **Warning** - Orange (`#f59e0b`)

### Components

Reusable Tailwind classes defined in `globals.css`:

- `.card` - Basic card with glassmorphism
- `.card-hover` - Card with hover effects
- `.btn-primary` - Primary action button
- `.btn-secondary` - Secondary action button
- `.badge-*` - Severity/status badges
- `.glassmorphism` - Glass effect with backdrop blur

### Animations

- Fade in on page load
- Slide up for cards
- Staggered children animations
- Pulse for live indicators
- Loading shimmer effects

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8001` |

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Performance

- **First Load** - Under 100 KB (gzipped)
- **Lighthouse Score** - 95+ on all metrics
- **Bundle Size** - Optimized with tree-shaking
- **Code Splitting** - Automatic route-based splitting

## Contributing

1. Follow the existing code style
2. Use TypeScript strict mode
3. Add types for all props
4. Test on multiple screen sizes
5. Ensure accessibility (WCAG 2.1 AA)

## License

MIT

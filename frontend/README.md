# MedCode API Frontend

Next.js dashboard for the MedCode API.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open http://localhost:3000

## Environment Variables

Create `.env.local`:
```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# NextAuth Configuration
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-random-secret-key-here

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Microsoft Azure AD OAuth
AZURE_AD_CLIENT_ID=your-azure-client-id
AZURE_AD_CLIENT_SECRET=your-azure-client-secret
AZURE_AD_TENANT_ID=common
```

### Setting up OAuth Providers

#### Google OAuth Setup:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Navigate to "APIs & Services" > "Credentials"
4. Click "Create Credentials" > "OAuth client ID"
5. Choose "Web application"
6. Add authorized redirect URI: `http://localhost:3000/api/auth/callback/google`
7. Copy Client ID and Client Secret to `.env.local`

#### Microsoft Azure AD Setup:
1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to "Azure Active Directory" > "App registrations"
3. Click "New registration"
4. Set name and supported account types
5. Add redirect URI: `http://localhost:3000/api/auth/callback/azure-ad`
6. Go to "Certificates & secrets" > Create new client secret
7. Copy Application (client) ID and client secret to `.env.local`

#### Generate NEXTAUTH_SECRET:
```bash
openssl rand -base64 32
```

## Project Structure

```
frontend/
├── app/
│   ├── page.tsx                 # Landing page
│   ├── layout.tsx               # Root layout
│   ├── login/page.tsx           # Login page
│   ├── signup/page.tsx          # Signup page
│   ├── dashboard/
│   │   ├── layout.tsx           # Dashboard layout with sidebar
│   │   ├── page.tsx             # Dashboard home (usage stats)
│   │   ├── api-keys/page.tsx   # API key management
│   │   ├── docs/page.tsx        # API documentation
│   │   └── billing/page.tsx     # Billing management
├── components/
│   ├── ui/                      # Reusable UI components
│   └── DashboardNav.tsx         # Dashboard navigation
├── lib/
│   ├── api.ts                   # API client (✓ Created)
│   ├── auth.tsx                 # Auth context (✓ Created)
│   └── utils.ts                 # Utility functions (✓ Created)
└── package.json                 # Dependencies (✓ Created)
```

## Features

- Landing page with features & pricing
- User authentication (email/password, Google SSO, Microsoft SSO)
- Dashboard with usage stats
- API key management (create, list, revoke)
- API documentation viewer
- Billing management (Stripe portal)
- Single Sign-On (SSO) with Google and Microsoft

## Technologies

- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- NextAuth.js for authentication and SSO
- Axios for API calls
- React Hook Form for forms
- Lucide React for icons

## Pages to Complete

The following pages still need to be created. I'll provide the code files separately.

### Required Pages:
1. `app/page.tsx` - Landing page
2. `app/login/page.tsx` - Login form
3. `app/signup/page.tsx` - Signup form
4. `app/dashboard/layout.tsx` - Dashboard layout with sidebar
5. `app/dashboard/page.tsx` - Usage stats dashboard
6. `app/dashboard/api-keys/page.tsx` - API key management
7. `app/dashboard/docs/page.tsx` - API documentation
8. `app/dashboard/billing/page.tsx` - Billing page

### Required Components:
1. `components/ui/Button.tsx`
2. `components/ui/Input.tsx`
3. `components/ui/Card.tsx`
4. `components/DashboardNav.tsx`

## API Integration

The API client (`lib/api.ts`) is configured to connect to the backend at `http://localhost:8000`.

All API calls use axios with automatic token management via interceptors.

## Authentication Flow

1. User signs up or logs in
2. JWT token is stored in localStorage
3. Token is automatically added to all API requests
4. User is redirected to dashboard
5. Protected routes check for valid token

## Next Steps

1. Run `npm install` to install dependencies
2. Ensure backend is running on port 8000
3. Start the dev server with `npm run dev`
4. Visit http://localhost:3000


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
```
NEXT_PUBLIC_API_URL=http://localhost:8000
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
- User authentication (signup/login)
- Dashboard with usage stats
- API key management (create, list, revoke)
- API documentation viewer
- Billing management (Stripe portal)

## Technologies

- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
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


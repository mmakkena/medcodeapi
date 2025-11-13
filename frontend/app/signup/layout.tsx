import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Get Free API Key - Medical Coding API - Nuvii.ai',
  description: 'Sign up for free ICD-10 & CPT coding API. Instant API key, 100 free requests/month. No credit card required.',
  keywords: ['AI medical coding API signup', 'free ICD-10 API', 'CPT API registration', 'healthcare developer tools', 'free medical coding API'],
  openGraph: {
    title: 'Get Free API Key - Medical Coding API',
    description: 'Sign up for free ICD-10 & CPT coding API. Instant API key, 100 free requests/month. No credit card required.',
    url: 'https://nuvii.ai/signup',
    siteName: 'Nuvii.ai',
    type: 'website',
  },
  twitter: {
    card: 'summary',
    title: 'Get Free API Key - Medical Coding API',
    description: 'Sign up for free ICD-10 & CPT coding API. Instant API key, 100 free requests/month.',
  },
  alternates: {
    canonical: 'https://nuvii.ai/signup',
  },
};

export default function SignupLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}

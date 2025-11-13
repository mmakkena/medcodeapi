import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Login - Nuvii.ai Medical Coding API',
  description: 'Log in to your Nuvii.ai account to access your medical coding API dashboard, manage API keys, and view usage statistics.',
  alternates: {
    canonical: 'https://nuvii.ai/login',
  },
};

export default function LoginLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}

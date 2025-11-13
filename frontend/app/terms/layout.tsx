import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Terms of Service - Nuvii.ai Medical Coding API',
  description: 'Terms of Service for Nuvii.ai medical coding API. Usage terms, service level agreements, and legal information.',
  alternates: {
    canonical: 'https://nuvii.ai/terms',
  },
};

export default function TermsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}

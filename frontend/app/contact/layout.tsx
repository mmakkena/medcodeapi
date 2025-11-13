import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Contact Us - Medical Coding API Support - Nuvii.ai',
  description: 'Get help with Nuvii medical coding API. Technical support, enterprise inquiries, partnership opportunities. Response in 24 hours.',
  keywords: ['medical API contact', 'healthcare AI partnership', 'coding API inquiry', 'medical coding support', 'API technical support'],
  openGraph: {
    title: 'Contact Us - Medical Coding API Support',
    description: 'Get help with Nuvii medical coding API. Technical support, enterprise inquiries, partnership opportunities.',
    url: 'https://nuvii.ai/contact',
    siteName: 'Nuvii.ai',
    type: 'website',
  },
  twitter: {
    card: 'summary',
    title: 'Contact Us - Medical Coding API Support',
    description: 'Get help with Nuvii medical coding API. Technical support, enterprise inquiries, partnership opportunities.',
  },
  alternates: {
    canonical: 'https://nuvii.ai/contact',
  },
};

export default function ContactLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}

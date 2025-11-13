import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'API Documentation - Medical Coding Reference - Nuvii.ai',
  description: 'Complete developer docs for ICD-10 & CPT coding API. REST endpoints, code examples, SDKs. Get started in 5 minutes.',
  keywords: ['developer API medical coding', 'REST medical coding API', 'ICD-10 CPT developer API', 'AI medical coding SDK', 'API documentation', 'medical coding API reference'],
  openGraph: {
    title: 'API Documentation - Medical Coding Reference',
    description: 'Complete developer docs for ICD-10 & CPT coding API. REST endpoints, code examples, SDKs.',
    url: 'https://nuvii.ai/docs',
    siteName: 'Nuvii.ai',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'API Documentation - Medical Coding Reference',
    description: 'Complete developer docs for ICD-10 & CPT coding API. REST endpoints, code examples, SDKs.',
  },
  alternates: {
    canonical: 'https://nuvii.ai/docs',
  },
};

export default function DocsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}

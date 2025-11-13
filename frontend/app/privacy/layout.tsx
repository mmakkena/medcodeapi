import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Privacy Policy - Nuvii.ai Medical Coding API',
  description: 'Privacy policy for Nuvii.ai medical coding API. Learn how we protect your data, HIPAA compliance, and information security practices.',
  alternates: {
    canonical: 'https://nuvii.ai/privacy',
  },
};

export default function PrivacyLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}

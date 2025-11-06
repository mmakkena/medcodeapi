import Link from 'next/link';
import Image from 'next/image';

export default function PrivacyPolicy() {
  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b sticky top-0 bg-white z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <Link href="/">
            <Image
              src="/nuvii_logo.png"
              alt="Nuvii AI"
              width={720}
              height={192}
              className="h-48 w-auto"
            />
          </Link>
          <Link
            href="/"
            className="text-gray-700 hover:text-gray-900"
          >
            Back to Home
          </Link>
        </div>
      </header>

      {/* Privacy Policy Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">Privacy Policy</h1>
        <p className="text-gray-600 mb-8">Last updated: January 2025</p>

        <div className="prose prose-lg max-w-none">
          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">1. Introduction</h2>
            <p className="text-gray-700 mb-4">
              Welcome to Nuvii AI (&ldquo;we,&rdquo; &ldquo;our,&rdquo; or &ldquo;us&rdquo;). We are committed to protecting your privacy and ensuring the security of your personal information. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our medical coding API services.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">2. Information We Collect</h2>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">2.1 Account Information</h3>
            <p className="text-gray-700 mb-4">
              When you create an account, we collect:
            </p>
            <ul className="list-disc pl-6 text-gray-700 mb-4 space-y-2">
              <li>Email address</li>
              <li>Password (encrypted)</li>
              <li>Account creation date</li>
              <li>Subscription plan information</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">2.2 API Usage Data</h3>
            <p className="text-gray-700 mb-4">
              When you use our API services, we collect:
            </p>
            <ul className="list-disc pl-6 text-gray-700 mb-4 space-y-2">
              <li>API request logs (timestamps, endpoints, response codes)</li>
              <li>Usage statistics and analytics</li>
              <li>Authentication tokens</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">2.3 Technical Information</h3>
            <p className="text-gray-700 mb-4">
              We automatically collect certain technical information, including:
            </p>
            <ul className="list-disc pl-6 text-gray-700 mb-4 space-y-2">
              <li>IP addresses</li>
              <li>Browser type and version</li>
              <li>Device information</li>
              <li>Operating system</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">3. Protected Health Information (PHI)</h2>
            <p className="text-gray-700 mb-4">
              <strong>We do not store or retain any Protected Health Information (PHI) or clinical data.</strong> Our API processes medical coding requests in real-time and does not persist any patient data or clinical notes. All API responses are generated on-demand and not stored on our servers.
            </p>
            <p className="text-gray-700 mb-4">
              While we are HIPAA-ready, you are responsible for ensuring that any data you send through our API is properly de-identified or that you have the necessary authorizations and agreements in place.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">4. How We Use Your Information</h2>
            <p className="text-gray-700 mb-4">
              We use the information we collect to:
            </p>
            <ul className="list-disc pl-6 text-gray-700 mb-4 space-y-2">
              <li>Provide, maintain, and improve our API services</li>
              <li>Process your API requests and deliver results</li>
              <li>Monitor usage and enforce rate limits</li>
              <li>Generate usage analytics and billing</li>
              <li>Detect and prevent fraud or abuse</li>
              <li>Communicate with you about service updates, security alerts, and support</li>
              <li>Comply with legal obligations</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">5. Information Sharing and Disclosure</h2>
            <p className="text-gray-700 mb-4">
              We do not sell, rent, or trade your personal information. We may share your information only in the following circumstances:
            </p>
            <ul className="list-disc pl-6 text-gray-700 mb-4 space-y-2">
              <li><strong>Service Providers:</strong> We work with trusted third-party service providers who assist us in operating our platform (e.g., cloud hosting, payment processing). These providers are bound by confidentiality agreements.</li>
              <li><strong>Legal Requirements:</strong> We may disclose information if required by law, court order, or governmental authority.</li>
              <li><strong>Business Transfers:</strong> In the event of a merger, acquisition, or sale of assets, your information may be transferred to the acquiring entity.</li>
              <li><strong>With Your Consent:</strong> We may share information with your explicit consent.</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">6. Data Security</h2>
            <p className="text-gray-700 mb-4">
              We implement industry-standard security measures to protect your information:
            </p>
            <ul className="list-disc pl-6 text-gray-700 mb-4 space-y-2">
              <li>256-bit SSL/TLS encryption for all data in transit</li>
              <li>Encrypted storage for sensitive data at rest</li>
              <li>Regular security audits and vulnerability assessments</li>
              <li>Access controls and authentication mechanisms</li>
              <li>Monitoring and logging of system activities</li>
            </ul>
            <p className="text-gray-700 mb-4">
              However, no method of transmission over the internet or electronic storage is 100% secure. While we strive to use commercially acceptable means to protect your information, we cannot guarantee absolute security.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">7. Data Retention</h2>
            <p className="text-gray-700 mb-4">
              We retain your account information and usage data for as long as your account is active or as needed to provide services. You may request deletion of your account at any time by contacting us at support@nuvii.ai.
            </p>
            <p className="text-gray-700 mb-4">
              API request logs and usage statistics are retained for billing and analytical purposes for up to 90 days, after which they are automatically purged from our systems.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">8. Your Rights</h2>
            <p className="text-gray-700 mb-4">
              Depending on your location, you may have the following rights regarding your personal information:
            </p>
            <ul className="list-disc pl-6 text-gray-700 mb-4 space-y-2">
              <li><strong>Access:</strong> Request a copy of the personal information we hold about you</li>
              <li><strong>Correction:</strong> Request correction of inaccurate or incomplete information</li>
              <li><strong>Deletion:</strong> Request deletion of your personal information</li>
              <li><strong>Portability:</strong> Request transfer of your data to another service</li>
              <li><strong>Objection:</strong> Object to processing of your personal information</li>
              <li><strong>Restriction:</strong> Request restriction of processing</li>
            </ul>
            <p className="text-gray-700 mb-4">
              To exercise any of these rights, please contact us at support@nuvii.ai.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">9. Cookies and Tracking</h2>
            <p className="text-gray-700 mb-4">
              Our website uses cookies and similar tracking technologies to:
            </p>
            <ul className="list-disc pl-6 text-gray-700 mb-4 space-y-2">
              <li>Maintain your login session</li>
              <li>Remember your preferences</li>
              <li>Analyze site traffic and usage patterns</li>
              <li>Improve user experience</li>
            </ul>
            <p className="text-gray-700 mb-4">
              You can control cookies through your browser settings. However, disabling cookies may limit your ability to use certain features of our platform.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">10. Third-Party Services</h2>
            <p className="text-gray-700 mb-4">
              Our service uses third-party authentication providers (e.g., Google OAuth). When you use these services, you are also subject to their respective privacy policies. We encourage you to review the privacy policies of any third-party services you use.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">11. International Data Transfers</h2>
            <p className="text-gray-700 mb-4">
              Your information may be transferred to and processed in countries other than your country of residence. These countries may have different data protection laws. By using our services, you consent to such transfers.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">12. Children&apos;s Privacy</h2>
            <p className="text-gray-700 mb-4">
              Our services are not directed to individuals under the age of 18. We do not knowingly collect personal information from children. If you become aware that a child has provided us with personal information, please contact us.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">13. Changes to This Privacy Policy</h2>
            <p className="text-gray-700 mb-4">
              We may update this Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy Policy on this page and updating the &ldquo;Last updated&rdquo; date. You are advised to review this Privacy Policy periodically for any changes.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">14. Contact Us</h2>
            <p className="text-gray-700 mb-4">
              If you have any questions or concerns about this Privacy Policy or our privacy practices, please contact us at:
            </p>
            <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
              <p className="text-gray-700 mb-2"><strong>Email:</strong> support@nuvii.ai</p>
              <p className="text-gray-700"><strong>Website:</strong> <Link href="/" className="text-nuvii-blue hover:underline">https://nuvii.ai</Link></p>
            </div>
          </section>
        </div>
      </div>

      {/* Footer */}
      <footer className="py-8 bg-gray-50 px-4 sm:px-6 lg:px-8 border-t mt-12">
        <div className="max-w-7xl mx-auto text-center">
          <p className="text-gray-600">&copy; 2025 Nuvii API. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

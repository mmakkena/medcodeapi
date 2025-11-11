import Link from 'next/link';
import Image from 'next/image';

export default function TermsOfService() {
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

      {/* Terms of Service Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">Terms of Service</h1>
        <p className="text-gray-600 mb-8">Last updated: January 2025</p>

        <div className="prose prose-lg max-w-none">
          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">1. Acceptance of Terms</h2>
            <p className="text-gray-700 mb-4">
              Welcome to Nuvii AI (&ldquo;we,&rdquo; &ldquo;our,&rdquo; or &ldquo;us&rdquo;). By accessing or using our medical coding API services, website, and related services (collectively, the &ldquo;Service&rdquo;), you agree to be bound by these Terms of Service (&ldquo;Terms&rdquo;). If you do not agree to these Terms, do not use our Service.
            </p>
            <p className="text-gray-700 mb-4">
              These Terms constitute a legally binding agreement between you (either an individual or a legal entity) and Nuvii AI. We reserve the right to modify these Terms at any time, and such modifications will be effective immediately upon posting. Your continued use of the Service after any changes constitutes your acceptance of the revised Terms.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">2. Account Registration and Security</h2>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">2.1 Account Requirements</h3>
            <p className="text-gray-700 mb-4">
              To use our Service, you must:
            </p>
            <ul className="list-disc pl-6 text-gray-700 mb-4 space-y-2">
              <li>Be at least 18 years of age or the age of majority in your jurisdiction</li>
              <li>Provide accurate, current, and complete information during registration</li>
              <li>Maintain and promptly update your account information</li>
              <li>Not impersonate any person or entity or falsely state your affiliation</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">2.2 Account Security</h3>
            <p className="text-gray-700 mb-4">
              You are responsible for:
            </p>
            <ul className="list-disc pl-6 text-gray-700 mb-4 space-y-2">
              <li>Maintaining the confidentiality of your account credentials and API keys</li>
              <li>All activities that occur under your account</li>
              <li>Immediately notifying us of any unauthorized use of your account</li>
              <li>Ensuring that your account is not shared with unauthorized parties</li>
            </ul>
            <p className="text-gray-700 mb-4">
              We are not liable for any loss or damage arising from your failure to maintain account security.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">3. API Usage and Restrictions</h2>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">3.1 Permitted Use</h3>
            <p className="text-gray-700 mb-4">
              Our API is designed for legitimate medical coding and healthcare technology applications. You may use the Service to:
            </p>
            <ul className="list-disc pl-6 text-gray-700 mb-4 space-y-2">
              <li>Search for ICD-10 diagnosis codes and CPT/HCPCS procedure codes</li>
              <li>Generate code suggestions from clinical text</li>
              <li>Integrate medical coding functionality into your applications</li>
              <li>Develop healthcare and medical billing solutions</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">3.2 Usage Restrictions</h3>
            <p className="text-gray-700 mb-4">
              You agree NOT to:
            </p>
            <ul className="list-disc pl-6 text-gray-700 mb-4 space-y-2">
              <li>Exceed the rate limits or usage quotas of your subscription plan</li>
              <li>Attempt to circumvent or bypass any rate limiting, authentication, or access control mechanisms</li>
              <li>Resell, redistribute, or sublicense access to the API without written permission</li>
              <li>Use the Service to transmit malware, viruses, or any harmful code</li>
              <li>Reverse engineer, decompile, or attempt to extract source code from the Service</li>
              <li>Use the Service for any illegal, fraudulent, or unauthorized purpose</li>
              <li>Attempt to gain unauthorized access to our systems or networks</li>
              <li>Submit excessive or abusive API requests designed to disrupt service availability</li>
              <li>Use automated tools to scrape or download our code databases in bulk</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">3.3 Rate Limits</h3>
            <p className="text-gray-700 mb-4">
              Each subscription plan includes specific rate limits and usage quotas. Exceeding these limits may result in:
            </p>
            <ul className="list-disc pl-6 text-gray-700 mb-4 space-y-2">
              <li>Temporary throttling of API requests</li>
              <li>Additional usage charges as specified in your plan</li>
              <li>Suspension of service for repeated violations</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">4. Protected Health Information (PHI) and HIPAA Compliance</h2>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">4.1 No PHI Storage</h3>
            <p className="text-gray-700 mb-4">
              <strong className="text-red-600">We do not store or retain any Protected Health Information (PHI) or patient data.</strong> All API requests are processed in real-time, and clinical text submitted through our Service is not persisted on our servers.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">4.2 Your PHI Responsibilities</h3>
            <p className="text-gray-700 mb-4">
              You acknowledge and agree that:
            </p>
            <ul className="list-disc pl-6 text-gray-700 mb-4 space-y-2">
              <li><strong>De-identification Required:</strong> You must de-identify all clinical text before submitting it to our API by removing all patient identifiers including names, dates, addresses, phone numbers, social security numbers, medical record numbers, and any other information that could identify an individual</li>
              <li><strong>Compliance is Your Responsibility:</strong> You are solely responsible for ensuring HIPAA compliance and compliance with all applicable healthcare privacy laws</li>
              <li><strong>No Playground PHI:</strong> You must never enter real patient data or PHI into our MedCode Playground, which is intended only for testing with synthetic or de-identified data</li>
              <li><strong>BAA Requirement:</strong> If you need to transmit PHI through our Service, you must contact us at support@nuvii.ai to execute a Business Associate Agreement (BAA) before doing so</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">4.3 Prohibited Patient Identifiers</h3>
            <p className="text-gray-700 mb-4">
              The following must be removed before submitting clinical text:
            </p>
            <ul className="list-disc pl-6 text-gray-700 mb-4 space-y-2">
              <li>Names (patient, family members, healthcare providers)</li>
              <li>Dates (birth, admission, discharge, death, or dates more specific than year)</li>
              <li>Phone numbers, fax numbers</li>
              <li>Email addresses</li>
              <li>Social Security numbers</li>
              <li>Medical record numbers</li>
              <li>Health plan beneficiary numbers</li>
              <li>Account numbers</li>
              <li>Certificate/license numbers</li>
              <li>Vehicle identifiers and serial numbers</li>
              <li>Device identifiers and serial numbers</li>
              <li>URLs and IP addresses</li>
              <li>Biometric identifiers (fingerprints, voiceprints)</li>
              <li>Full face photos and comparable images</li>
              <li>Any other unique identifying numbers, characteristics, or codes</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">5. Payment Terms</h2>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">5.1 Subscription Plans</h3>
            <p className="text-gray-700 mb-4">
              We offer multiple subscription tiers with different usage limits and pricing. All prices are in U.S. dollars and exclude applicable taxes unless otherwise stated.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">5.2 Billing</h3>
            <p className="text-gray-700 mb-4">
              By subscribing to a paid plan, you agree that:
            </p>
            <ul className="list-disc pl-6 text-gray-700 mb-4 space-y-2">
              <li>Subscription fees are charged in advance on a monthly or annual basis</li>
              <li>Payment is due immediately upon subscription and automatically renews unless cancelled</li>
              <li>Usage charges beyond your plan limits may apply and are billed monthly in arrears</li>
              <li>All fees are non-refundable except as required by law</li>
              <li>We use Stripe for payment processing and do not store your payment card information</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">5.3 Price Changes</h3>
            <p className="text-gray-700 mb-4">
              We reserve the right to modify our pricing at any time. Price changes will not affect existing subscriptions until renewal. We will provide at least 30 days&apos; notice of any price increases.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">5.4 Failed Payments</h3>
            <p className="text-gray-700 mb-4">
              If a payment fails, we may:
            </p>
            <ul className="list-disc pl-6 text-gray-700 mb-4 space-y-2">
              <li>Retry the payment using your stored payment method</li>
              <li>Downgrade your account to a free plan or suspend API access</li>
              <li>Terminate your account if payment is not received within 14 days</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">6. Service Level and Availability</h2>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">6.1 Service Level Agreement (SLA)</h3>
            <p className="text-gray-700 mb-4">
              We strive to maintain high availability of our Service:
            </p>
            <ul className="list-disc pl-6 text-gray-700 mb-4 space-y-2">
              <li><strong>Free and Developer Plans:</strong> Best-effort availability with no SLA guarantee</li>
              <li><strong>Growth Plan:</strong> 99.9% uptime SLA</li>
              <li><strong>Enterprise Plan:</strong> 99.99% uptime SLA with custom terms</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">6.2 Maintenance and Downtime</h3>
            <p className="text-gray-700 mb-4">
              We reserve the right to:
            </p>
            <ul className="list-disc pl-6 text-gray-700 mb-4 space-y-2">
              <li>Perform scheduled maintenance with advance notice when possible</li>
              <li>Conduct emergency maintenance without notice if necessary</li>
              <li>Modify, suspend, or discontinue any aspect of the Service</li>
            </ul>
            <p className="text-gray-700 mb-4">
              We are not liable for any downtime, service interruptions, or data loss that may occur.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">7. Intellectual Property Rights</h2>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">7.1 Our IP</h3>
            <p className="text-gray-700 mb-4">
              All rights, title, and interest in and to the Service, including all software, algorithms, documentation, trademarks, and content (excluding publicly available medical codes), are owned by Nuvii AI or our licensors. These Terms do not grant you any ownership rights to the Service.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">7.2 Medical Code Data</h3>
            <p className="text-gray-700 mb-4">
              ICD-10-CM codes are maintained by the Centers for Medicare & Medicaid Services (CMS) and are in the public domain. CPT codes are copyrighted by the American Medical Association (AMA). You agree to comply with all applicable licenses and restrictions on the use of medical coding data.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">7.3 Your Content</h3>
            <p className="text-gray-700 mb-4">
              You retain all rights to the clinical text and data you submit to our Service. By using the Service, you grant us a limited license to process your submissions solely for the purpose of providing the Service to you.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">8. Disclaimers and Limitation of Liability</h2>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">8.1 Service Provided &ldquo;As Is&rdquo;</h3>
            <p className="text-gray-700 mb-4">
              THE SERVICE IS PROVIDED &ldquo;AS IS&rdquo; AND &ldquo;AS AVAILABLE&rdquo; WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT, OR ACCURACY.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">8.2 Medical Disclaimer</h3>
            <p className="text-gray-700 mb-4">
              <strong className="text-red-600">Our Service provides medical coding suggestions for informational purposes only and is not a substitute for professional medical coding judgment.</strong> Code suggestions should always be reviewed and verified by qualified medical coding professionals. We do not guarantee the accuracy, completeness, or appropriateness of any code suggestions for billing or clinical purposes.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">8.3 Limitation of Liability</h3>
            <p className="text-gray-700 mb-4">
              TO THE MAXIMUM EXTENT PERMITTED BY LAW, NUVII AI SHALL NOT BE LIABLE FOR:
            </p>
            <ul className="list-disc pl-6 text-gray-700 mb-4 space-y-2">
              <li>Any indirect, incidental, special, consequential, or punitive damages</li>
              <li>Loss of profits, revenue, data, or business opportunities</li>
              <li>Service interruptions, errors, or inaccuracies in code suggestions</li>
              <li>Claims arising from coding errors, denied claims, or billing disputes</li>
              <li>Damages arising from unauthorized access to your account or data breaches</li>
            </ul>
            <p className="text-gray-700 mb-4">
              OUR TOTAL LIABILITY TO YOU FOR ALL CLAIMS ARISING FROM THESE TERMS OR YOUR USE OF THE SERVICE SHALL NOT EXCEED THE AMOUNT YOU PAID US IN THE 12 MONTHS PRECEDING THE CLAIM, OR $100, WHICHEVER IS GREATER.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">9. Indemnification</h2>
            <p className="text-gray-700 mb-4">
              You agree to indemnify, defend, and hold harmless Nuvii AI, its affiliates, officers, directors, employees, and agents from any claims, liabilities, damages, losses, or expenses (including reasonable attorneys&apos; fees) arising from:
            </p>
            <ul className="list-disc pl-6 text-gray-700 mb-4 space-y-2">
              <li>Your violation of these Terms</li>
              <li>Your use or misuse of the Service</li>
              <li>Your violation of any laws, regulations, or third-party rights</li>
              <li>Your submission of PHI without proper de-identification or authorization</li>
              <li>Claims arising from coding errors or billing disputes related to your use of our Service</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">10. Termination</h2>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">10.1 Termination by You</h3>
            <p className="text-gray-700 mb-4">
              You may terminate your account at any time by:
            </p>
            <ul className="list-disc pl-6 text-gray-700 mb-4 space-y-2">
              <li>Cancelling your subscription through your account dashboard or billing portal</li>
              <li>Contacting us at support@nuvii.ai to request account deletion</li>
            </ul>
            <p className="text-gray-700 mb-4">
              Termination does not entitle you to any refunds for prepaid fees.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">10.2 Termination by Us</h3>
            <p className="text-gray-700 mb-4">
              We may suspend or terminate your account immediately if:
            </p>
            <ul className="list-disc pl-6 text-gray-700 mb-4 space-y-2">
              <li>You violate these Terms</li>
              <li>Your payment method fails and is not updated within 14 days</li>
              <li>You engage in fraudulent, abusive, or illegal activity</li>
              <li>Your use of the Service poses a security risk or violates applicable laws</li>
              <li>We are required to do so by law or regulatory authority</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">10.3 Effect of Termination</h3>
            <p className="text-gray-700 mb-4">
              Upon termination:
            </p>
            <ul className="list-disc pl-6 text-gray-700 mb-4 space-y-2">
              <li>Your access to the Service will be immediately revoked</li>
              <li>All API keys will be deactivated</li>
              <li>You remain liable for all outstanding fees and charges</li>
              <li>Sections of these Terms that by their nature should survive termination will remain in effect</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">11. Modifications to the Service and Terms</h2>
            <p className="text-gray-700 mb-4">
              We reserve the right to modify or discontinue the Service (or any part thereof) at any time with or without notice. We may also modify these Terms from time to time. Material changes will be communicated via email or through a notice on our website. Your continued use of the Service after such changes constitutes acceptance of the revised Terms.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">12. Governing Law and Dispute Resolution</h2>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">12.1 Governing Law</h3>
            <p className="text-gray-700 mb-4">
              These Terms shall be governed by and construed in accordance with the laws of the State of California, United States, without regard to its conflict of law provisions.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">12.2 Dispute Resolution</h3>
            <p className="text-gray-700 mb-4">
              Any disputes arising from these Terms or your use of the Service shall be resolved through binding arbitration in accordance with the rules of the American Arbitration Association. You agree to waive any right to a jury trial or to participate in a class action lawsuit.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">13. Miscellaneous</h2>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">13.1 Entire Agreement</h3>
            <p className="text-gray-700 mb-4">
              These Terms, together with our Privacy Policy, constitute the entire agreement between you and Nuvii AI regarding the Service.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">13.2 Severability</h3>
            <p className="text-gray-700 mb-4">
              If any provision of these Terms is found to be unenforceable, that provision shall be modified to the minimum extent necessary to make it enforceable, and the remaining provisions shall remain in full effect.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">13.3 Waiver</h3>
            <p className="text-gray-700 mb-4">
              Our failure to enforce any right or provision of these Terms shall not constitute a waiver of such right or provision.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">13.4 Assignment</h3>
            <p className="text-gray-700 mb-4">
              You may not assign or transfer these Terms or your account without our prior written consent. We may assign these Terms at any time without notice.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">14. Contact Information</h2>
            <p className="text-gray-700 mb-4">
              If you have any questions about these Terms of Service, please contact us:
            </p>
            <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
              <p className="text-gray-700 mb-2"><strong>Email:</strong> support@nuvii.ai</p>
              <p className="text-gray-700"><strong>Website:</strong> <Link href="/" className="text-nuvii-blue hover:underline">https://nuvii.ai</Link></p>
            </div>
          </section>

          <section className="mb-8">
            <div className="bg-blue-50 border-l-4 border-nuvii-blue p-6 rounded">
              <p className="text-gray-900 font-semibold mb-2">Important Notice</p>
              <p className="text-gray-700 text-sm">
                By creating an account or using our Service, you acknowledge that you have read, understood, and agree to be bound by these Terms of Service and our <Link href="/privacy" className="text-nuvii-blue hover:underline">Privacy Policy</Link>.
              </p>
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

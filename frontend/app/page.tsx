import Link from 'next/link';
import { Search, Zap, Shield, BarChart, Code, Clock } from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="text-2xl font-bold text-blue-600">Nuvii API</div>
          <nav className="flex gap-4">
            <Link
              href="/login"
              className="px-4 py-2 text-gray-700 hover:text-gray-900"
            >
              Log in
            </Link>
            <Link
              href="/signup"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Sign up
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Medical Coding Lookup API
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Fast, accurate ICD-10 and CPT code lookups for healthcare applications.
            Simple REST API with intelligent search and AI-powered suggestions.
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/signup"
              className="px-8 py-3 bg-blue-600 text-white rounded-md text-lg font-semibold hover:bg-blue-700"
            >
              Get Started Free
            </Link>
            <Link
              href="/login"
              className="px-8 py-3 border border-gray-300 text-gray-700 rounded-md text-lg font-semibold hover:bg-gray-50"
            >
              View Documentation
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-gray-50 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            Everything you need for medical coding
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <Search className="w-12 h-12 text-blue-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Fast Code Search</h3>
              <p className="text-gray-600">
                Search ICD-10 and CPT codes by code or description with fuzzy matching and full-text search.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <Zap className="w-12 h-12 text-blue-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">AI-Powered Suggestions</h3>
              <p className="text-gray-600">
                Get intelligent code suggestions from clinical text using advanced keyword extraction.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <Shield className="w-12 h-12 text-blue-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Secure & Compliant</h3>
              <p className="text-gray-600">
                HIPAA-ready infrastructure with encrypted API keys and secure authentication.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <BarChart className="w-12 h-12 text-blue-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Usage Analytics</h3>
              <p className="text-gray-600">
                Track API usage with detailed logs, statistics, and insights for your application.
              </p>
            </div>

            {/* Feature 5 */}
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <Code className="w-12 h-12 text-blue-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Simple REST API</h3>
              <p className="text-gray-600">
                Clean, well-documented RESTful API with Swagger docs and code examples.
              </p>
            </div>

            {/* Feature 6 */}
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <Clock className="w-12 h-12 text-blue-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Rate Limiting</h3>
              <p className="text-gray-600">
                Fair usage policies with Redis-backed rate limiting and flexible tier options.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            Simple, transparent pricing
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {/* Free Tier */}
            <div className="border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow">
              <h3 className="text-xl font-semibold mb-2">Free</h3>
              <div className="text-3xl font-bold mb-4">$0<span className="text-lg text-gray-600">/mo</span></div>
              <ul className="space-y-2 mb-6 text-gray-600">
                <li>✓ 100 requests/month</li>
                <li>✓ 60 req/min rate limit</li>
                <li>✓ Community support</li>
                <li>✓ API documentation</li>
              </ul>
              <Link
                href="/signup"
                className="block w-full text-center px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
              >
                Get Started
              </Link>
            </div>

            {/* Developer Tier */}
            <div className="border-2 border-blue-600 rounded-lg p-6 hover:shadow-lg transition-shadow relative">
              <div className="absolute top-0 right-0 bg-blue-600 text-white px-3 py-1 text-sm rounded-bl-lg rounded-tr-lg">
                Popular
              </div>
              <h3 className="text-xl font-semibold mb-2">Developer</h3>
              <div className="text-3xl font-bold mb-4">$49<span className="text-lg text-gray-600">/mo</span></div>
              <ul className="space-y-2 mb-6 text-gray-600">
                <li>✓ 10,000 requests/month</li>
                <li>✓ 300 req/min rate limit</li>
                <li>✓ Email support</li>
                <li>✓ API documentation</li>
              </ul>
              <Link
                href="/signup"
                className="block w-full text-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Get Started
              </Link>
            </div>

            {/* Growth Tier */}
            <div className="border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow">
              <h3 className="text-xl font-semibold mb-2">Growth</h3>
              <div className="text-3xl font-bold mb-4">$299<span className="text-lg text-gray-600">/mo</span></div>
              <ul className="space-y-2 mb-6 text-gray-600">
                <li>✓ 100,000 requests/month</li>
                <li>✓ 1000 req/min rate limit</li>
                <li>✓ Priority support</li>
                <li>✓ 99.9% SLA</li>
              </ul>
              <Link
                href="/signup"
                className="block w-full text-center px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
              >
                Get Started
              </Link>
            </div>

            {/* Enterprise Tier */}
            <div className="border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow">
              <h3 className="text-xl font-semibold mb-2">Enterprise</h3>
              <div className="text-3xl font-bold mb-4">Custom</div>
              <ul className="space-y-2 mb-6 text-gray-600">
                <li>✓ 1M+ requests/month</li>
                <li>✓ Custom rate limits</li>
                <li>✓ Dedicated support</li>
                <li>✓ 99.99% SLA</li>
              </ul>
              <Link
                href="/signup"
                className="block w-full text-center px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
              >
                Contact Sales
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-blue-600 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to get started?
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            Create your free account and get your API key in minutes.
          </p>
          <Link
            href="/signup"
            className="inline-block px-8 py-3 bg-white text-blue-600 rounded-md text-lg font-semibold hover:bg-gray-100"
          >
            Sign up for free
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 bg-gray-50 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center text-gray-600">
          <p>&copy; 2025 Nuvii API. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

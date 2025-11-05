import Link from 'next/link';
import { Search, Zap, Shield, BarChart, Code, Clock, CheckCircle2, Copy } from 'lucide-react';
import Image from 'next/image';

export default function Home() {
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
          <nav className="hidden md:flex gap-6 items-center">
            <Link href="#features" className="text-gray-700 hover:text-gray-900">
              Features
            </Link>
            <Link href="#how-it-works" className="text-gray-700 hover:text-gray-900">
              How it Works
            </Link>
            <Link href="#pricing" className="text-gray-700 hover:text-gray-900">
              Pricing
            </Link>
            <Link href="https://api.nuvii.ai/docs" target="_blank" className="text-gray-700 hover:text-gray-900">
              Docs
            </Link>
            <Link href="/dashboard" className="text-gray-700 hover:text-gray-900">
              Dashboard
            </Link>
          </nav>
          <div className="flex gap-3">
            <Link
              href="/login"
              className="px-4 py-2 text-gray-700 hover:text-gray-900"
            >
              Log in
            </Link>
            <Link
              href="/signup"
              className="btn-primary"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
              The fastest, simplest way to add AI-powered medical coding to your app
            </h1>
            <p className="text-xl md:text-2xl text-gray-600 mb-4">
              AI-powered ICD-10 & CPT APIs that convert clinical notes into codes. No contracts. Ready in 5 minutes.
            </p>
            <div className="flex flex-wrap justify-center gap-6 mb-8 text-gray-700">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-nuvii-teal" />
                <span>Free tier to start</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-nuvii-teal" />
                <span>Instant API key & full docs</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-nuvii-teal" />
                <span>Pay-as-you-go pricing</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-nuvii-teal" />
                <span>Developer SDKs + examples</span>
              </div>
            </div>
            <div className="flex gap-4 justify-center">
              <Link
                href="/signup"
                className="btn-primary text-lg px-8 py-3"
              >
                Start with Free Tier
              </Link>
              <Link
                href="https://api.nuvii.ai/docs"
                target="_blank"
                className="btn-secondary text-lg px-8 py-3"
              >
                View Documentation
              </Link>
            </div>
          </div>

          {/* Code Example */}
          <div className="max-w-3xl mx-auto mt-12">
            <div className="bg-gray-900 rounded-lg p-6 text-sm font-mono text-gray-100 relative">
              <div className="text-gray-400 mb-2"># Try it now - Search for hypertension codes</div>
              <div className="text-green-400">curl</div>{' '}
              <span className="text-blue-300">https://api.nuvii.ai/api/v1/icd10/search?query=hypertension</span>{' '}
              <span className="text-yellow-300">\</span>
              <br />
              <span className="text-purple-300 ml-4">-H</span>{' '}
              <span className="text-orange-300">&quot;Authorization: Bearer YOUR_API_KEY&quot;</span>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="py-20 bg-gray-50 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-4xl font-bold text-center text-gray-900 mb-4">
            How it works
          </h2>
          <p className="text-xl text-gray-600 text-center mb-12 max-w-2xl mx-auto">
            Get started in minutes with our simple 4-step process
          </p>
          <div className="grid md:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 rounded-full flex items-center justify-center text-white text-2xl font-bold mx-auto mb-4 bg-nuvii-blue">
                1
              </div>
              <h3 className="text-xl font-semibold mb-2">Sign up & get API key</h3>
              <p className="text-gray-600">
                Create your free account and receive your API key instantly
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 rounded-full flex items-center justify-center text-white text-2xl font-bold mx-auto mb-4 bg-nuvii-blue">
                2
              </div>
              <h3 className="text-xl font-semibold mb-2">Integrate in minutes</h3>
              <p className="text-gray-600">
                Use our simple REST API with clear documentation and examples
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 rounded-full flex items-center justify-center text-white text-2xl font-bold mx-auto mb-4 bg-nuvii-blue">
                3
              </div>
              <h3 className="text-xl font-semibold mb-2">Query codes</h3>
              <p className="text-gray-600">
                Search ICD-10, CPT codes, or get AI-powered suggestions
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 rounded-full flex items-center justify-center text-white text-2xl font-bold mx-auto mb-4 bg-nuvii-blue">
                4
              </div>
              <h3 className="text-xl font-semibold mb-2">Scale with usage</h3>
              <p className="text-gray-600">
                Monitor usage and upgrade plans as your application grows
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-4xl font-bold text-center text-gray-900 mb-4">
            Everything you need for medical coding
          </h2>
          <p className="text-xl text-gray-600 text-center mb-12 max-w-2xl mx-auto">
            Built for developers who need reliable, fast medical coding data
          </p>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            <div className="bg-white p-6 rounded-lg border border-gray-200 hover:shadow-lg transition-shadow">
              <Search className="w-12 h-12 mb-4 text-nuvii-blue" />
              <h3 className="text-xl font-semibold mb-2">Fast Code Search</h3>
              <p className="text-gray-600">
                Search ICD-10 and CPT codes by code or description with fuzzy matching and full-text search.
              </p>
            </div>

            <div className="bg-white p-6 rounded-lg border border-gray-200 hover:shadow-lg transition-shadow">
              <Zap className="w-12 h-12 mb-4 text-nuvii-blue" />
              <h3 className="text-xl font-semibold mb-2">AI-Powered Suggestions</h3>
              <p className="text-gray-600">
                Get intelligent code suggestions from clinical text using advanced keyword extraction and matching.
              </p>
            </div>

            <div className="bg-white p-6 rounded-lg border border-gray-200 hover:shadow-lg transition-shadow">
              <Shield className="w-12 h-12 mb-4 text-nuvii-blue" />
              <h3 className="text-xl font-semibold mb-2">Secure & Compliant</h3>
              <p className="text-gray-600">
                All API calls encrypted. No PHI stored. HIPAA-ready infrastructure with secure authentication.
              </p>
            </div>

            <div className="bg-white p-6 rounded-lg border border-gray-200 hover:shadow-lg transition-shadow">
              <BarChart className="w-12 h-12 mb-4 text-nuvii-blue" />
              <h3 className="text-xl font-semibold mb-2">Usage Analytics</h3>
              <p className="text-gray-600">
                Track API usage with detailed logs, real-time statistics, and insights for your application.
              </p>
            </div>

            <div className="bg-white p-6 rounded-lg border border-gray-200 hover:shadow-lg transition-shadow">
              <Code className="w-12 h-12 mb-4 text-nuvii-blue" />
              <h3 className="text-xl font-semibold mb-2">Simple REST API</h3>
              <p className="text-gray-600">
                Clean, well-documented RESTful API with interactive Swagger docs and ready-to-use code examples.
              </p>
            </div>

            <div className="bg-white p-6 rounded-lg border border-gray-200 hover:shadow-lg transition-shadow">
              <Clock className="w-12 h-12 mb-4 text-nuvii-blue" />
              <h3 className="text-xl font-semibold mb-2">99.9% Uptime SLA</h3>
              <p className="text-gray-600">
                Production-ready infrastructure with rate limiting, auto-scaling, and 24/7 monitoring.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Use Cases Section */}
      <section className="py-20 bg-gray-50 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-4xl font-bold text-center text-gray-900 mb-4">
            Built for healthcare innovators
          </h2>
          <p className="text-xl text-gray-600 text-center mb-12 max-w-2xl mx-auto">
            Powering the next generation of healthcare applications
          </p>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white p-6 rounded-lg border border-gray-200">
              <h3 className="text-lg font-semibold mb-2">Telehealth Assistants</h3>
              <p className="text-gray-600 text-sm">
                Automatically suggest codes during virtual consultations
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg border border-gray-200">
              <h3 className="text-lg font-semibold mb-2">Clinical Documentation</h3>
              <p className="text-gray-600 text-sm">
                Streamline EHR coding with AI-powered code suggestions
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg border border-gray-200">
              <h3 className="text-lg font-semibold mb-2">Billing Automation</h3>
              <p className="text-gray-600 text-sm">
                Reduce coding errors and speed up medical billing workflows
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg border border-gray-200">
              <h3 className="text-lg font-semibold mb-2">Research Pipelines</h3>
              <p className="text-gray-600 text-sm">
                Process clinical data at scale for research and analytics
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Trust Signals */}
      <section className="py-12 border-y bg-white px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-wrap justify-center items-center gap-8 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-nuvii-teal" />
              <span className="font-semibold">All API calls encrypted</span>
            </div>
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-nuvii-teal" />
              <span className="font-semibold">No PHI stored</span>
            </div>
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-nuvii-teal" />
              <span className="font-semibold">GDPR/HIPAA-ready</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-nuvii-teal" />
              <span className="font-semibold">99.9% uptime guarantee</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-nuvii-teal" />
              <span className="font-semibold">No contract required</span>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-4xl font-bold text-center text-gray-900 mb-4">
            Simple, transparent pricing
          </h2>
          <p className="text-xl text-gray-600 text-center mb-2 max-w-2xl mx-auto">
            Start free. Scale as you grow. Cancel anytime.
          </p>
          <p className="text-sm text-gray-500 text-center mb-12">
            No contracts • Pay-as-you-go • Upgrade or downgrade anytime
          </p>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {/* Free Tier */}
            <div className="border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow bg-white">
              <h3 className="text-xl font-semibold mb-2">Free</h3>
              <div className="text-4xl font-bold mb-4">$0<span className="text-lg text-gray-600 font-normal">/mo</span></div>
              <p className="text-sm text-gray-500 mb-6">Perfect for testing and small projects</p>
              <ul className="space-y-3 mb-6 text-gray-700">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-5 h-5 mt-0.5 flex-shrink-0 text-nuvii-teal" />
                  <span>100 requests/month</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-5 h-5 mt-0.5 flex-shrink-0 text-nuvii-teal" />
                  <span>60 req/min rate limit</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-5 h-5 mt-0.5 flex-shrink-0 text-nuvii-teal" />
                  <span>Community support</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-5 h-5 mt-0.5 flex-shrink-0 text-nuvii-teal" />
                  <span>Full API documentation</span>
                </li>
              </ul>
              <Link
                href="/signup?plan=free"
                className="block w-full text-center px-4 py-3 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 font-semibold"
              >
                Start with Free Tier
              </Link>
            </div>

            {/* Developer Tier */}
            <div className="border-2 border-nuvii-blue rounded-lg p-6 hover:shadow-lg transition-shadow relative bg-white">
              <div className="absolute top-0 right-0 bg-nuvii-blue text-white px-3 py-1 text-sm rounded-bl-lg rounded-tr-lg font-semibold">
                Popular
              </div>
              <h3 className="text-xl font-semibold mb-2">Developer</h3>
              <div className="text-4xl font-bold mb-4">$49<span className="text-lg text-gray-600 font-normal">/mo</span></div>
              <p className="text-sm text-gray-500 mb-6">For individual developers</p>
              <ul className="space-y-3 mb-6 text-gray-700">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-5 h-5 mt-0.5 flex-shrink-0 text-nuvii-teal" />
                  <span>10,000 requests/month</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-5 h-5 mt-0.5 flex-shrink-0 text-nuvii-teal" />
                  <span>300 req/min rate limit</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-5 h-5 mt-0.5 flex-shrink-0 text-nuvii-teal" />
                  <span>Email support</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-5 h-5 mt-0.5 flex-shrink-0 text-nuvii-teal" />
                  <span>Usage analytics</span>
                </li>
              </ul>
              <Link
                href="/signup?plan=developer"
                className="btn-primary block w-full text-center"
              >
                Get Started
              </Link>
              <p className="text-xs text-gray-500 text-center mt-3">$5 per 1,000 additional requests</p>
            </div>

            {/* Growth Tier */}
            <div className="border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow bg-white">
              <h3 className="text-xl font-semibold mb-2">Growth</h3>
              <div className="text-4xl font-bold mb-4">$299<span className="text-lg text-gray-600 font-normal">/mo</span></div>
              <p className="text-sm text-gray-500 mb-6">For growing startups</p>
              <ul className="space-y-3 mb-6 text-gray-700">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-5 h-5 mt-0.5 flex-shrink-0 text-nuvii-teal" />
                  <span>100,000 requests/month</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-5 h-5 mt-0.5 flex-shrink-0 text-nuvii-teal" />
                  <span>1,000 req/min rate limit</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-5 h-5 mt-0.5 flex-shrink-0 text-nuvii-teal" />
                  <span>Priority support</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-5 h-5 mt-0.5 flex-shrink-0 text-nuvii-teal" />
                  <span>99.9% SLA</span>
                </li>
              </ul>
              <Link
                href="/signup?plan=growth"
                className="btn-secondary block w-full text-center"
              >
                Get Started
              </Link>
              <p className="text-xs text-gray-500 text-center mt-3">$2.50 per 1,000 additional requests</p>
            </div>

            {/* Enterprise Tier */}
            <div className="border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow bg-white">
              <h3 className="text-xl font-semibold mb-2">Enterprise</h3>
              <div className="text-4xl font-bold mb-4">Custom</div>
              <p className="text-sm text-gray-500 mb-6">For large organizations</p>
              <ul className="space-y-3 mb-6 text-gray-700">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-5 h-5 mt-0.5 flex-shrink-0 text-nuvii-teal" />
                  <span>1M+ requests/month</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-5 h-5 mt-0.5 flex-shrink-0 text-nuvii-teal" />
                  <span>Custom rate limits</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-5 h-5 mt-0.5 flex-shrink-0 text-nuvii-teal" />
                  <span>Dedicated support</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-5 h-5 mt-0.5 flex-shrink-0 text-nuvii-teal" />
                  <span>99.99% SLA</span>
                </li>
              </ul>
              <Link
                href="mailto:support@nuvii.ai"
                className="block w-full text-center px-4 py-3 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 font-semibold"
              >
                Contact Sales
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-nuvii-gradient">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl font-bold text-white mb-4">
            Ready to get started?
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            Create your free account and get your API key in minutes. No credit card required.
          </p>
          <Link
            href="/signup"
            className="inline-block px-8 py-3 bg-white rounded-md text-lg font-semibold hover:bg-gray-100 text-nuvii-blue"
          >
            Sign up for free
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 bg-gray-50 px-4 sm:px-6 lg:px-8 border-t">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <h3 className="font-semibold text-gray-900 mb-4">Product</h3>
              <ul className="space-y-2">
                <li><Link href="#features" className="text-gray-600 hover:text-gray-900">Features</Link></li>
                <li><Link href="#pricing" className="text-gray-600 hover:text-gray-900">Pricing</Link></li>
                <li><Link href="https://api.nuvii.ai/docs" target="_blank" className="text-gray-600 hover:text-gray-900">Documentation</Link></li>
                <li><Link href="https://api.nuvii.ai" target="_blank" className="text-gray-600 hover:text-gray-900">API Status</Link></li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-4">Company</h3>
              <ul className="space-y-2">
                <li><Link href="#" className="text-gray-600 hover:text-gray-900">About</Link></li>
                <li><Link href="mailto:support@nuvii.ai" className="text-gray-600 hover:text-gray-900">Contact</Link></li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-4">Legal</h3>
              <ul className="space-y-2">
                <li><Link href="#" className="text-gray-600 hover:text-gray-900">Privacy Policy</Link></li>
                <li><Link href="#" className="text-gray-600 hover:text-gray-900">Terms of Service</Link></li>
                <li><Link href="#" className="text-gray-600 hover:text-gray-900">Security</Link></li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-4">Support</h3>
              <ul className="space-y-2">
                <li><Link href="https://api.nuvii.ai/docs" target="_blank" className="text-gray-600 hover:text-gray-900">Help Center</Link></li>
                <li><Link href="mailto:support@nuvii.ai" className="text-gray-600 hover:text-gray-900">Email Support</Link></li>
              </ul>
            </div>
          </div>
          <div className="border-t pt-8 text-center text-gray-600">
            <p>&copy; 2025 Nuvii API. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

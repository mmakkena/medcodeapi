'use client';

import { useState } from 'react';
import { billingAPI } from '@/lib/api';
import { CreditCard, ExternalLink } from 'lucide-react';

export default function BillingPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleManageBilling = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await billingAPI.getPortal();
      // Open Stripe billing portal in new window
      window.open(response.data.url, '_blank');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to open billing portal');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Billing & Subscription</h1>
        <p className="mt-2 text-gray-600">
          Manage your subscription, payment methods, and billing history.
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Current Plan */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-xl font-semibold mb-2">Current Plan</h2>
            <p className="text-3xl font-bold text-blue-600">Free Tier</p>
            <p className="text-gray-600 mt-2">100 requests per month</p>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-500">Monthly Cost</div>
            <div className="text-2xl font-bold">$0</div>
          </div>
        </div>
      </div>

      {/* Upgrade Options */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold mb-4">Upgrade Your Plan</h2>
        <div className="grid md:grid-cols-3 gap-4">
          {/* Developer Plan */}
          <div className="border border-gray-200 rounded-lg p-4">
            <h3 className="font-semibold text-lg mb-2">Developer</h3>
            <div className="text-2xl font-bold mb-2">$49<span className="text-sm text-gray-600">/mo</span></div>
            <ul className="space-y-1 text-sm text-gray-600 mb-4">
              <li>✓ 10,000 requests/month</li>
              <li>✓ 300 req/min rate limit</li>
              <li>✓ Email support</li>
            </ul>
            <button
              onClick={handleManageBilling}
              disabled={loading}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Loading...' : 'Upgrade'}
            </button>
          </div>

          {/* Growth Plan */}
          <div className="border-2 border-blue-600 rounded-lg p-4 relative">
            <div className="absolute top-0 right-0 bg-blue-600 text-white px-2 py-1 text-xs rounded-bl rounded-tr">
              Popular
            </div>
            <h3 className="font-semibold text-lg mb-2">Growth</h3>
            <div className="text-2xl font-bold mb-2">$299<span className="text-sm text-gray-600">/mo</span></div>
            <ul className="space-y-1 text-sm text-gray-600 mb-4">
              <li>✓ 100,000 requests/month</li>
              <li>✓ 1000 req/min rate limit</li>
              <li>✓ Priority support</li>
              <li>✓ 99.9% SLA</li>
            </ul>
            <button
              onClick={handleManageBilling}
              disabled={loading}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Loading...' : 'Upgrade'}
            </button>
          </div>

          {/* Enterprise Plan */}
          <div className="border border-gray-200 rounded-lg p-4">
            <h3 className="font-semibold text-lg mb-2">Enterprise</h3>
            <div className="text-2xl font-bold mb-2">Custom</div>
            <ul className="space-y-1 text-sm text-gray-600 mb-4">
              <li>✓ 1M+ requests/month</li>
              <li>✓ Custom rate limits</li>
              <li>✓ Dedicated support</li>
              <li>✓ 99.99% SLA</li>
            </ul>
            <button
              onClick={handleManageBilling}
              disabled={loading}
              className="w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 disabled:opacity-50"
            >
              Contact Sales
            </button>
          </div>
        </div>
      </div>

      {/* Stripe Billing Portal */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-start gap-4">
          <CreditCard className="w-8 h-8 text-blue-600 flex-shrink-0" />
          <div className="flex-1">
            <h2 className="text-xl font-semibold mb-2">Manage Billing</h2>
            <p className="text-gray-600 mb-4">
              Access the Stripe billing portal to manage your payment methods, view invoices, and update your subscription.
            </p>
            <button
              onClick={handleManageBilling}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Opening...' : (
                <>
                  Open Billing Portal
                  <ExternalLink className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Billing Information */}
      <div className="bg-gray-50 rounded-lg border border-gray-200 p-6">
        <h3 className="font-semibold mb-3">Billing Information</h3>
        <div className="space-y-2 text-sm text-gray-600">
          <div className="flex justify-between">
            <span>Billing Cycle:</span>
            <span className="font-medium text-gray-900">Monthly</span>
          </div>
          <div className="flex justify-between">
            <span>Next Billing Date:</span>
            <span className="font-medium text-gray-900">N/A (Free Plan)</span>
          </div>
          <div className="flex justify-between">
            <span>Payment Method:</span>
            <span className="font-medium text-gray-900">None</span>
          </div>
        </div>
      </div>

      {/* Usage-Based Pricing Note */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-900">
          <strong>Note:</strong> All plans include usage-based pricing. If you exceed your monthly request limit,
          additional requests will be charged at $0.001 per request. You can set usage alerts in the billing portal.
        </p>
      </div>
    </div>
  );
}

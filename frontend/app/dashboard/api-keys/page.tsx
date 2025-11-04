'use client';

import { useEffect, useState } from 'react';
import { apiKeysAPI } from '@/lib/api';
import { Copy, Trash2, Check } from 'lucide-react';

export default function APIKeysPage() {
  const [apiKeys, setApiKeys] = useState<any[]>([]);
  const [newKeyName, setNewKeyName] = useState('');
  const [newKey, setNewKey] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchKeys();
  }, []);

  const fetchKeys = async () => {
    try {
      const response = await apiKeysAPI.list();
      setApiKeys(response.data);
    } catch (error) {
      console.error('Failed to fetch API keys:', error);
    }
  };

  const createKey = async () => {
    setLoading(true);
    try {
      const response = await apiKeysAPI.create(newKeyName || 'Unnamed Key');
      setNewKey(response.data.api_key);
      setNewKeyName('');
      await fetchKeys();
    } catch (error) {
      console.error('Failed to create API key:', error);
    } finally {
      setLoading(false);
    }
  };

  const revokeKey = async (id: string) => {
    if (confirm('Are you sure you want to revoke this API key? This action cannot be undone.')) {
      setDeletingId(id);
      setError('');
      try {
        await apiKeysAPI.revoke(id);
        await fetchKeys();
        alert('API key revoked successfully!');
      } catch (error: any) {
        const errorMsg = error.response?.data?.detail || 'Failed to revoke API key';
        setError(errorMsg);
        console.error('Failed to revoke API key:', error);
      } finally {
        setDeletingId(null);
      }
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
      // Fallback for browsers that don't support clipboard API
      const textArea = document.createElement('textarea');
      textArea.value = text;
      textArea.style.position = 'fixed';
      textArea.style.left = '-999999px';
      document.body.appendChild(textArea);
      textArea.select();
      try {
        document.execCommand('copy');
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      } catch (fallbackErr) {
        alert('Failed to copy. Please copy manually: ' + text);
      }
      document.body.removeChild(textArea);
    }
  };

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold">API Keys</h1>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md">
          {error}
        </div>
      )}

      {/* Create New Key */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4">Create New API Key</h2>
        <div className="flex gap-4">
          <input
            type="text"
            placeholder="API Key Name (optional)"
            className="flex-1 px-3 py-2 border rounded-md"
            value={newKeyName}
            onChange={(e) => setNewKeyName(e.target.value)}
          />
          <button
            onClick={createKey}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Creating...' : 'Create Key'}
          </button>
        </div>

        {newKey && (
          <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-md">
            <p className="text-sm font-medium text-green-800 mb-2">
              New API Key Created! Copy it now - you won't see it again.
            </p>
            <div className="flex items-center gap-2">
              <code className="flex-1 p-2 bg-white border rounded text-sm font-mono">
                {newKey}
              </code>
              <button
                onClick={() => copyToClipboard(newKey)}
                className={`p-2 rounded transition-colors ${
                  copied
                    ? 'bg-green-200 text-green-800'
                    : 'hover:bg-green-100'
                }`}
                title={copied ? 'Copied!' : 'Copy to clipboard'}
              >
                {copied ? (
                  <Check className="w-5 h-5" />
                ) : (
                  <Copy className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* API Keys List */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4">Your API Keys</h2>
        <div className="space-y-2">
          {apiKeys.map((key) => (
            <div key={key.id} className="flex justify-between items-center p-4 border rounded-md">
              <div>
                <p className="font-mono font-semibold">{key.key_prefix}...</p>
                <p className="text-sm text-gray-600">{key.name || 'Unnamed'}</p>
                <p className="text-xs text-gray-500">
                  Created: {new Date(key.created_at).toLocaleDateString()}
                  {key.last_used_at && ` • Last used: ${new Date(key.last_used_at).toLocaleDateString()}`}
                </p>
              </div>
              <button
                onClick={() => revokeKey(key.id)}
                disabled={deletingId === key.id}
                className="p-2 text-red-600 hover:bg-red-50 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                title="Revoke API key"
              >
                {deletingId === key.id ? (
                  <span className="animate-spin">⏳</span>
                ) : (
                  <Trash2 className="w-5 h-5" />
                )}
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
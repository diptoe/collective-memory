'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Copy, Check } from 'lucide-react';
import { api } from '@/lib/api';
import { Model, ModelProvider } from '@/types';
import { use } from 'react';
import { useAuthStore, isAdmin } from '@/lib/stores/auth-store';

export default function ModelDetailPage({ params }: { params: Promise<{ key: string }> }) {
  const { key } = use(params);

  const router = useRouter();
  const { user } = useAuthStore();
  const canEdit = isAdmin(user);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [model, setModel] = useState<Model | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [copiedField, setCopiedField] = useState<string | null>(null);

  const copyToClipboard = async (text: string, field: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const formatDateTime = (dateStr?: string) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    const year = date.getUTCFullYear();
    const month = String(date.getUTCMonth() + 1).padStart(2, '0');
    const day = String(date.getUTCDate()).padStart(2, '0');
    const hours = String(date.getUTCHours()).padStart(2, '0');
    const minutes = String(date.getUTCMinutes()).padStart(2, '0');
    const seconds = String(date.getUTCSeconds()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds} UTC`;
  };

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    provider: '' as ModelProvider,
    model_id: '',
    description: '',
    capabilities: '',
    context_window: 0,
    max_output_tokens: 0,
  });

  const providers: ModelProvider[] = ['anthropic', 'google', 'openai'];

  useEffect(() => {
    loadModel();
  }, [key]);

  async function loadModel() {
    try {
      setLoading(true);
      const res = await api.models.get(key);
      const m = res.data;

      if (m && m.model_key) {
        setModel(m);
        setFormData({
          name: m.name,
          provider: m.provider,
          model_id: m.model_id,
          description: m.description || '',
          capabilities: m.capabilities?.join(', ') || '',
          context_window: m.context_window || 0,
          max_output_tokens: m.max_output_tokens || 0,
        });
      } else {
        setError('Model not found');
      }
    } catch (err: any) {
      console.error('Failed to load model:', err);
      setError(err.response?.data?.msg || 'Failed to load model');
    } finally {
      setLoading(false);
    }
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);

    try {
      const capabilitiesList = formData.capabilities.split(',').map(c => c.trim()).filter(Boolean);

      await api.models.update(key, {
        name: formData.name,
        provider: formData.provider,
        model_id: formData.model_id,
        description: formData.description,
        capabilities: capabilitiesList,
        context_window: formData.context_window || undefined,
        max_output_tokens: formData.max_output_tokens || undefined,
      });

      await loadModel();
      setIsEditing(false);
    } catch (err: any) {
      setError(err.response?.data?.msg || 'Failed to update model');
    } finally {
      setSaving(false);
    }
  };

  const handleToggleStatus = async () => {
    if (!model) return;

    try {
      if (model.status === 'active') {
        await api.models.deprecate(key);
      }
      // No activate endpoint yet, so just reload
      loadModel();
    } catch (err: any) {
      setError(err.response?.data?.msg || 'Failed to update status');
    }
  };

  const getProviderColor = (provider: ModelProvider) => {
    switch (provider) {
      case 'anthropic': return 'bg-orange-50 text-orange-700 border-orange-200';
      case 'google': return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'openai': return 'bg-green-50 text-green-700 border-green-200';
      default: return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-cm-coffee">Loading model...</p>
      </div>
    );
  }

  if (!model && !loading) {
    return (
      <div className="p-6">
        <div className="bg-red-50 text-red-700 p-4 rounded-lg">
          {error || 'Model not found'}
        </div>
        <Link href="/models" className="mt-4 inline-block text-cm-terracotta hover:underline">
          &larr; Back to Models
        </Link>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            href="/models"
            className="text-cm-coffee hover:text-cm-charcoal transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </Link>
          <div>
            <h1 className="font-serif text-2xl font-semibold text-cm-charcoal flex items-center gap-3">
              {model?.name}
              <span className={`px-2 py-0.5 text-xs rounded-full border ${
                model?.status === 'active'
                  ? 'bg-green-50 text-green-700 border-green-200'
                  : 'bg-gray-100 text-gray-500 border-gray-200'
              }`}>
                {model?.status}
              </span>
            </h1>
            <p className="text-cm-coffee font-mono text-sm mt-1">
              {model?.model_id}
            </p>
          </div>
        </div>
        {canEdit && (
          <div className="flex items-center gap-3">
            {!isEditing && model?.status === 'active' && (
              <button
                onClick={handleToggleStatus}
                className="px-4 py-2 rounded-lg transition-colors border border-amber-200 text-amber-600 hover:bg-amber-50"
              >
                Deprecate
              </button>
            )}

            {isEditing ? (
              <button
                onClick={() => setIsEditing(false)}
                className="px-4 py-2 text-cm-coffee hover:text-cm-charcoal border border-cm-sand rounded-lg"
              >
                Cancel
              </button>
            ) : (
              <button
                onClick={() => setIsEditing(true)}
                className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-lg hover:bg-cm-sienna"
              >
                Edit Model
              </button>
            )}
          </div>
        )}
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 text-red-700 rounded-lg border border-red-200">
          {error}
        </div>
      )}

      {isEditing ? (
        <form onSubmit={handleSave} className="bg-cm-ivory rounded-xl border border-cm-sand shadow-sm p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-cm-charcoal mb-1">
                Display Name
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/20 focus:border-cm-terracotta"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-cm-charcoal mb-1">
                Provider
              </label>
              <select
                required
                value={formData.provider}
                onChange={(e) => setFormData({ ...formData, provider: e.target.value as ModelProvider })}
                className="w-full px-3 py-2 border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/20 focus:border-cm-terracotta"
              >
                {providers.map(p => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-cm-charcoal mb-1">
              Model ID (API identifier)
            </label>
            <input
              type="text"
              required
              value={formData.model_id}
              onChange={(e) => setFormData({ ...formData, model_id: e.target.value })}
              className="w-full px-3 py-2 border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/20 focus:border-cm-terracotta font-mono text-sm"
              placeholder="e.g., claude-opus-4-5-20251101"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-cm-charcoal mb-1">
              Description
            </label>
            <textarea
              rows={3}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/20 focus:border-cm-terracotta"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-cm-charcoal mb-1">
              Capabilities
            </label>
            <input
              type="text"
              value={formData.capabilities}
              onChange={(e) => setFormData({ ...formData, capabilities: e.target.value })}
              className="w-full px-3 py-2 border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/20 focus:border-cm-terracotta"
              placeholder="Comma separated, e.g., chat, code, vision, tools"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-cm-charcoal mb-1">
                Context Window
              </label>
              <input
                type="number"
                value={formData.context_window || ''}
                onChange={(e) => setFormData({ ...formData, context_window: parseInt(e.target.value) || 0 })}
                className="w-full px-3 py-2 border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/20 focus:border-cm-terracotta"
                placeholder="e.g., 200000"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-cm-charcoal mb-1">
                Max Output Tokens
              </label>
              <input
                type="number"
                value={formData.max_output_tokens || ''}
                onChange={(e) => setFormData({ ...formData, max_output_tokens: parseInt(e.target.value) || 0 })}
                className="w-full px-3 py-2 border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/20 focus:border-cm-terracotta"
                placeholder="e.g., 32000"
              />
            </div>
          </div>

          <div className="flex justify-end pt-4 border-t border-cm-sand">
            <button
              type="submit"
              disabled={saving}
              className="px-6 py-2 bg-cm-terracotta text-cm-ivory rounded-lg hover:bg-cm-sienna transition-colors disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="col-span-2 space-y-6">
              <div className="bg-cm-ivory rounded-xl border border-cm-sand p-6">
                <h3 className="text-sm font-medium text-cm-coffee mb-3">Description</h3>
                <p className="text-cm-charcoal">
                  {model?.description || <span className="text-cm-coffee/50 italic">No description provided</span>}
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-cm-ivory rounded-xl border border-cm-sand p-6">
                  <h3 className="text-sm font-medium text-cm-coffee mb-3">Capabilities</h3>
                  <div className="flex flex-wrap gap-2">
                    {model?.capabilities?.map(cap => (
                      <span key={cap} className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm border border-blue-100">
                        {cap}
                      </span>
                    ))}
                    {(!model?.capabilities || model.capabilities.length === 0) && (
                      <span className="text-cm-coffee/50 text-sm italic">None defined</span>
                    )}
                  </div>
                </div>

                <div className="bg-cm-ivory rounded-xl border border-cm-sand p-6">
                  <h3 className="text-sm font-medium text-cm-coffee mb-3">Token Limits</h3>
                  <div className="space-y-3">
                    <div>
                      <span className="text-xs text-cm-coffee uppercase tracking-wider">Context Window</span>
                      <p className="text-sm text-cm-charcoal mt-1 font-mono">
                        {model?.context_window?.toLocaleString() || 'Not specified'}
                      </p>
                    </div>
                    <div>
                      <span className="text-xs text-cm-coffee uppercase tracking-wider">Max Output</span>
                      <p className="text-sm text-cm-charcoal mt-1 font-mono">
                        {model?.max_output_tokens?.toLocaleString() || 'Not specified'}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <div className="bg-cm-ivory rounded-xl border border-cm-sand p-6">
                <h3 className="text-sm font-medium text-cm-coffee mb-4">Metadata</h3>

                <div className="space-y-4">
                  <div>
                    <span className="text-xs text-cm-coffee uppercase tracking-wider">Model Key</span>
                    <p className="font-mono text-sm text-cm-charcoal mt-1 break-all flex items-center gap-2">
                      {model?.model_key}
                      {model?.model_key && (
                        <button
                          onClick={() => copyToClipboard(model.model_key, 'key')}
                          className="p-1 text-cm-coffee/50 hover:text-cm-coffee transition-colors"
                          title="Copy model key"
                        >
                          {copiedField === 'key' ? <Check className="w-4 h-4 text-green-600" /> : <Copy className="w-4 h-4" />}
                        </button>
                      )}
                    </p>
                  </div>

                  <div>
                    <span className="text-xs text-cm-coffee uppercase tracking-wider">Provider</span>
                    <p className="mt-1">
                      <span className={`px-2 py-1 text-xs rounded-full border ${getProviderColor(model?.provider || 'anthropic')}`}>
                        {model?.provider}
                      </span>
                    </p>
                  </div>

                  <div>
                    <span className="text-xs text-cm-coffee uppercase tracking-wider">Model ID</span>
                    <p className="font-mono text-sm text-cm-charcoal mt-1 break-all flex items-center gap-2">
                      {model?.model_id}
                      {model?.model_id && (
                        <button
                          onClick={() => copyToClipboard(model.model_id, 'model_id')}
                          className="p-1 text-cm-coffee/50 hover:text-cm-coffee transition-colors"
                          title="Copy model ID"
                        >
                          {copiedField === 'model_id' ? <Check className="w-4 h-4 text-green-600" /> : <Copy className="w-4 h-4" />}
                        </button>
                      )}
                    </p>
                  </div>

                  <div>
                    <span className="text-xs text-cm-coffee uppercase tracking-wider">Created</span>
                    <p className="text-sm text-cm-charcoal mt-1">
                      {formatDateTime(model?.created_at)}
                    </p>
                  </div>

                  <div>
                    <span className="text-xs text-cm-coffee uppercase tracking-wider">Updated</span>
                    <p className="text-sm text-cm-charcoal mt-1">
                      {formatDateTime(model?.updated_at)}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

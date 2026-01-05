'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Model, ModelProvider } from '@/types';
import { cn } from '@/lib/utils';

const PROVIDER_COLORS: Record<ModelProvider, string> = {
  anthropic: 'bg-orange-100 text-orange-800',
  openai: 'bg-green-100 text-green-800',
  google: 'bg-blue-100 text-blue-800',
};

const PROVIDER_LABELS: Record<ModelProvider, string> = {
  anthropic: 'Anthropic',
  openai: 'OpenAI',
  google: 'Google',
};

export default function ModelsPage() {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedModel, setSelectedModel] = useState<Model | null>(null);
  const [filterProvider, setFilterProvider] = useState<string>('all');
  const [includeDeprecated, setIncludeDeprecated] = useState(false);

  // Load models
  useEffect(() => {
    async function loadModels() {
      try {
        const params: { provider?: string; include_deprecated?: boolean } = {};
        if (filterProvider !== 'all') {
          params.provider = filterProvider;
        }
        if (includeDeprecated) {
          params.include_deprecated = true;
        }
        const res = await api.models.list(params);
        setModels(res.data?.models || []);
      } catch (err) {
        console.error('Failed to load models:', err);
      } finally {
        setLoading(false);
      }
    }

    loadModels();
  }, [filterProvider, includeDeprecated]);

  // Group models by provider
  const modelsByProvider = models.reduce((acc, model) => {
    const provider = model.provider;
    if (!acc[provider]) {
      acc[provider] = [];
    }
    acc[provider].push(model);
    return acc;
  }, {} as Record<string, Model[]>);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-cm-coffee">Loading models...</p>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-serif text-2xl font-semibold text-cm-charcoal">
            AI Models
          </h1>
          <p className="text-cm-coffee mt-1">
            Manage available LLM models for AI agents
          </p>
        </div>
        <button className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-lg hover:bg-cm-sienna transition-colors">
          + Add Model
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 mb-6">
        <div className="flex items-center gap-1">
          <button
            onClick={() => setFilterProvider('all')}
            className={cn(
              'px-3 py-1.5 text-sm rounded-lg transition-colors',
              filterProvider === 'all'
                ? 'bg-cm-terracotta text-cm-ivory'
                : 'bg-cm-sand text-cm-coffee hover:bg-cm-sand/80'
            )}
          >
            All Providers
          </button>
          {(['anthropic', 'openai', 'google'] as ModelProvider[]).map((provider) => (
            <button
              key={provider}
              onClick={() => setFilterProvider(provider)}
              className={cn(
                'px-3 py-1.5 text-sm rounded-lg transition-colors',
                filterProvider === provider
                  ? 'bg-cm-terracotta text-cm-ivory'
                  : 'bg-cm-sand text-cm-coffee hover:bg-cm-sand/80'
              )}
            >
              {PROVIDER_LABELS[provider]}
            </button>
          ))}
        </div>

        <label className="flex items-center gap-2 text-sm text-cm-coffee">
          <input
            type="checkbox"
            checked={includeDeprecated}
            onChange={(e) => setIncludeDeprecated(e.target.checked)}
            className="rounded border-cm-sand"
          />
          Show deprecated
        </label>
      </div>

      {/* Models grid */}
      {models.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-cm-coffee mb-4">No models found.</p>
          <p className="text-sm text-cm-coffee/70">
            Add your first model or adjust your filters.
          </p>
        </div>
      ) : filterProvider === 'all' ? (
        // Show grouped by provider
        <div className="space-y-8">
          {Object.entries(modelsByProvider).map(([provider, providerModels]) => (
            <div key={provider}>
              <h2 className="font-serif text-lg font-semibold text-cm-charcoal mb-4 flex items-center gap-2">
                <span className={cn('px-2 py-0.5 rounded text-xs font-normal', PROVIDER_COLORS[provider as ModelProvider])}>
                  {PROVIDER_LABELS[provider as ModelProvider]}
                </span>
                <span className="text-cm-coffee font-normal text-sm">
                  ({providerModels.length} models)
                </span>
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {providerModels.map((model) => (
                  <ModelCard
                    key={model.model_key}
                    model={model}
                    onClick={() => setSelectedModel(model)}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        // Show flat list for single provider
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {models.map((model) => (
            <ModelCard
              key={model.model_key}
              model={model}
              onClick={() => setSelectedModel(model)}
            />
          ))}
        </div>
      )}

      {/* Detail modal */}
      {selectedModel && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-40"
          onClick={() => setSelectedModel(null)}
        >
          <div
            className="bg-cm-ivory rounded-xl shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-4 border-b border-cm-sand flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-cm-charcoal flex items-center gap-2">
                  {selectedModel.name}
                  <span className={cn('px-2 py-0.5 rounded text-xs', PROVIDER_COLORS[selectedModel.provider])}>
                    {PROVIDER_LABELS[selectedModel.provider]}
                  </span>
                </h3>
                <p className="text-sm text-cm-coffee font-mono">{selectedModel.model_id}</p>
              </div>
              <button
                onClick={() => setSelectedModel(null)}
                className="text-cm-coffee hover:text-cm-charcoal transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="p-4 overflow-y-auto max-h-[60vh]">
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-cm-coffee mb-1">Model Key</h4>
                  <p className="font-mono text-sm text-cm-charcoal">
                    {selectedModel.model_key}
                  </p>
                </div>

                <div>
                  <h4 className="text-sm font-medium text-cm-coffee mb-1">Status</h4>
                  <span className={cn(
                    'px-2 py-1 rounded text-xs',
                    selectedModel.status === 'active' ? 'bg-green-100 text-green-800' :
                    selectedModel.status === 'deprecated' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  )}>
                    {selectedModel.status}
                  </span>
                </div>

                {selectedModel.description && (
                  <div>
                    <h4 className="text-sm font-medium text-cm-coffee mb-1">Description</h4>
                    <p className="text-sm text-cm-charcoal">
                      {selectedModel.description}
                    </p>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4">
                  {selectedModel.context_window && (
                    <div>
                      <h4 className="text-sm font-medium text-cm-coffee mb-1">Context Window</h4>
                      <p className="text-sm text-cm-charcoal">
                        {selectedModel.context_window.toLocaleString()} tokens
                      </p>
                    </div>
                  )}
                  {selectedModel.max_output_tokens && (
                    <div>
                      <h4 className="text-sm font-medium text-cm-coffee mb-1">Max Output</h4>
                      <p className="text-sm text-cm-charcoal">
                        {selectedModel.max_output_tokens.toLocaleString()} tokens
                      </p>
                    </div>
                  )}
                </div>

                {selectedModel.capabilities && selectedModel.capabilities.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-cm-coffee mb-2">Capabilities</h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedModel.capabilities.map((cap) => (
                        <span
                          key={cap}
                          className="px-2 py-1 bg-cm-sand text-cm-coffee rounded text-xs"
                        >
                          {cap}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="pt-4 border-t border-cm-sand">
                  <p className="text-xs text-cm-coffee">
                    Created: {new Date(selectedModel.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ModelCard({ model, onClick }: { model: Model; onClick: () => void }) {
  return (
    <div
      onClick={onClick}
      className="p-4 bg-cm-cream border border-cm-sand rounded-lg hover:border-cm-terracotta/50 hover:shadow-md transition-all cursor-pointer"
    >
      <div className="flex items-start justify-between mb-2">
        <div>
          <h3 className="font-semibold text-cm-charcoal">{model.name}</h3>
          <p className="text-xs text-cm-coffee font-mono">{model.model_id}</p>
        </div>
        <span className={cn(
          'px-2 py-0.5 rounded text-xs',
          model.status === 'active' ? 'bg-green-100 text-green-800' :
          model.status === 'deprecated' ? 'bg-yellow-100 text-yellow-800' :
          'bg-red-100 text-red-800'
        )}>
          {model.status}
        </span>
      </div>

      {model.capabilities && model.capabilities.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2">
          {model.capabilities.slice(0, 4).map((cap) => (
            <span
              key={cap}
              className="px-1.5 py-0.5 bg-cm-sand/50 text-cm-coffee rounded text-xs"
            >
              {cap}
            </span>
          ))}
          {model.capabilities.length > 4 && (
            <span className="text-xs text-cm-coffee">
              +{model.capabilities.length - 4} more
            </span>
          )}
        </div>
      )}

      {model.context_window && (
        <p className="text-xs text-cm-coffee mt-2">
          {(model.context_window / 1000).toFixed(0)}K context
        </p>
      )}
    </div>
  );
}

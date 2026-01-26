'use client';

import { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import { api } from '@/lib/api';
import { Client, Model, Persona, ClientType, ModelProvider } from '@/types';
import { cn } from '@/lib/utils';

const CLIENT_ICONS: Record<string, string> = {
  'client-claude-code': '/icons/claude_code.svg',
  'client-claude-desktop': '/icons/claude_desktop.svg',
  'client-codex': '/icons/gpt_codex.svg',
  'client-gemini-cli': '/icons/gemini_cli.svg',
  'client-cursor': '/icons/cursor.svg',
};

const PROVIDER_ICONS: Record<ModelProvider, string> = {
  anthropic: '/icons/claude.svg',
  openai: '/icons/gpt.svg',
  google: '/icons/gemini.svg',
};

const PROVIDER_LABELS: Record<ModelProvider, string> = {
  anthropic: 'Anthropic',
  openai: 'OpenAI',
  google: 'Google',
};

interface AgentPropertiesModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AgentPropertiesModal({ isOpen, onClose }: AgentPropertiesModalProps) {
  const [clients, setClients] = useState<Client[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'clients' | 'models' | 'personas'>('clients');

  useEffect(() => {
    if (isOpen) {
      loadData();
    }
  }, [isOpen]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [clientsRes, modelsRes, personasRes] = await Promise.all([
        api.clients.list({ status: 'active', include_counts: true }),
        api.models.list({}),
        api.personas.list({}),
      ]);

      if (clientsRes.success && clientsRes.data) {
        setClients((clientsRes.data.clients || []) as Client[]);
      }
      if (modelsRes.success && modelsRes.data) {
        setModels(modelsRes.data.models || []);
      }
      if (personasRes.success && personasRes.data) {
        setPersonas((personasRes.data.personas || []).filter(p => p.status === 'active'));
      }
    } catch (err) {
      console.error('Failed to load agent properties:', err);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  // Group models by provider
  const modelsByProvider = models.reduce((acc, model) => {
    const provider = model.provider as ModelProvider;
    if (!acc[provider]) {
      acc[provider] = [];
    }
    acc[provider].push(model);
    return acc;
  }, {} as Record<ModelProvider, Model[]>);

  // Group personas by client
  const personasByClient = personas.reduce((acc, persona) => {
    const clientKey = persona.client_key || 'unlinked';
    if (!acc[clientKey]) {
      acc[clientKey] = [];
    }
    acc[clientKey].push(persona);
    return acc;
  }, {} as Record<string, Persona[]>);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-cm-cream rounded-lg shadow-xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-cm-sand">
          <h2 className="text-xl font-semibold text-cm-charcoal">Agent Properties</h2>
          <button
            onClick={onClose}
            className="p-1 text-cm-coffee hover:text-cm-charcoal transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-cm-sand">
          <button
            onClick={() => setActiveTab('clients')}
            className={cn(
              'flex-1 px-4 py-3 text-sm font-medium transition-colors',
              activeTab === 'clients'
                ? 'text-cm-terracotta border-b-2 border-cm-terracotta'
                : 'text-cm-coffee hover:text-cm-charcoal'
            )}
          >
            Clients ({clients.length})
          </button>
          <button
            onClick={() => setActiveTab('models')}
            className={cn(
              'flex-1 px-4 py-3 text-sm font-medium transition-colors',
              activeTab === 'models'
                ? 'text-cm-terracotta border-b-2 border-cm-terracotta'
                : 'text-cm-coffee hover:text-cm-charcoal'
            )}
          >
            Models ({models.length})
          </button>
          <button
            onClick={() => setActiveTab('personas')}
            className={cn(
              'flex-1 px-4 py-3 text-sm font-medium transition-colors',
              activeTab === 'personas'
                ? 'text-cm-terracotta border-b-2 border-cm-terracotta'
                : 'text-cm-coffee hover:text-cm-charcoal'
            )}
          >
            Personas ({personas.length})
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(80vh-140px)]">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <p className="text-cm-coffee">Loading...</p>
            </div>
          ) : (
            <>
              {/* Clients Tab */}
              {activeTab === 'clients' && (
                <div className="space-y-4">
                  <p className="text-sm text-cm-coffee mb-4">
                    Available AI development tools and IDEs that can connect to Collective Memory.
                  </p>
                  {clients.length === 0 ? (
                    <p className="text-center text-cm-coffee py-8">No clients configured</p>
                  ) : (
                    <div className="grid gap-3">
                      {clients.map((client) => (
                        <div
                          key={client.client_key}
                          className="flex items-center gap-4 p-4 bg-cm-ivory border border-cm-sand rounded-lg"
                        >
                          <img
                            src={CLIENT_ICONS[client.client_key] || '/icons/claude.svg'}
                            alt=""
                            className="w-10 h-10"
                          />
                          <div className="flex-1">
                            <h3 className="font-medium text-cm-charcoal">{client.name}</h3>
                            {client.description && (
                              <p className="text-sm text-cm-coffee mt-0.5 line-clamp-1">
                                {client.description}
                              </p>
                            )}
                            <div className="flex items-center gap-3 mt-1 text-xs text-cm-coffee">
                              {client.publisher && <span>{client.publisher}</span>}
                              {client.models_count !== undefined && (
                                <span>{client.models_count} models</span>
                              )}
                              {client.personas_count !== undefined && (
                                <span>{client.personas_count} personas</span>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Models Tab */}
              {activeTab === 'models' && (
                <div className="space-y-6">
                  <p className="text-sm text-cm-coffee mb-4">
                    AI models available for agent sessions, grouped by provider.
                  </p>
                  {models.length === 0 ? (
                    <p className="text-center text-cm-coffee py-8">No models configured</p>
                  ) : (
                    Object.entries(modelsByProvider).map(([provider, providerModels]) => (
                      <div key={provider}>
                        <div className="flex items-center gap-2 mb-3">
                          <img
                            src={PROVIDER_ICONS[provider as ModelProvider]}
                            alt=""
                            className="w-5 h-5"
                          />
                          <h3 className="font-medium text-cm-charcoal">
                            {PROVIDER_LABELS[provider as ModelProvider] || provider}
                          </h3>
                          <span className="text-xs text-cm-coffee">
                            ({providerModels.length})
                          </span>
                        </div>
                        <div className="grid gap-2 ml-7">
                          {providerModels.map((model) => (
                            <div
                              key={model.model_key}
                              className="flex items-center justify-between p-3 bg-cm-ivory border border-cm-sand rounded-lg"
                            >
                              <div>
                                <h4 className="text-sm font-medium text-cm-charcoal">
                                  {model.name}
                                </h4>
                                <p className="text-xs text-cm-coffee font-mono mt-0.5">
                                  {model.model_id}
                                </p>
                              </div>
                              <div className="flex items-center gap-2">
                                {model.context_window && (
                                  <span className="text-xs text-cm-coffee">
                                    {(model.context_window / 1000).toFixed(0)}K ctx
                                  </span>
                                )}
                                {model.capabilities && model.capabilities.length > 0 && (
                                  <div className="flex gap-1">
                                    {model.capabilities.slice(0, 2).map((cap) => (
                                      <span
                                        key={cap}
                                        className="px-1.5 py-0.5 bg-cm-sand/50 text-cm-coffee rounded text-xs"
                                      >
                                        {cap}
                                      </span>
                                    ))}
                                  </div>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* Personas Tab */}
              {activeTab === 'personas' && (
                <div className="space-y-4">
                  <p className="text-sm text-cm-coffee mb-4">
                    AI personas define behavioral roles and personalities for agent interactions.
                  </p>
                  {personas.length === 0 ? (
                    <p className="text-center text-cm-coffee py-8">No personas configured</p>
                  ) : (
                    <div className="grid gap-3">
                      {personas.map((persona) => {
                        const linkedClient = clients.find(c => c.client_key === persona.client_key);
                        return (
                          <div
                            key={persona.persona_key}
                            className="flex items-center gap-4 p-4 bg-cm-ivory border border-cm-sand rounded-lg"
                          >
                            <div
                              className="w-10 h-10 rounded-full flex items-center justify-center text-white text-sm font-medium flex-shrink-0"
                              style={{ backgroundColor: persona.color || '#d97757' }}
                            >
                              {persona.name.charAt(0)}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <h3 className="font-medium text-cm-charcoal">{persona.name}</h3>
                                <span className="text-xs text-cm-coffee font-mono">
                                  {persona.role}
                                </span>
                              </div>
                              {persona.capabilities && persona.capabilities.length > 0 && (
                                <div className="flex flex-wrap gap-1 mt-1">
                                  {persona.capabilities.slice(0, 4).map((cap) => (
                                    <span
                                      key={cap}
                                      className="px-1.5 py-0.5 bg-cm-sand/50 text-cm-coffee rounded text-xs"
                                    >
                                      {cap}
                                    </span>
                                  ))}
                                  {persona.capabilities.length > 4 && (
                                    <span className="text-xs text-cm-coffee">
                                      +{persona.capabilities.length - 4}
                                    </span>
                                  )}
                                </div>
                              )}
                            </div>
                            {linkedClient && (
                              <div className="flex items-center gap-1.5 flex-shrink-0">
                                <img
                                  src={CLIENT_ICONS[linkedClient.client_key] || '/icons/claude.svg'}
                                  alt=""
                                  className="w-4 h-4"
                                />
                                <span className="text-xs text-cm-coffee">{linkedClient.name}</span>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

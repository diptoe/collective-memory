import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { useDebugStore } from '@/lib/stores/debug-store';
import { Entity, Relationship, Persona, Conversation, ChatMessage, Agent, Message, ContextResult, Model, Client, ClientType, Activity, ActivitySummary, ActivityTimelinePoint, User, Session, Domain } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:5001/api';
const PERSON_ID = process.env.NEXT_PUBLIC_PERSON_ID || 'web-ui';

// Response type wrappers
interface EntitiesResponse { entities: Entity[] }
interface EntityResponse { entity: Entity }
interface EntityTypesResponse { types: { type: string; count: number }[] }
interface RelationshipsResponse { relationships: Relationship[] }
interface ModelsResponse { models: Model[] }
interface ModelResponse extends Model {}
interface ProvidersResponse { providers: string[] }
interface ClientsResponse { clients: Client[] }
interface ClientResponse extends Client {}
interface PersonasResponse { personas: Persona[] }
interface PersonaResponse extends Persona {}
interface ConversationsResponse { conversations: Conversation[] }
interface ConversationResponse { conversation: Conversation }
interface MessagesResponse { messages: ChatMessage[] }
interface MessageResponse { message: ChatMessage }
interface AgentsResponse { agents: Agent[] }
interface AgentResponse { agent: Agent }
interface FocusResponse { focus: string; focus_updated_at?: string }
interface InterAgentMessagesResponse { messages: Message[] }
interface ContextQueryResponse extends ContextResult { }
interface ActivitiesResponse { activities: Activity[]; count: number }
interface ActivitySummaryResponse extends ActivitySummary { }
interface ActivityTimelineResponse { timeline: ActivityTimelinePoint[]; hours: number; bucket_minutes: number }
interface ActivityTypesResponse { types: string[] }

// Auth response types
interface AuthUserResponse { user: User; session?: Session; session_expires_at?: string }
interface SessionsResponse { sessions: Session[] }
interface PatResponse { pat: string; pat_created_at: string }
interface UsersResponse { users: User[]; total: number; limit: number; offset: number }
interface UserResponse { user: User; session_count?: number }
interface UserStatsResponse { total: number; active: number; suspended: number; admins: number; users: number }

// Domain response types
interface DomainsResponse { domains: Domain[] }
interface DomainResponse { domain: Domain }
interface DomainUsersResponse { domain: Domain; users: User[] }
interface DomainStatsResponse { total: number; active: number; suspended: number; with_owner: number; users_with_domain: number; users_without_domain: number }

/**
 * API Response type from the backend
 */
export interface ApiResponse<T = unknown> {
  success: boolean;
  msg: string;
  data?: T;
}

/**
 * Debug request entry for the debug panel
 */
export interface DebugEntry {
  id: string;
  method: string;
  url: string;
  requestBody?: unknown;
  responseBody?: unknown;
  status?: number;
  duration?: number;
  timestamp: Date;
  error?: string;
}

/**
 * Base API client with debug panel integration
 */
class BaseApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
        'X-Agent-Id': `human:${PERSON_ID}`,
      },
      withCredentials: true,  // Enable cookie handling for auth
    });

    // Request interceptor - log outgoing requests
    this.client.interceptors.request.use(
      (config) => {
        const entry: Partial<DebugEntry> = {
          id: crypto.randomUUID(),
          method: config.method?.toUpperCase() || 'GET',
          url: config.url || '',
          requestBody: config.data,
          timestamp: new Date(),
        };

        // Store start time for duration calculation
        (config as any).__debugEntry = entry;
        (config as any).__startTime = Date.now();

        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor - log responses
    this.client.interceptors.response.use(
      (response) => {
        this.logResponse(response);
        return response;
      },
      (error) => {
        this.logError(error);
        return Promise.reject(error);
      }
    );
  }

  private logResponse(response: AxiosResponse) {
    const config = response.config as any;
    const entry: DebugEntry = {
      ...config.__debugEntry,
      responseBody: response.data,
      status: response.status,
      duration: Date.now() - config.__startTime,
    };

    // Add to debug store if available
    if (typeof window !== 'undefined') {
      useDebugStore.getState().addEntry(entry);
    }
  }

  private logError(error: any) {
    const config = error.config as any;
    if (!config) return;

    const entry: DebugEntry = {
      ...config.__debugEntry,
      responseBody: error.response?.data,
      status: error.response?.status || 0,
      duration: Date.now() - config.__startTime,
      error: error.message,
    };

    if (typeof window !== 'undefined') {
      useDebugStore.getState().addEntry(entry);
    }
  }

  async get<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.client.get<ApiResponse<T>>(url, config);
    return response.data;
  }

  async post<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.client.post<ApiResponse<T>>(url, data, config);
    return response.data;
  }

  async put<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.client.put<ApiResponse<T>>(url, data, config);
    return response.data;
  }

  async delete<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.client.delete<ApiResponse<T>>(url, config);
    return response.data;
  }
}

// Export singleton instance
export const apiClient = new BaseApiClient();

/**
 * Domain-specific API helpers
 */
export const api = {
  // Entities
  entities: {
    list: (params?: Record<string, string>) =>
      apiClient.get<EntitiesResponse>('/entities', { params }),
    get: (key: string, includeRelationships = false) =>
      apiClient.get<EntityResponse>(`/entities/${key}`, { params: { include_relationships: includeRelationships } }),
    create: (data: { entity_key?: string; entity_type: string; name: string; properties?: Record<string, unknown>; context_domain?: string }) =>
      apiClient.post<EntityResponse>('/entities', data),
    update: (key: string, data: Record<string, unknown>) =>
      apiClient.put<EntityResponse>(`/entities/${key}`, data),
    delete: (key: string) =>
      apiClient.delete(`/entities/${key}`),
    types: () =>
      apiClient.get<EntityTypesResponse>('/entities/types'),
  },

  // Relationships
  relationships: {
    list: (params?: { type?: string; entity?: string; limit?: number }) =>
      apiClient.get<RelationshipsResponse>('/relationships', { params }),
    create: (data: { from_entity_key: string; to_entity_key: string; relationship_type: string; properties?: Record<string, unknown> }) =>
      apiClient.post('/relationships', data),
    delete: (key: string) =>
      apiClient.delete(`/relationships/${key}`),
  },

  // Models
  models: {
    list: (params?: { provider?: string; include_deprecated?: boolean }) =>
      apiClient.get<ModelsResponse>('/models', { params }),
    get: (key: string) =>
      apiClient.get<ModelResponse>(`/models/${key}`),
    create: (data: { name: string; provider: string; model_id: string; capabilities?: string[]; context_window?: number; max_output_tokens?: number; description?: string }) =>
      apiClient.post<ModelResponse>('/models', data),
    update: (key: string, data: Record<string, unknown>) =>
      apiClient.put<ModelResponse>(`/models/${key}`, data),
    delete: (key: string) =>
      apiClient.delete(`/models/${key}`),
    deprecate: (key: string) =>
      apiClient.post(`/models/${key}/deprecate`),
    providers: () =>
      apiClient.get<ProvidersResponse>('/models/providers'),
    byProvider: (provider: string) =>
      apiClient.get<ModelsResponse>(`/models/by-provider/${provider}`),
  },

  // Clients
  clients: {
    list: () =>
      apiClient.get<ClientsResponse>('/clients'),
    get: (client: ClientType) =>
      apiClient.get<ClientResponse>(`/clients/${client}`),
    getPersonas: (client: ClientType) =>
      apiClient.get<PersonasResponse>(`/clients/${client}/personas`),
  },

  // Personas
  personas: {
    list: (params?: { role?: string; client?: string; include_archived?: boolean }) =>
      apiClient.get<PersonasResponse>('/personas', { params }),
    get: (key: string, includeSystemPrompt = false) =>
      apiClient.get<PersonaResponse>(`/personas/${key}`, { params: { include_system_prompt: includeSystemPrompt } }),
    getByRole: (role: string, includeSystemPrompt = false) =>
      apiClient.get<PersonaResponse>(`/personas/by-role/${role}`, { params: { include_system_prompt: includeSystemPrompt } }),
    create: (data: { name: string; role: string; system_prompt?: string; suggested_clients?: ClientType[]; color?: string; capabilities?: string[] }) =>
      apiClient.post<PersonaResponse>('/personas', data),
    update: (key: string, data: Record<string, unknown>) =>
      apiClient.put<PersonaResponse>(`/personas/${key}`, data),
    delete: (key: string) =>
      apiClient.delete(`/personas/${key}`),
    activate: (key: string) =>
      apiClient.post(`/personas/${key}/activate`),
  },

  // Conversations
  conversations: {
    list: (params?: { persona_key?: string; limit?: number }) =>
      apiClient.get<ConversationsResponse>('/conversations', { params }),
    get: (key: string, includeMessages = true) =>
      apiClient.get<ConversationResponse>(`/conversations/${key}`, { params: { include_messages: includeMessages } }),
    create: (data: { persona_key: string; title?: string; initial_message?: string }) =>
      apiClient.post<ConversationResponse>('/conversations', data),
    sendMessage: (conversationKey: string, content: string, role = 'user') =>
      apiClient.post<MessageResponse>(`/conversations/${conversationKey}/messages`, { content, role }),
    getMessages: (conversationKey: string, params?: { limit?: number; offset?: number }) =>
      apiClient.get<MessagesResponse>(`/conversations/${conversationKey}/messages`, { params }),
    clear: (conversationKey: string) =>
      apiClient.delete(`/conversations/${conversationKey}/clear`),
  },

  // Agents
  agents: {
    list: (params?: { active_only?: boolean; client?: string; persona_key?: string }) =>
      apiClient.get<AgentsResponse>('/agents', { params }),
    get: (agentId: string) =>
      apiClient.get<AgentResponse>(`/agents/${agentId}`),
    register: (data: {
      agent_id: string;
      client?: ClientType;
      model_key?: string;
      persona_key?: string;
      focus?: string;
      capabilities?: string[]
    }) =>
      apiClient.post<AgentResponse>('/agents/register', data),
    updateStatus: (agentId: string, status: Record<string, unknown>) =>
      apiClient.put<AgentResponse>(`/agents/${agentId}/status`, status),
    getFocus: (agentId: string) =>
      apiClient.get<FocusResponse>(`/agents/${agentId}/focus`),
    updateFocus: (agentId: string, focus: string) =>
      apiClient.put<FocusResponse>(`/agents/${agentId}/focus`, { focus }),
    heartbeat: (agentId: string) =>
      apiClient.post(`/agents/${agentId}/heartbeat`),
    delete: (agentKey: string) =>
      apiClient.delete<{ agent_id: string; agent_key: string }>(`/agents/${agentKey}`),
    deleteInactive: () =>
      apiClient.delete<{ deleted_count: number; deleted_agents: string[] }>('/agents/inactive'),
  },

  // Messages (inter-agent)
  messages: {
    list: (channel?: string, params?: { limit?: number; unread_only?: boolean; include_readers?: boolean; include_thread_info?: boolean; since?: string; entity_key?: string }) =>
      channel
        ? apiClient.get<InterAgentMessagesResponse>(`/messages/${channel}`, { params: { ...params, include_readers: true, include_thread_info: true } })
        : apiClient.get<InterAgentMessagesResponse>('/messages', { params: { ...params, include_readers: true, include_thread_info: true } }),
    byEntity: (entityKey: string, params?: { limit?: number }) =>
      apiClient.get<InterAgentMessagesResponse>('/messages', { params: { ...params, entity_key: entityKey, include_readers: true, include_thread_info: true } }),
    post: (data: { channel: string; from_agent: string; to_agent?: string; reply_to_key?: string; message_type: string; content: unknown; priority?: string }) =>
      apiClient.post('/messages', data),
    getChannel: (channel: string, params?: { limit?: number; unread_only?: boolean; include_readers?: boolean; include_thread_info?: boolean }) =>
      apiClient.get<InterAgentMessagesResponse>(`/messages/${channel}`, { params: { ...params, include_readers: true, include_thread_info: true } }),
    detail: (messageKey: string, params?: { include_thread?: boolean; include_readers?: boolean; include_entities?: boolean; for_agent?: string }) =>
      apiClient.get<Message>(`/messages/detail/${messageKey}`, { params: { include_thread: true, include_readers: true, include_entities: true, ...params } }),
    markRead: (messageKey: string) =>
      apiClient.post(`/messages/mark-read/${messageKey}`),
    confirm: (messageKey: string, confirmedBy: string) =>
      apiClient.post<Message>(`/messages/confirm/${messageKey}`, null, { params: { confirmed_by: confirmedBy } }),
    unconfirm: (messageKey: string) =>
      apiClient.delete<Message>(`/messages/confirm/${messageKey}`),
    deleteThread: (messageKey: string) =>
      apiClient.delete<{ deleted_count: number; deleted_keys: string[] }>(`/messages/detail/${messageKey}`),
    clearAll: () =>
      apiClient.delete<{ deleted_count: number }>('/messages/clear-all'),
  },

  // Context
  context: {
    query: (query: string, maxEntities = 20, maxTokens = 4000) =>
      apiClient.post<ContextQueryResponse>('/context/query', { query, max_entities: maxEntities, max_tokens: maxTokens }),
    subgraph: (entityKeys: string[], includeRelationships = true) =>
      apiClient.post('/context/subgraph', { entity_keys: entityKeys, include_relationships: includeRelationships }),
    neighbors: (entityKey: string, maxHops = 1) =>
      apiClient.post('/context/neighbors', { entity_key: entityKey, max_hops: maxHops }),
  },

  // Activities
  activities: {
    list: (params?: { limit?: number; type?: string; hours?: number; since?: string; until?: string; actor?: string }) =>
      apiClient.get<ActivitiesResponse>('/activities', { params }),
    summary: (params?: { hours?: number; since?: string; until?: string }) =>
      apiClient.get<ActivitySummaryResponse>('/activities/summary', { params }),
    timeline: (params?: { hours?: number; bucket_minutes?: number; since?: string }) =>
      apiClient.get<ActivityTimelineResponse>('/activities/timeline', { params }),
    types: () =>
      apiClient.get<ActivityTypesResponse>('/activities/types'),
    purge: () =>
      apiClient.post<{ deleted: number; retention_days: number }>('/activities/purge'),
  },

  // Auth
  auth: {
    register: (data: { email: string; password: string; first_name: string; last_name: string }) =>
      apiClient.post<AuthUserResponse>('/auth/register', data),
    login: (email: string, password: string, rememberMe = false) =>
      apiClient.post<AuthUserResponse>('/auth/login', { email, password, remember_me: rememberMe }),
    logout: () =>
      apiClient.post('/auth/logout'),
    me: () =>
      apiClient.get<AuthUserResponse>('/auth/me'),
    updateProfile: (data: { first_name?: string; last_name?: string }) =>
      apiClient.put<AuthUserResponse>('/auth/profile', data),
    changePassword: (currentPassword: string, newPassword: string) =>
      apiClient.put('/auth/password', { current_password: currentPassword, new_password: newPassword }),
    regeneratePat: () =>
      apiClient.post<PatResponse>('/auth/pat/regenerate'),
    sessions: () =>
      apiClient.get<SessionsResponse>('/auth/sessions'),
    revokeSession: (sessionKey: string) =>
      apiClient.delete(`/auth/sessions/${sessionKey}`),
    revokeAllSessions: () =>
      apiClient.delete<{ revoked_count: number }>('/auth/sessions/all'),
  },

  // Users (admin only)
  users: {
    list: (params?: { role?: string; status?: string; limit?: number; offset?: number }) =>
      apiClient.get<UsersResponse>('/users', { params }),
    get: (userKey: string) =>
      apiClient.get<UserResponse>(`/users/${userKey}`),
    update: (userKey: string, data: { first_name?: string; last_name?: string; status?: string }) =>
      apiClient.put<UserResponse>(`/users/${userKey}`, data),
    delete: (userKey: string) =>
      apiClient.delete<UserResponse>(`/users/${userKey}`),
    changeRole: (userKey: string, role: 'admin' | 'user') =>
      apiClient.post<UserResponse>(`/users/${userKey}/role`, { role }),
    sessions: (userKey: string) =>
      apiClient.get<SessionsResponse>(`/users/${userKey}/sessions`),
    revokeSessions: (userKey: string) =>
      apiClient.delete<{ revoked_count: number }>(`/users/${userKey}/sessions`),
    stats: () =>
      apiClient.get<UserStatsResponse>('/users/stats'),
    changeDomain: (userKey: string, domainKey: string | null) =>
      apiClient.put<UserResponse>(`/users/${userKey}/domain`, { domain_key: domainKey }),
  },

  // Domains (admin only)
  domains: {
    list: (params?: { status?: string }) =>
      apiClient.get<DomainsResponse>('/domains', { params }),
    get: (domainKey: string) =>
      apiClient.get<DomainResponse>(`/domains/${domainKey}`),
    create: (data: { name: string; slug: string; description?: string; owner_key?: string }) =>
      apiClient.post<DomainResponse>('/domains', data),
    update: (domainKey: string, data: { name?: string; description?: string; owner_key?: string | null; status?: string }) =>
      apiClient.put<DomainResponse>(`/domains/${domainKey}`, data),
    users: (domainKey: string) =>
      apiClient.get<DomainUsersResponse>(`/domains/${domainKey}/users`),
    stats: () =>
      apiClient.get<DomainStatsResponse>('/domains/stats'),
  },
};

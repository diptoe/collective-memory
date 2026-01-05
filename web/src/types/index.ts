/**
 * Collective Memory Platform - TypeScript Types
 */

// Entity types
export type EntityType = 'Person' | 'Project' | 'Technology' | 'Document' | 'Organization' | 'Concept' | 'Repository';

export interface Entity {
  entity_key: string;
  entity_type: EntityType;
  name: string;
  properties: Record<string, unknown>;
  context_domain?: string;
  confidence: number;
  source?: string;
  created_at: string;
  updated_at: string;
  relationships?: {
    outgoing: Relationship[];
    incoming: Relationship[];
  };
}

// Relationship types
export type RelationshipType =
  | 'WORKS_ON'
  | 'USES_TECHNOLOGY'
  | 'DEPENDS_ON'
  | 'COLLABORATES_WITH'
  | 'PART_OF'
  | 'CREATED'
  | 'OWNS'
  | 'RELATED_TO';

export interface Relationship {
  relationship_key: string;
  from_entity_key: string;
  to_entity_key: string;
  relationship_type: RelationshipType;
  properties: Record<string, unknown>;
  confidence: number;
  valid_from?: string;
  valid_to?: string;
  created_at: string;
  updated_at: string;
  from_entity?: EntitySummary;
  to_entity?: EntitySummary;
}

export interface EntitySummary {
  entity_key: string;
  name: string;
  entity_type: EntityType;
}

// Model types
export type ModelProvider = 'anthropic' | 'openai' | 'google';
export type ModelStatus = 'active' | 'deprecated' | 'disabled';

export interface Model {
  model_key: string;
  name: string;
  provider: ModelProvider;
  model_id: string;
  capabilities: string[];
  context_window?: number;
  max_output_tokens?: number;
  description?: string;
  status: ModelStatus;
  created_at: string;
  updated_at: string;
}

// Client types
export type ClientType = 'claude-code' | 'claude-desktop' | 'codex' | 'gemini' | 'custom';

export interface Client {
  client: ClientType;
  name: string;
  description: string;
  suggested_personas: string[];
}

// Persona types
export interface Persona {
  persona_key: string;
  name: string;
  role: string;
  system_prompt?: string;
  personality: {
    traits?: string[];
    communication_style?: string;
  };
  capabilities: string[];
  suggested_clients: ClientType[];
  avatar_url?: string;
  color: string;
  status: 'active' | 'inactive' | 'archived';
  created_at: string;
  updated_at: string;
}

// Conversation types
export interface Conversation {
  conversation_key: string;
  persona_key: string;
  agent_id?: string;
  title?: string;
  summary?: string;
  extracted_entities: string[];
  extra_data: Record<string, unknown>;
  message_count: number;
  created_at: string;
  updated_at: string;
  persona?: Persona;
  messages?: ChatMessage[];
}

export interface ChatMessage {
  message_key: string;
  conversation_key: string;
  persona_key?: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  extra_data: Record<string, unknown>;
  created_at: string;
  persona?: {
    name: string;
    color: string;
    avatar_url?: string;
  };
}

// Agent types
export interface Agent {
  agent_key: string;
  agent_id: string;
  client?: ClientType;
  model_key?: string;
  persona_key?: string;
  role?: string;  // Legacy, prefer persona_key
  focus?: string;
  focus_updated_at?: string;
  capabilities: string[];
  status: {
    current_task?: string;
    progress?: 'not_started' | 'in_progress' | 'blocked' | 'completed';
    blocker?: string;
    recent_actions?: string[];
  };
  is_active: boolean;
  last_heartbeat: string;
  created_at: string;
  updated_at: string;
  // Resolved references (optional, populated by API)
  model?: Model;
  persona?: Persona;
}

// Message types (inter-agent)
export type MessageType = 'question' | 'handoff' | 'announcement' | 'status';
export type Priority = 'high' | 'normal' | 'low';

export interface Message {
  message_key: string;
  channel: string;
  from_agent: string;
  to_agent?: string;
  message_type: MessageType;
  content: Record<string, unknown>;
  priority: Priority;
  is_read: boolean;
  read_at?: string;
  created_at: string;
}

// Context types
export interface ContextResult {
  entities: Entity[];
  relationships: Relationship[];
  context_text: string;
  entity_count: number;
  relationship_count: number;
}

// API response wrapper
export interface ApiResponse<T> {
  success: boolean;
  msg: string;
  data?: T;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

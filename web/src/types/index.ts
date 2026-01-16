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
export type ClientType = 'claude-code' | 'claude-desktop' | 'codex' | 'gemini-cli' | 'cursor';

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
  focused_mode?: boolean;
  focused_mode_expires_at?: string;
  is_focused?: boolean;
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
export type MessageType = 'status' | 'announcement' | 'request' | 'task' | 'message' | 'acknowledged' | 'waiting' | 'resumed';
export type Priority = 'normal' | 'high' | 'urgent';

export interface MessageReader {
  agent_id: string;
  read_at: string | null;
}

export interface Message {
  message_key: string;
  channel: string;
  from_agent: string;
  to_agent?: string;
  reply_to_key?: string;
  message_type: MessageType;
  content: Record<string, unknown>;
  priority: Priority;
  autonomous?: boolean;  // Task requiring receiver to work independently and reply
  confirmed?: boolean;   // Operator confirmed task completion
  confirmed_by?: string; // Who confirmed
  confirmed_at?: string; // When confirmed
  entity_keys?: string[];  // Linked entity keys for knowledge graph connection
  is_read: boolean;
  read_at?: string;
  created_at: string;
  // Per-agent read tracking
  readers?: MessageReader[];
  read_count?: number;
  // Threading info (when include_thread_info=true)
  reply_count?: number;
  has_parent?: boolean;
  // Full thread context (from /detail endpoint)
  parent?: Message;
  replies?: Message[];
  // Linked entities (when include_entities=true on detail endpoint)
  linked_entities?: Entity[];
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

// Activity types
export type ActivityType =
  | 'message_sent'
  | 'agent_heartbeat'
  | 'agent_registered'
  | 'search_performed'
  | 'entity_created'
  | 'entity_updated'
  | 'entity_deleted'
  | 'entity_read'
  | 'relationship_created'
  | 'relationship_deleted';

export interface Activity {
  activity_key: string;
  activity_type: ActivityType;
  actor: string;
  target_key?: string;
  target_type?: string;  // 'entity', 'message', 'agent', 'relationship'
  extra_data: Record<string, unknown>;
  created_at: string;
}

export interface ActivitySummary {
  summary: Record<string, number>;
  total: number;
}

export interface ActivityTimelinePoint {
  timestamp: string;
  total: number;
  [key: string]: number | string;  // Dynamic type counts
}

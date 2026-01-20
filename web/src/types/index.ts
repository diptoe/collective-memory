/**
 * Collective Memory Platform - TypeScript Types
 */

// Entity types
export type EntityType = 'Person' | 'Project' | 'Technology' | 'Document' | 'Organization' | 'Concept' | 'Repository' | 'Milestone';

export interface Entity {
  entity_key: string;
  entity_type: EntityType;
  name: string;
  properties: Record<string, unknown>;
  context_domain?: string;
  confidence: number;
  source?: string;
  scope_type?: 'domain' | 'team' | 'user' | null;
  scope_key?: string | null;
  scope_name?: string; // Resolved name of the scope (team name, user name, etc.)
  work_session_key?: string; // Work session this entity was created in
  created_at: string;
  updated_at: string;
  relationships?: {
    outgoing: Relationship[];
    incoming: Relationship[];
  };
  metrics?: Metric[]; // Populated for Milestone entities when include_metrics=true
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
  // User association
  user_key?: string;
  user_name?: string;      // Display name (denormalized)
  user_initials?: string;  // Initials for avatar
  // Team association
  team_key?: string;
  team_name?: string;      // Team name (denormalized)
  // Project/Repository context
  project_key?: string;
  project_name?: string;   // Repository name (denormalized)
  // Current milestone tracking (denormalized for display)
  current_milestone_key?: string;
  current_milestone_name?: string;
  current_milestone_status?: 'started' | 'completed' | 'blocked';
  current_milestone_started_at?: string;
  has_active_milestone?: boolean;
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

// Message scope types
export type MessageScope =
  | 'broadcast-domain'    // Visible to all agents/users in domain
  | 'broadcast-team'      // Visible to all agents/users in team
  | 'agent-agent'         // Direct message between agents
  | 'agent-user'          // Agent sending to user
  | 'user-agent'          // User sending to agent
  | 'user-agents'         // User broadcasting to all agents
  | 'agent-agents';       // Agent broadcasting to all agents

export interface Message {
  message_key: string;
  channel: string;
  from_key: string;       // agent_key or user_key of sender
  from_name?: string;     // Display name of sender (denormalized for readability)
  to_key?: string;        // agent_key or user_key of recipient (null for broadcasts)
  to_name?: string;       // Display name of recipient (denormalized for readability)
  user_key?: string;      // user_key associated with agent sender (if applicable)
  scope: MessageScope;    // Message visibility scope
  reply_to_key?: string;
  message_type: MessageType;
  content: Record<string, unknown>;
  priority: Priority;
  autonomous?: boolean;  // Task requiring receiver to work independently and reply
  confirmed?: boolean;   // Operator confirmed task completion
  confirmed_by?: string; // Who confirmed
  confirmed_at?: string; // When confirmed
  entity_keys?: string[];  // Linked entity keys for knowledge graph connection
  team_key?: string;     // Team scope (null = domain-wide)
  team_name?: string;    // Resolved team name for display
  work_session_key?: string; // Work session this message was sent in
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

// User authentication types
export type UserRole = 'admin' | 'domain_admin' | 'user';
export type UserStatus = 'active' | 'suspended' | 'pending';

export interface UserTeam {
  team_key: string;
  name: string;
  slug: string;
  description?: string;
  role: TeamMemberRole;
  membership_slug?: string;
}

export interface User {
  user_key: string;
  email: string;
  first_name: string;
  last_name: string;
  display_name: string;
  initials: string;
  role: UserRole;
  status: UserStatus;
  preferences: Record<string, unknown>;
  entity_key?: string;
  domain_key?: string;  // Domain for multi-tenancy
  domain?: {  // Domain details (when include_domain=true)
    domain_key: string;
    name: string;
    slug: string;
  };
  teams?: UserTeam[];  // User's team memberships (from auth/me)
  pat?: string;  // Only included when viewing own data
  pat_created_at?: string;
  last_login_at?: string;
  created_at: string;
  updated_at: string;
}

export interface Session {
  session_key: string;
  user_key: string;
  agent_key?: string;  // For MCP-initiated sessions
  device_info?: string;
  user_agent?: string;
  ip_address?: string;
  expires_at: string;
  last_activity_at: string;
  created_at: string;
  is_current?: boolean;  // Set when viewing own sessions
  // Extended fields for admin view
  user?: {
    email: string;
    name: string;
  };
  agent?: {
    agent_id: string;
    client: string;
  };
}

// Domain types (multi-tenancy)
export type DomainStatus = 'active' | 'suspended';

export interface Domain {
  domain_key: string;
  name: string;
  slug: string;
  description?: string;
  owner_key?: string;
  status: DomainStatus;
  created_at: string;
  updated_at: string;
  // Extended fields from API
  user_count?: number;
  owner?: {
    user_key: string;
    display_name: string;
    email: string;
  };
}

// Team types (flexible scoping within domains)
export type TeamStatus = 'active' | 'archived';
export type TeamMemberRole = 'owner' | 'admin' | 'member' | 'viewer';

export interface Team {
  team_key: string;
  domain_key: string;
  name: string;
  slug: string;
  description?: string;
  status: TeamStatus;
  settings: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  // Extended fields from API
  member_count?: number;
  domain?: {
    domain_key: string;
    name: string;
  };
}

export interface TeamMembership {
  membership_key: string;
  team_key: string;
  user_key: string;
  role: TeamMemberRole;
  slug?: string;  // Custom identifier for this user within the team (e.g., initials or nickname)
  joined_at: string;
  // Extended fields from API
  user?: {
    user_key: string;
    display_name: string;
    email: string;
    initials: string;
  };
  team?: {
    team_key: string;
    name: string;
  };
}

// Project types (dedicated repository/project tracking)
export type ProjectStatus = 'active' | 'archived';
export type RepositoryType = 'github' | 'gitlab' | 'bitbucket' | 'azure' | 'codecommit' | null;

export interface Project {
  project_key: string;
  name: string;
  description?: string;
  repository_type?: RepositoryType;
  repository_url?: string;
  repository_owner?: string;
  repository_name?: string;
  domain_key: string;
  entity_key?: string;  // Link to Project entity in knowledge graph
  status: ProjectStatus;
  extra_data?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  // Extended fields (when include_teams=true)
  teams?: TeamProject[];
}

// Team-Project association
export type TeamProjectRole = 'owner' | 'contributor' | 'viewer';

export interface TeamProject {
  team_project_key: string;
  team_key: string;
  project_key: string;
  role: TeamProjectRole;
  created_at: string;
  updated_at?: string;
  // Extended fields
  team?: Team;
  project?: Project;
}

// Scope types for entity visibility control
export type ScopeType = 'domain' | 'team' | 'user';
export type ScopeAccessLevel = 'owner' | 'admin' | 'member' | 'viewer';

export interface Scope {
  scope_type: ScopeType;
  scope_key: string;
  name: string;
  access_level: ScopeAccessLevel;
}

// Metric types
export interface Metric {
  metric_key: string;
  entity_key: string;
  metric_type: string;
  value: number;
  recorded_at: string;
  extra: Record<string, unknown>;
  tags: string[];
  created_at: string;
}

// Milestone properties (stored in Entity.properties for Milestone entities)
export interface MilestoneProperties {
  status: 'started' | 'completed' | 'blocked';
  goal?: string;
  outcome?: string;
  summary?: string;
  agent_id?: string;  // Agent that recorded the milestone (stable identifier)
  // Time tracking
  started_at?: string;    // ISO timestamp when milestone started
  completed_at?: string;  // ISO timestamp when milestone completed/blocked
  duration_seconds?: number;  // Calculated duration (completed_at - started_at)
}

// Common metric type constants for milestones
export const MilestoneMetricTypes = {
  // Auto-capture metrics
  TOOL_CALLS: 'milestone_tool_calls',
  FILES_TOUCHED: 'milestone_files_touched',
  LINES_ADDED: 'milestone_lines_added',
  LINES_REMOVED: 'milestone_lines_removed',
  COMMITS_MADE: 'milestone_commits_made',
  DURATION_MINUTES: 'milestone_duration_minutes',
  // Self-assessment metrics (1-5 scale)
  HUMAN_GUIDANCE: 'milestone_human_guidance',
  MODEL_UNDERSTANDING: 'milestone_model_understanding',
  MODEL_ACCURACY: 'milestone_model_accuracy',
  COLLABORATION_RATING: 'milestone_collaboration_rating',
  COMPLEXITY_RATING: 'milestone_complexity_rating',
} as const;

// Knowledge Stats types (scope-aggregated overview)
export interface ScopeStats {
  scope_type: ScopeType;
  scope_key: string;
  name: string;
  entity_count: number;
  entity_types: Record<string, number>;
  relationship_count: number;
}

export interface CrossScopeRelationship {
  from_scope: {
    scope_type: ScopeType;
    scope_key: string;
    name?: string;
  };
  to_scope: {
    scope_type: ScopeType;
    scope_key: string;
    name?: string;
  };
  count: number;
}

export interface KnowledgeStatsData {
  scopes: ScopeStats[];
  cross_scope_relationships: CrossScopeRelationship[];
  totals: {
    entities: number;
    relationships: number;
    scopes: number;
  };
}

export interface KnowledgeDomain {
  domain_key: string;
  name: string;
  slug: string;
}

// Work Session types (focused work periods on projects)
export type WorkSessionStatus = 'active' | 'closed' | 'expired';
export type WorkSessionClosedBy = 'user' | 'agent' | 'system' | null;

export interface WorkSession {
  session_key: string;
  user_key: string;
  project_key: string;
  team_key?: string;
  domain_key?: string;
  agent_id?: string;  // Agent that started the session (uses agent_id for stability across agent recreation)
  name?: string;
  status: WorkSessionStatus;
  started_at: string;
  ended_at?: string;
  last_activity_at: string;
  auto_close_at?: string;
  closed_by?: WorkSessionClosedBy;
  summary?: string;
  properties: Record<string, unknown>;
  // Computed fields
  time_remaining_seconds?: number;
  is_expired?: boolean;
  // Extended fields (always included by default)
  user?: {
    user_key: string;
    display_name: string;
    email: string;
  };
  project?: {
    project_key?: string;  // From Project table
    entity_key?: string;   // From Entity (legacy)
    name: string;
    description?: string;
    repository_type?: string;
    repository_url?: string;
    repository_owner?: string;
    repository_name?: string;
  };
  agent?: {
    agent_id: string;
    agent_key: string;
    client?: string;
    user_key?: string;
    user_name?: string;
    user_initials?: string;
    persona_name?: string;
    persona_role?: string;
    model_name?: string;
    model_id?: string;
  };
  // Stats (when include_stats=true)
  stats?: {
    milestone_count: number;
    message_count: number;
    other_entity_count: number;
    total_entity_count: number;
    entity_count: number; // Legacy, same as total_entity_count
  };
}

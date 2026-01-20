/**
 * Collective Memory MCP Tool Documentation
 *
 * This file contains comprehensive documentation for all 46 MCP tools
 * available in Collective Memory, organized by category.
 */

export interface ToolParameter {
  name: string;
  type: string;
  required: boolean;
  description: string;
  default?: string;
  enum?: string[];
}

export interface ToolExample {
  description: string;
  code: string;
}

export interface ToolDoc {
  name: string;
  category: string;
  categorySlug: string;
  description: string;
  longDescription?: string;
  parameters: ToolParameter[];
  returns: string;
  examples: ToolExample[];
  relatedTools: string[];
  whenToUse?: string[];
  tips?: string[];
}

export interface ToolCategory {
  name: string;
  slug: string;
  description: string;
  icon: string;
  toolCount: number;
}

export const TOOL_CATEGORIES: ToolCategory[] = [
  {
    name: 'Entity Management',
    slug: 'entities',
    description: 'Create, search, and manage entities in the knowledge graph',
    icon: '🔷',
    toolCount: 7,
  },
  {
    name: 'Relationships',
    slug: 'relationships',
    description: 'Connect entities and explore graph structure',
    icon: '🔗',
    toolCount: 3,
  },
  {
    name: 'Context & RAG',
    slug: 'context',
    description: 'Retrieve context for AI reasoning',
    icon: '🎯',
    toolCount: 2,
  },
  {
    name: 'Personas',
    slug: 'personas',
    description: 'AI personas for specialized interactions',
    icon: '🎭',
    toolCount: 2,
  },
  {
    name: 'Agent Discovery',
    slug: 'agents',
    description: 'Find and list active AI agents',
    icon: '🤖',
    toolCount: 1,
  },
  {
    name: 'Agent Identity',
    slug: 'identity',
    description: 'Register and manage your agent identity',
    icon: '🪪',
    toolCount: 3,
  },
  {
    name: 'Team & Scope',
    slug: 'teams',
    description: 'Team management and entity visibility scopes',
    icon: '👥',
    toolCount: 3,
  },
  {
    name: 'Messaging',
    slug: 'messaging',
    description: 'Inter-agent communication and message queue',
    icon: '💬',
    toolCount: 5,
  },
  {
    name: 'Model Management',
    slug: 'models',
    description: 'AI models, clients, and focus tracking',
    icon: '⚡',
    toolCount: 4,
  },
  {
    name: 'GitHub Repository',
    slug: 'github-repo',
    description: 'Sync repositories and view GitHub data',
    icon: '📦',
    toolCount: 4,
  },
  {
    name: 'GitHub Sync',
    slug: 'github-sync',
    description: 'Sync commit history and updates',
    icon: '🔄',
    toolCount: 2,
  },
  {
    name: 'GitHub Work Items',
    slug: 'github-work',
    description: 'Create entities from commits and issues',
    icon: '📋',
    toolCount: 3,
  },
  {
    name: 'Activity Monitoring',
    slug: 'activity',
    description: 'Track agent activity and summaries',
    icon: '📊',
    toolCount: 2,
  },
  {
    name: 'Work Sessions',
    slug: 'sessions',
    description: 'Manage focused work sessions',
    icon: '⏱️',
    toolCount: 5,
  },
  {
    name: 'Milestones',
    slug: 'milestones',
    description: 'Track progress and achievements',
    icon: '🏆',
    toolCount: 2,
  },
];

export const TOOL_DOCS: Record<string, ToolDoc> = {
  // ==========================================================
  // Entity Management Tools
  // ==========================================================
  search_entities: {
    name: 'search_entities',
    category: 'Entity Management',
    categorySlug: 'entities',
    description: 'Search for entities in the knowledge graph by name or type.',
    longDescription:
      'Search for entities using text queries and/or type filters. Supports partial name matching and returns entities with their keys, names, types, and properties.',
    parameters: [
      {
        name: 'query',
        type: 'string',
        required: false,
        description: 'Search query - matches entity names (partial match supported)',
      },
      {
        name: 'entity_type',
        type: 'string',
        required: false,
        description:
          'Filter by type: Person, Project, Technology, Organization, Document, Concept, or any custom type',
      },
      {
        name: 'limit',
        type: 'integer',
        required: false,
        description: 'Maximum results to return',
        default: '10',
      },
    ],
    returns: 'List of matching entities with keys, names, types, and properties.',
    examples: [
      { description: 'Search by name', code: '{"query": "React"}' },
      { description: 'Search by type', code: '{"entity_type": "Technology"}' },
      { description: 'Combined search', code: '{"query": "dashboard", "entity_type": "Project"}' },
    ],
    relatedTools: ['get_entity', 'create_entity', 'search_entities_semantic'],
    whenToUse: [
      'Before creating a new entity to check if it already exists',
      'When exploring what entities exist in the knowledge graph',
      'To find entities related to a specific topic or project',
    ],
  },

  get_entity: {
    name: 'get_entity',
    category: 'Entity Management',
    categorySlug: 'entities',
    description: 'Get detailed information about a specific entity by its key.',
    longDescription:
      'Retrieve complete details about an entity including all properties, metadata, scope information, and linked messages.',
    parameters: [
      {
        name: 'entity_key',
        type: 'string',
        required: true,
        description: "The unique entity key (e.g., 'swift-bold-keen-lion')",
      },
    ],
    returns: 'Complete entity data including name, type, properties, source attribution, and timestamps.',
    examples: [{ description: 'Get entity by key', code: '{"entity_key": "swift-bold-keen-lion"}' }],
    relatedTools: ['search_entities', 'update_entity', 'get_entity_context'],
    whenToUse: [
      'When you have an entity key and need full details',
      'To view all properties and metadata of an entity',
      'To see what messages are linked to an entity',
    ],
  },

  create_entity: {
    name: 'create_entity',
    category: 'Entity Management',
    categorySlug: 'entities',
    description: 'Create a new entity in the knowledge graph.',
    longDescription:
      'Create a new entity with a name, type, and optional properties. Your agent ID is automatically recorded as the source. Entities can be scoped to domain, team, or user visibility.',
    parameters: [
      {
        name: 'name',
        type: 'string',
        required: true,
        description: 'Entity name - should be clear and unique',
      },
      {
        name: 'entity_type',
        type: 'string',
        required: true,
        description: 'Type: Person, Project, Technology, Organization, Document, Concept, or custom',
      },
      {
        name: 'properties',
        type: 'object',
        required: false,
        description: 'Additional properties as key-value pairs (flexible schema)',
      },
      {
        name: 'scope_type',
        type: 'string',
        required: false,
        description: "Scope type: 'domain', 'team', or 'user'. If omitted, uses session default.",
        enum: ['domain', 'team', 'user'],
      },
      {
        name: 'scope_key',
        type: 'string',
        required: false,
        description: 'Scope key (team_key or user_key). Required if scope_type is set.',
      },
    ],
    returns: 'The created entity with its assigned entity_key and scope.',
    examples: [
      {
        description: 'Create a project',
        code: '{"name": "React Dashboard", "entity_type": "Project", "properties": {"status": "active"}}',
      },
      {
        description: 'Create team-scoped entity',
        code: '{"name": "Sarah Chen", "entity_type": "Person", "scope_type": "team", "scope_key": "team-xyz"}',
      },
    ],
    relatedTools: ['search_entities', 'update_entity', 'create_relationship'],
    whenToUse: [
      'After confirming an entity does not already exist (use search_entities first)',
      'When you need to add new knowledge to the graph',
      'To track people, projects, technologies, or concepts',
    ],
    tips: [
      'Always search before creating to avoid duplicates',
      'Use meaningful names that are easy to search for',
      'Include relevant properties for better context',
    ],
  },

  update_entity: {
    name: 'update_entity',
    category: 'Entity Management',
    categorySlug: 'entities',
    description: "Update an existing entity's name, type, properties, or scope.",
    parameters: [
      {
        name: 'entity_key',
        type: 'string',
        required: true,
        description: 'The entity key to update',
      },
      {
        name: 'name',
        type: 'string',
        required: false,
        description: 'New name (optional)',
      },
      {
        name: 'entity_type',
        type: 'string',
        required: false,
        description: 'New type (optional)',
      },
      {
        name: 'properties',
        type: 'object',
        required: false,
        description: 'Properties to add/update (merged with existing)',
      },
      {
        name: 'scope_type',
        type: 'string',
        required: false,
        description: 'New scope type (optional)',
        enum: ['domain', 'team', 'user'],
      },
      {
        name: 'scope_key',
        type: 'string',
        required: false,
        description: 'New scope key - team_key or user_key (required if scope_type is set)',
      },
    ],
    returns: 'Updated entity details.',
    examples: [
      { description: 'Update name', code: '{"entity_key": "swift-bold-keen-lion", "name": "React Dashboard v2"}' },
      {
        description: 'Add properties',
        code: '{"entity_key": "swift-bold-keen-lion", "properties": {"status": "completed"}}',
      },
    ],
    relatedTools: ['get_entity', 'create_entity', 'move_entity_scope'],
    tips: ['Properties are merged, not replaced. Set a property to null to remove it.'],
  },

  search_entities_semantic: {
    name: 'search_entities_semantic',
    category: 'Entity Management',
    categorySlug: 'entities',
    description: 'Semantic search using natural language. Finds entities by meaning, not just keywords.',
    longDescription:
      'Uses vector embeddings to find conceptually related entities. Enter a natural language description and find entities with similar semantic meaning.',
    parameters: [
      {
        name: 'query',
        type: 'string',
        required: true,
        description: 'Natural language description of what you are looking for',
      },
      {
        name: 'entity_type',
        type: 'string',
        required: false,
        description: 'Optionally filter results by type',
      },
      {
        name: 'limit',
        type: 'integer',
        required: false,
        description: 'Maximum results',
        default: '10',
      },
    ],
    returns: 'Entities ranked by semantic similarity with confidence scores.',
    examples: [
      { description: 'Find UI tools', code: '{"query": "tools for building user interfaces"}' },
      { description: 'Find people', code: '{"query": "people who work on authentication"}' },
    ],
    relatedTools: ['search_entities', 'get_context'],
    whenToUse: [
      'When keyword search is not finding what you need',
      'To find conceptually related entities',
      'For exploratory searches with natural language',
    ],
  },

  extract_entities_from_text: {
    name: 'extract_entities_from_text',
    category: 'Entity Management',
    categorySlug: 'entities',
    description: 'Extract named entities from text using NER (Named Entity Recognition).',
    parameters: [
      {
        name: 'text',
        type: 'string',
        required: true,
        description: 'Text to analyze for entity mentions',
      },
      {
        name: 'auto_create',
        type: 'boolean',
        required: false,
        description: "If true, automatically create entities that don't exist",
        default: 'false',
      },
    ],
    returns: 'List of extracted entities with their types. If auto_create=true, also returns created entity keys.',
    examples: [
      {
        description: 'Extract from text',
        code: '{"text": "Sarah from Acme Corp discussed the React migration with our team"}',
      },
      {
        description: 'Auto-create entities',
        code: '{"text": "The new dashboard uses PostgreSQL and Redis", "auto_create": true}',
      },
    ],
    relatedTools: ['create_entity', 'search_entities'],
    whenToUse: [
      'When processing meeting notes or documentation',
      'To automatically discover entities mentioned in text',
      'For bulk entity creation from documents',
    ],
  },

  move_entity_scope: {
    name: 'move_entity_scope',
    category: 'Entity Management',
    categorySlug: 'entities',
    description: 'Move an entity and its related entities to a different scope.',
    longDescription:
      'Requires domain_admin or admin role. Recursively updates connected entities via relationships unless include_related=false.',
    parameters: [
      {
        name: 'entity_key',
        type: 'string',
        required: true,
        description: 'The entity key to move',
      },
      {
        name: 'scope_type',
        type: 'string',
        required: true,
        description: 'Target scope type',
        enum: ['domain', 'team', 'user'],
      },
      {
        name: 'scope_key',
        type: 'string',
        required: true,
        description: 'Target scope key (domain_key, team_key, or user_key)',
      },
      {
        name: 'include_related',
        type: 'boolean',
        required: false,
        description: 'Include related entities recursively',
        default: 'true',
      },
    ],
    returns: 'Count and list of updated entities.',
    examples: [
      {
        description: 'Move to team',
        code: '{"entity_key": "ent-project", "scope_type": "team", "scope_key": "team-xyz"}',
      },
    ],
    relatedTools: ['update_entity', 'list_my_scopes'],
  },

  // ==========================================================
  // Relationship Tools
  // ==========================================================
  list_relationships: {
    name: 'list_relationships',
    category: 'Relationships',
    categorySlug: 'relationships',
    description: 'List relationships in the knowledge graph, optionally filtered by entity.',
    parameters: [
      {
        name: 'entity_key',
        type: 'string',
        required: false,
        description: 'Show only relationships involving this entity',
      },
      {
        name: 'limit',
        type: 'integer',
        required: false,
        description: 'Maximum results',
        default: '20',
      },
    ],
    returns: 'Relationships with from/to entity keys, types, and properties.',
    examples: [
      { description: 'All relationships', code: '{}' },
      { description: 'For specific entity', code: '{"entity_key": "swift-bold-keen-lion"}' },
    ],
    relatedTools: ['create_relationship', 'delete_relationship'],
    whenToUse: [
      'To understand how entities are connected',
      'To explore the graph structure around an entity',
    ],
  },

  create_relationship: {
    name: 'create_relationship',
    category: 'Relationships',
    categorySlug: 'relationships',
    description: 'Create a relationship between two entities.',
    longDescription:
      'Connect two entities with a typed relationship. Common types: WORKS_ON, KNOWS, USES, CREATED, BELONGS_TO, RELATED_TO.',
    parameters: [
      {
        name: 'from_entity_key',
        type: 'string',
        required: true,
        description: "Source entity key (the 'from' side)",
      },
      {
        name: 'to_entity_key',
        type: 'string',
        required: true,
        description: "Target entity key (the 'to' side)",
      },
      {
        name: 'relationship_type',
        type: 'string',
        required: true,
        description: 'WORKS_ON, KNOWS, USES, CREATED, BELONGS_TO, RELATED_TO, or custom',
      },
      {
        name: 'properties',
        type: 'object',
        required: false,
        description: 'Additional properties for the relationship',
      },
    ],
    returns: 'The created relationship with its assigned relationship_key.',
    examples: [
      {
        description: 'Person works on project',
        code: '{"from_entity_key": "ent-sarah", "to_entity_key": "ent-dashboard", "relationship_type": "WORKS_ON", "properties": {"role": "Tech Lead"}}',
      },
    ],
    relatedTools: ['list_relationships', 'delete_relationship'],
  },

  delete_relationship: {
    name: 'delete_relationship',
    category: 'Relationships',
    categorySlug: 'relationships',
    description: 'Delete a relationship from the knowledge graph.',
    parameters: [
      {
        name: 'relationship_key',
        type: 'string',
        required: true,
        description: 'The unique relationship key to delete',
      },
    ],
    returns: 'Confirmation of deletion.',
    examples: [{ description: 'Delete relationship', code: '{"relationship_key": "rel-abc123"}' }],
    relatedTools: ['list_relationships', 'create_relationship'],
    tips: ['Use list_relationships first to confirm the correct key before deleting.'],
  },

  // ==========================================================
  // Context Tools
  // ==========================================================
  get_context: {
    name: 'get_context',
    category: 'Context & RAG',
    categorySlug: 'context',
    description: 'Get relevant context from the knowledge graph for a query.',
    parameters: [
      {
        name: 'query',
        type: 'string',
        required: true,
        description: 'Query to find relevant context for',
      },
      {
        name: 'limit',
        type: 'integer',
        required: false,
        description: 'Maximum items to return',
        default: '10',
      },
    ],
    returns: 'Relevant entities and documents that provide context for the query.',
    examples: [{ description: 'Get context', code: '{"query": "authentication implementation"}' }],
    relatedTools: ['get_entity_context', 'search_entities_semantic'],
    whenToUse: [
      'When starting work on a topic and need background information',
      'For RAG (Retrieval Augmented Generation) workflows',
    ],
  },

  get_entity_context: {
    name: 'get_entity_context',
    category: 'Context & RAG',
    categorySlug: 'context',
    description: 'Get context centered around a specific entity.',
    parameters: [
      {
        name: 'entity_key',
        type: 'string',
        required: true,
        description: 'Entity to get context for',
      },
      {
        name: 'depth',
        type: 'integer',
        required: false,
        description: 'How many relationship hops to include',
        default: '2',
      },
    ],
    returns: 'Entity details plus related entities and their relationships.',
    examples: [{ description: 'Get entity context', code: '{"entity_key": "swift-bold-keen-lion"}' }],
    relatedTools: ['get_entity', 'get_context', 'list_relationships'],
  },

  // ==========================================================
  // Persona Tools
  // ==========================================================
  list_personas: {
    name: 'list_personas',
    category: 'Personas',
    categorySlug: 'personas',
    description: 'List available AI personas.',
    parameters: [],
    returns: 'List of personas with their roles, names, and descriptions.',
    examples: [{ description: 'List all personas', code: '{}' }],
    relatedTools: ['chat_with_persona', 'identify'],
    whenToUse: ['To see what personas are available for specialized interactions'],
  },

  chat_with_persona: {
    name: 'chat_with_persona',
    category: 'Personas',
    categorySlug: 'personas',
    description: 'Have a conversation with a specific AI persona.',
    parameters: [
      {
        name: 'persona_key',
        type: 'string',
        required: true,
        description: 'The persona to chat with',
      },
      {
        name: 'message',
        type: 'string',
        required: true,
        description: 'Your message to the persona',
      },
    ],
    returns: "The persona's response based on their role and expertise.",
    examples: [
      {
        description: 'Ask architect persona',
        code: '{"persona_key": "architect", "message": "How should I structure this microservice?"}',
      },
    ],
    relatedTools: ['list_personas'],
  },

  // ==========================================================
  // Agent Discovery
  // ==========================================================
  list_agents: {
    name: 'list_agents',
    category: 'Agent Discovery',
    categorySlug: 'agents',
    description: 'List active AI agents in Collective Memory.',
    parameters: [
      {
        name: 'active_only',
        type: 'boolean',
        required: false,
        description: 'Only show active agents',
        default: 'true',
      },
    ],
    returns: 'List of agents with their IDs, clients, models, and current focus.',
    examples: [
      { description: 'List active agents', code: '{}' },
      { description: 'List all agents', code: '{"active_only": false}' },
    ],
    relatedTools: ['identify', 'send_message'],
    whenToUse: ['To see who else is working in the system', 'Before sending a direct message to another agent'],
  },

  // ==========================================================
  // Identity Tools
  // ==========================================================
  identify: {
    name: 'identify',
    category: 'Agent Identity',
    categorySlug: 'identity',
    description: 'Identify yourself to Collective Memory. This is the FIRST tool you should call.',
    longDescription:
      'Register your agent with CM. When called without parameters, shows guidance for dynamic self-identification including available personas, clients, and models.',
    parameters: [
      {
        name: 'agent_id',
        type: 'string',
        required: true,
        description: "Your unique agent ID (e.g., 'claude-code-collective-memory')",
      },
      {
        name: 'client',
        type: 'string',
        required: true,
        description: 'Client type: claude-code, claude-desktop, codex, gemini-cli, cursor',
      },
      {
        name: 'model_id',
        type: 'string',
        required: true,
        description: "Your model identifier (e.g., 'claude-opus-4-5-20251101')",
      },
      {
        name: 'persona',
        type: 'string',
        required: false,
        description: 'Persona role: backend-code, frontend-code, architect, consultant, etc.',
      },
      {
        name: 'focus',
        type: 'string',
        required: false,
        description: 'What you are currently working on',
      },
      {
        name: 'team_key',
        type: 'string',
        required: false,
        description: 'Explicit team key to set as active',
      },
    ],
    returns: 'Either identity guidance (options) or confirmation of registration.',
    examples: [
      { description: 'Show options', code: '{}' },
      {
        description: 'Full registration',
        code: '{"agent_id": "claude-code-myproject", "client": "claude-code", "model_id": "claude-opus-4-5-20251101", "persona": "backend-code"}',
      },
    ],
    relatedTools: ['get_my_identity', 'update_my_identity'],
    whenToUse: ['Always call this first when connecting to CM', 'To see available options before registering'],
    tips: [
      'Create an agent_id that reflects your context (project name, task)',
      'You MUST provide client and model_id - you know these about yourself',
    ],
  },

  get_my_identity: {
    name: 'get_my_identity',
    category: 'Agent Identity',
    categorySlug: 'identity',
    description: 'Get your current identity in Collective Memory.',
    parameters: [],
    returns: 'Your agent ID, agent key, persona details, and registration status.',
    examples: [{ description: 'Check identity', code: '{}' }],
    relatedTools: ['identify', 'update_my_identity'],
    whenToUse: [
      'To verify your registration status',
      'To see your current persona and focus',
      'If not registered, shows guidance for self-identification',
    ],
  },

  update_my_identity: {
    name: 'update_my_identity',
    category: 'Agent Identity',
    categorySlug: 'identity',
    description: 'Change your identity in Collective Memory.',
    parameters: [
      {
        name: 'agent_id',
        type: 'string',
        required: false,
        description: 'New agent ID (creates NEW agent if different from current)',
      },
      {
        name: 'persona',
        type: 'string',
        required: false,
        description: 'New persona role',
      },
      {
        name: 'model_key',
        type: 'string',
        required: false,
        description: 'New model key',
      },
      {
        name: 'focus',
        type: 'string',
        required: false,
        description: 'Current work focus',
      },
    ],
    returns: 'Your new identity details after the change.',
    examples: [
      { description: 'Switch persona', code: '{"persona": "frontend-code"}' },
      { description: 'Update focus', code: '{"focus": "Working on auth module"}' },
    ],
    relatedTools: ['identify', 'get_my_identity'],
    tips: ['Changing agent_id creates a NEW agent registration'],
  },

  // ==========================================================
  // Team & Scope Tools
  // ==========================================================
  list_my_scopes: {
    name: 'list_my_scopes',
    category: 'Team & Scope',
    categorySlug: 'teams',
    description: 'List the scopes you have access to.',
    parameters: [],
    returns: 'List of available scopes with their types (domain, team, user) and access levels.',
    examples: [{ description: 'List scopes', code: '{}' }],
    relatedTools: ['set_active_team', 'list_teams'],
    whenToUse: ['To see what scopes you can create entities in', 'Before setting scope on a new entity'],
  },

  set_active_team: {
    name: 'set_active_team',
    category: 'Team & Scope',
    categorySlug: 'teams',
    description: 'Set your active team for default entity scoping.',
    parameters: [
      {
        name: 'team_key',
        type: 'string',
        required: true,
        description: 'Team key to set as active',
      },
    ],
    returns: 'Confirmation of active team change.',
    examples: [{ description: 'Set active team', code: '{"team_key": "team-backend"}' }],
    relatedTools: ['list_my_scopes', 'list_teams'],
    whenToUse: ['To change the default scope for new entities', 'When switching between team contexts'],
  },

  list_teams: {
    name: 'list_teams',
    category: 'Team & Scope',
    categorySlug: 'teams',
    description: 'List all teams in the domain.',
    parameters: [],
    returns: 'List of teams with their keys, names, and member counts.',
    examples: [{ description: 'List teams', code: '{}' }],
    relatedTools: ['set_active_team', 'list_my_scopes'],
  },

  // ==========================================================
  // Messaging Tools
  // ==========================================================
  send_message: {
    name: 'send_message',
    category: 'Messaging',
    categorySlug: 'messaging',
    description: 'Send a message to other agents or human coordinators via the message queue.',
    longDescription:
      'Messages appear in the Messages UI. Use for status updates, questions, handoffs, announcements, and autonomous task collaboration.',
    parameters: [
      {
        name: 'content',
        type: 'string',
        required: true,
        description: 'Message content',
      },
      {
        name: 'channel',
        type: 'string',
        required: false,
        description: 'Channel name: general, backend, frontend, urgent, or custom',
        default: 'general',
      },
      {
        name: 'message_type',
        type: 'string',
        required: false,
        description: 'Type: status, announcement, request, task, message, acknowledged, waiting, resumed',
        default: 'status',
      },
      {
        name: 'to_agent',
        type: 'string',
        required: false,
        description: 'Specific agent ID to send to (null for broadcast)',
      },
      {
        name: 'reply_to',
        type: 'string',
        required: false,
        description: 'message_key to reply to (creates threaded conversation)',
      },
      {
        name: 'priority',
        type: 'string',
        required: false,
        description: 'Priority: high, normal, low',
        default: 'normal',
      },
      {
        name: 'autonomous',
        type: 'boolean',
        required: false,
        description: 'Set true to request autonomous work from receiver',
        default: 'false',
      },
      {
        name: 'entity_keys',
        type: 'array',
        required: false,
        description: 'Entity keys to link this message to',
      },
    ],
    returns: 'Confirmation with message key.',
    examples: [
      { description: 'Status update', code: '{"channel": "general", "content": "Starting work on auth module"}' },
      {
        description: 'Request autonomous work',
        code: '{"to_agent": "claude-backend", "content": "Please implement the auth API", "autonomous": true}',
      },
    ],
    relatedTools: ['get_messages', 'mark_message_read'],
    whenToUse: [
      'To communicate with other agents or humans',
      'For status updates and announcements',
      'To request work from other agents',
    ],
  },

  get_messages: {
    name: 'get_messages',
    category: 'Messaging',
    categorySlug: 'messaging',
    description: 'Get messages from the message queue.',
    parameters: [
      {
        name: 'channel',
        type: 'string',
        required: false,
        description: 'Filter by channel',
      },
      {
        name: 'unread_only',
        type: 'boolean',
        required: false,
        description: 'Only unread messages',
        default: 'true',
      },
      {
        name: 'limit',
        type: 'integer',
        required: false,
        description: 'Maximum messages to retrieve',
        default: '20',
      },
      {
        name: 'since',
        type: 'string',
        required: false,
        description: 'Only return messages after this ISO8601 timestamp',
      },
    ],
    returns: 'List of messages with sender, content, type, and read status.',
    examples: [
      { description: 'Get unread messages', code: '{}' },
      { description: 'Get from channel', code: '{"channel": "backend"}' },
    ],
    relatedTools: ['send_message', 'mark_message_read', 'mark_all_messages_read'],
    whenToUse: ['To check for messages from other agents', 'At the start of a session to see what you missed'],
  },

  mark_message_read: {
    name: 'mark_message_read',
    category: 'Messaging',
    categorySlug: 'messaging',
    description: 'Mark a message as read by you.',
    parameters: [
      {
        name: 'message_key',
        type: 'string',
        required: true,
        description: 'The message key to mark as read',
      },
    ],
    returns: 'Confirmation.',
    examples: [{ description: 'Mark read', code: '{"message_key": "msg-abc123"}' }],
    relatedTools: ['get_messages', 'mark_all_messages_read'],
    tips: ['Uses per-agent tracking - other agents will still see the message as unread'],
  },

  mark_all_messages_read: {
    name: 'mark_all_messages_read',
    category: 'Messaging',
    categorySlug: 'messaging',
    description: 'Mark all unread messages as read for you.',
    parameters: [
      {
        name: 'channel',
        type: 'string',
        required: false,
        description: 'Only mark messages in this channel',
      },
    ],
    returns: 'Number of messages marked as read.',
    examples: [
      { description: 'Mark all read', code: '{}' },
      { description: 'Mark channel read', code: '{"channel": "backend"}' },
    ],
    relatedTools: ['get_messages', 'mark_message_read'],
  },

  link_message_entities: {
    name: 'link_message_entities',
    category: 'Messaging',
    categorySlug: 'messaging',
    description: 'Link entities to an existing message.',
    parameters: [
      {
        name: 'message_key',
        type: 'string',
        required: true,
        description: 'The message key to update',
      },
      {
        name: 'entity_keys',
        type: 'array',
        required: true,
        description: 'Entity keys to link/unlink',
      },
      {
        name: 'mode',
        type: 'string',
        required: false,
        description: 'Link mode: add (default), replace, or remove',
        default: 'add',
      },
    ],
    returns: 'Updated message with new entity links.',
    examples: [
      { description: 'Add entity link', code: '{"message_key": "msg-abc", "entity_keys": ["ent-xyz"]}' },
    ],
    relatedTools: ['send_message', 'get_messages'],
  },

  // ==========================================================
  // Model Management Tools
  // ==========================================================
  list_models: {
    name: 'list_models',
    category: 'Model Management',
    categorySlug: 'models',
    description: 'List available AI models.',
    parameters: [],
    returns: 'List of models with their keys, names, providers, and model IDs.',
    examples: [{ description: 'List models', code: '{}' }],
    relatedTools: ['list_clients', 'identify'],
  },

  list_clients: {
    name: 'list_clients',
    category: 'Model Management',
    categorySlug: 'models',
    description: 'List available AI clients.',
    parameters: [],
    returns: 'List of clients with their names and descriptions.',
    examples: [{ description: 'List clients', code: '{}' }],
    relatedTools: ['list_models', 'identify'],
  },

  update_focus: {
    name: 'update_focus',
    category: 'Model Management',
    categorySlug: 'models',
    description: 'Update your current work focus.',
    parameters: [
      {
        name: 'focus',
        type: 'string',
        required: true,
        description: 'Description of what you are working on',
      },
    ],
    returns: 'Confirmation of focus update.',
    examples: [{ description: 'Update focus', code: '{"focus": "Implementing user authentication"}' }],
    relatedTools: ['identify', 'get_my_identity'],
    whenToUse: ['To let others know what you are working on', 'When switching tasks'],
  },

  set_focused_mode: {
    name: 'set_focused_mode',
    category: 'Model Management',
    categorySlug: 'models',
    description: 'Enable or disable focused mode (reduces notifications).',
    parameters: [
      {
        name: 'enabled',
        type: 'boolean',
        required: true,
        description: 'Whether to enable focused mode',
      },
    ],
    returns: 'Confirmation of mode change.',
    examples: [{ description: 'Enable focus', code: '{"enabled": true}' }],
    relatedTools: ['update_focus'],
  },

  // ==========================================================
  // GitHub Repository Tools
  // ==========================================================
  sync_repository: {
    name: 'sync_repository',
    category: 'GitHub Repository',
    categorySlug: 'github-repo',
    description: 'Sync a Repository entity with live data from GitHub.',
    parameters: [
      {
        name: 'repository_url',
        type: 'string',
        required: true,
        description: 'GitHub repository URL (e.g., https://github.com/owner/repo) or owner/repo format',
      },
      {
        name: 'create_if_missing',
        type: 'boolean',
        required: false,
        description: "Create Repository entity if it doesn't exist",
        default: 'true',
      },
    ],
    returns: 'Sync results with current GitHub stats and entity key.',
    examples: [
      { description: 'Sync repository', code: '{"repository_url": "https://github.com/owner/repo"}' },
    ],
    relatedTools: ['get_repo_issues', 'get_repo_commits'],
    whenToUse: [
      'To update or create a Repository entity with current stats',
      'When starting work on a new repository',
    ],
  },

  get_repo_issues: {
    name: 'get_repo_issues',
    category: 'GitHub Repository',
    categorySlug: 'github-repo',
    description: 'Get issues from a GitHub repository.',
    parameters: [
      {
        name: 'repository_url',
        type: 'string',
        required: true,
        description: 'GitHub repository URL or owner/repo format',
      },
      {
        name: 'state',
        type: 'string',
        required: false,
        description: "Issue state: 'open', 'closed', or 'all'",
        default: 'open',
      },
      {
        name: 'limit',
        type: 'integer',
        required: false,
        description: 'Maximum issues to return',
        default: '20',
      },
      {
        name: 'labels',
        type: 'string',
        required: false,
        description: 'Comma-separated labels to filter by',
      },
    ],
    returns: 'List of issues with numbers, titles, authors, labels, and comment counts.',
    examples: [
      { description: 'Get open issues', code: '{"repository_url": "owner/repo"}' },
      { description: 'Filter by label', code: '{"repository_url": "owner/repo", "labels": "bug,help wanted"}' },
    ],
    relatedTools: ['sync_repository', 'create_issue_entity'],
  },

  get_repo_commits: {
    name: 'get_repo_commits',
    category: 'GitHub Repository',
    categorySlug: 'github-repo',
    description: 'Get recent commits from a GitHub repository.',
    parameters: [
      {
        name: 'repository_url',
        type: 'string',
        required: true,
        description: 'GitHub repository URL or owner/repo format',
      },
      {
        name: 'days',
        type: 'integer',
        required: false,
        description: 'Number of days to look back',
        default: '7',
      },
      {
        name: 'limit',
        type: 'integer',
        required: false,
        description: 'Maximum commits to return',
        default: '20',
      },
      {
        name: 'branch',
        type: 'string',
        required: false,
        description: 'Branch to get commits from',
      },
    ],
    returns: 'Commit list with SHA, message, author, stats, and co-authors.',
    examples: [
      { description: 'Last 7 days', code: '{"repository_url": "owner/repo"}' },
      { description: 'Last 30 days', code: '{"repository_url": "owner/repo", "days": 30}' },
    ],
    relatedTools: ['sync_repository', 'create_commit_entity'],
    tips: ['Includes AI co-author detection (Claude, Copilot)'],
  },

  get_repo_contributors: {
    name: 'get_repo_contributors',
    category: 'GitHub Repository',
    categorySlug: 'github-repo',
    description: 'Get contributors for a GitHub repository.',
    parameters: [
      {
        name: 'repository_url',
        type: 'string',
        required: true,
        description: 'GitHub repository URL or owner/repo format',
      },
      {
        name: 'limit',
        type: 'integer',
        required: false,
        description: 'Maximum contributors to return',
        default: '20',
      },
    ],
    returns: 'Contributors ranked by commit count with percentages.',
    examples: [{ description: 'Get contributors', code: '{"repository_url": "owner/repo"}' }],
    relatedTools: ['sync_repository', 'get_repo_commits'],
  },

  // ==========================================================
  // GitHub Sync Tools
  // ==========================================================
  sync_repository_history: {
    name: 'sync_repository_history',
    category: 'GitHub Sync',
    categorySlug: 'github-sync',
    description: 'Sync full commit history for a repository.',
    parameters: [
      {
        name: 'repository_url',
        type: 'string',
        required: true,
        description: 'GitHub repository URL',
      },
      {
        name: 'days',
        type: 'integer',
        required: false,
        description: 'Number of days of history to sync',
        default: '90',
      },
    ],
    returns: 'Summary of synced commits and any AI co-authored commits found.',
    examples: [{ description: 'Sync 90 days', code: '{"repository_url": "owner/repo"}' }],
    relatedTools: ['sync_repository_updates', 'sync_repository'],
  },

  sync_repository_updates: {
    name: 'sync_repository_updates',
    category: 'GitHub Sync',
    categorySlug: 'github-sync',
    description: 'Sync recent updates (incremental sync).',
    parameters: [
      {
        name: 'repository_url',
        type: 'string',
        required: true,
        description: 'GitHub repository URL',
      },
    ],
    returns: 'Summary of new commits since last sync.',
    examples: [{ description: 'Sync updates', code: '{"repository_url": "owner/repo"}' }],
    relatedTools: ['sync_repository_history', 'sync_repository'],
  },

  // ==========================================================
  // GitHub Work Item Tools
  // ==========================================================
  create_commit_entity: {
    name: 'create_commit_entity',
    category: 'GitHub Work Items',
    categorySlug: 'github-work',
    description: 'Create an entity from a GitHub commit.',
    parameters: [
      {
        name: 'repository_url',
        type: 'string',
        required: true,
        description: 'GitHub repository URL',
      },
      {
        name: 'sha',
        type: 'string',
        required: true,
        description: 'Commit SHA',
      },
    ],
    returns: 'Created entity with commit details.',
    examples: [
      { description: 'Create from commit', code: '{"repository_url": "owner/repo", "sha": "abc123"}' },
    ],
    relatedTools: ['get_repo_commits', 'link_work_item'],
  },

  create_issue_entity: {
    name: 'create_issue_entity',
    category: 'GitHub Work Items',
    categorySlug: 'github-work',
    description: 'Create an entity from a GitHub issue.',
    parameters: [
      {
        name: 'repository_url',
        type: 'string',
        required: true,
        description: 'GitHub repository URL',
      },
      {
        name: 'issue_number',
        type: 'integer',
        required: true,
        description: 'Issue number',
      },
    ],
    returns: 'Created entity with issue details.',
    examples: [
      { description: 'Create from issue', code: '{"repository_url": "owner/repo", "issue_number": 42}' },
    ],
    relatedTools: ['get_repo_issues', 'link_work_item'],
  },

  link_work_item: {
    name: 'link_work_item',
    category: 'GitHub Work Items',
    categorySlug: 'github-work',
    description: 'Link a work item (commit/issue) to an Idea entity.',
    parameters: [
      {
        name: 'work_item_key',
        type: 'string',
        required: true,
        description: 'Entity key of the work item (commit or issue)',
      },
      {
        name: 'idea_key',
        type: 'string',
        required: true,
        description: 'Entity key of the Idea to link to',
      },
    ],
    returns: 'Confirmation of the link.',
    examples: [
      { description: 'Link work item', code: '{"work_item_key": "ent-commit", "idea_key": "ent-idea"}' },
    ],
    relatedTools: ['create_commit_entity', 'create_issue_entity'],
  },

  // ==========================================================
  // Activity Tools
  // ==========================================================
  list_activities: {
    name: 'list_activities',
    category: 'Activity Monitoring',
    categorySlug: 'activity',
    description: 'List recent activities in the system.',
    parameters: [
      {
        name: 'limit',
        type: 'integer',
        required: false,
        description: 'Maximum activities to return',
        default: '50',
      },
      {
        name: 'agent_key',
        type: 'string',
        required: false,
        description: 'Filter by specific agent',
      },
    ],
    returns: 'List of activities with timestamps, agents, and actions.',
    examples: [
      { description: 'Recent activities', code: '{}' },
      { description: 'Agent activities', code: '{"agent_key": "swift-bold-keen-lion"}' },
    ],
    relatedTools: ['get_activity_summary'],
  },

  get_activity_summary: {
    name: 'get_activity_summary',
    category: 'Activity Monitoring',
    categorySlug: 'activity',
    description: 'Get a summary of activity for a time period.',
    parameters: [
      {
        name: 'hours',
        type: 'integer',
        required: false,
        description: 'Number of hours to summarize',
        default: '24',
      },
    ],
    returns: 'Summary with counts by activity type and agent.',
    examples: [{ description: 'Last 24 hours', code: '{}' }],
    relatedTools: ['list_activities'],
  },

  // ==========================================================
  // Session Tools
  // ==========================================================
  get_active_session: {
    name: 'get_active_session',
    category: 'Work Sessions',
    categorySlug: 'sessions',
    description: 'Check for an active work session for the current user.',
    parameters: [
      {
        name: 'project_key',
        type: 'string',
        required: false,
        description: 'Filter by specific project entity key',
      },
    ],
    returns: 'Active session details including time remaining, or message that no session is active.',
    examples: [
      { description: 'Check for active session', code: '{}' },
      { description: 'Check for project session', code: '{"project_key": "ent-project-xyz"}' },
    ],
    relatedTools: ['start_session', 'end_session', 'record_milestone'],
    whenToUse: ['Before starting a new session', 'To see time remaining on current session'],
  },

  start_session: {
    name: 'start_session',
    category: 'Work Sessions',
    categorySlug: 'sessions',
    description: 'Start a new work session for a project.',
    longDescription:
      'Creates a work session tied to a Project. Entities and messages created while session is active are automatically linked. Session auto-closes after 1 hour of inactivity.',
    parameters: [
      {
        name: 'project_key',
        type: 'string',
        required: false,
        description: 'The Project key to work on (auto-detected from git remote if identify was called)',
      },
      {
        name: 'name',
        type: 'string',
        required: false,
        description: 'Descriptive name for the session',
      },
      {
        name: 'team_key',
        type: 'string',
        required: false,
        description: 'Team scope for the session',
      },
    ],
    returns: 'Session details including session_key and auto-close time.',
    examples: [
      { description: 'Auto-detect project', code: '{}' },
      { description: 'With name', code: '{"name": "Implementing auth feature"}' },
    ],
    relatedTools: ['end_session', 'get_active_session', 'record_milestone'],
    whenToUse: ['When beginning focused work on a project', 'To track entities created during a work session'],
    tips: [
      'Record milestones during the session to track progress',
      'Sessions without milestones lose valuable tracking data',
    ],
  },

  end_session: {
    name: 'end_session',
    category: 'Work Sessions',
    categorySlug: 'sessions',
    description: 'End (close) a work session.',
    parameters: [
      {
        name: 'session_key',
        type: 'string',
        required: false,
        description: 'Specific session to close (defaults to active session)',
      },
      {
        name: 'summary',
        type: 'string',
        required: false,
        description: 'Summary of work done in the session',
      },
    ],
    returns: 'Closed session details including duration.',
    examples: [
      {
        description: 'End with summary',
        code: '{"summary": "Implemented project management system with team associations"}',
      },
    ],
    relatedTools: ['start_session', 'get_active_session'],
    tips: [
      'Write a thoughtful summary capturing what was accomplished',
      "Don't just list milestone names - synthesize the work",
    ],
  },

  extend_session: {
    name: 'extend_session',
    category: 'Work Sessions',
    categorySlug: 'sessions',
    description: 'Extend the auto-close timer for a work session.',
    parameters: [
      {
        name: 'session_key',
        type: 'string',
        required: false,
        description: 'Specific session to extend (defaults to active session)',
      },
      {
        name: 'hours',
        type: 'number',
        required: false,
        description: 'Hours to extend (max 8.0)',
        default: '1.0',
      },
    ],
    returns: 'Updated session with new auto-close time.',
    examples: [
      { description: 'Extend by 1 hour', code: '{}' },
      { description: 'Extend by 2 hours', code: '{"hours": 2}' },
    ],
    relatedTools: ['start_session', 'get_active_session'],
    whenToUse: ['When you need more time to complete work', 'To prevent the session from auto-closing'],
  },

  update_session: {
    name: 'update_session',
    category: 'Work Sessions',
    categorySlug: 'sessions',
    description: "Update a work session's name or summary.",
    parameters: [
      {
        name: 'session_key',
        type: 'string',
        required: false,
        description: 'Specific session to update (defaults to active session)',
      },
      {
        name: 'name',
        type: 'string',
        required: false,
        description: 'New name for the session',
      },
      {
        name: 'summary',
        type: 'string',
        required: false,
        description: 'Summary or notes about the session',
      },
    ],
    returns: 'Updated session details.',
    examples: [{ description: 'Name the session', code: '{"name": "Implementing authentication system"}' }],
    relatedTools: ['start_session', 'end_session'],
    whenToUse: [
      'To name an unnamed session',
      'When work focus has evolved and the session name should reflect that',
    ],
  },

  // ==========================================================
  // Milestone Tools
  // ==========================================================
  record_milestone: {
    name: 'record_milestone',
    category: 'Milestones',
    categorySlug: 'milestones',
    description: 'Record a milestone during a work session.',
    longDescription:
      "Creates or updates a Milestone entity linked to the current work session. When starting, creates a new milestone. When completing, updates the existing 'started' milestone.",
    parameters: [
      {
        name: 'name',
        type: 'string',
        required: true,
        description: 'Name/description of the milestone',
      },
      {
        name: 'status',
        type: 'string',
        required: false,
        description: "Milestone status: 'started', 'completed', or 'blocked'",
        default: 'completed',
        enum: ['started', 'completed', 'blocked'],
      },
      {
        name: 'goal',
        type: 'string',
        required: false,
        description: 'What this milestone aims to achieve (markdown supported)',
      },
      {
        name: 'outcome',
        type: 'string',
        required: false,
        description: 'The concrete result of the work (markdown supported)',
      },
      {
        name: 'summary',
        type: 'string',
        required: false,
        description: 'Narrative of collaboration, key decisions (markdown supported)',
      },
      {
        name: 'files_touched',
        type: 'integer',
        required: false,
        description: 'Number of files touched',
      },
      {
        name: 'lines_added',
        type: 'integer',
        required: false,
        description: 'Lines of code added',
      },
      {
        name: 'lines_removed',
        type: 'integer',
        required: false,
        description: 'Lines of code removed',
      },
      {
        name: 'human_guidance_level',
        type: 'integer',
        required: false,
        description: '1=fully autonomous, 5=heavy guidance (1-5 scale)',
      },
      {
        name: 'complexity_rating',
        type: 'integer',
        required: false,
        description: '1=trivial, 5=very complex (1-5 scale)',
      },
    ],
    returns: 'Created Milestone entity details with metrics recorded.',
    examples: [
      {
        description: 'Start a milestone',
        code: '{"name": "Implementing authentication", "status": "started", "goal": "Add JWT-based auth"}',
      },
      {
        description: 'Complete a milestone',
        code: '{"name": "Auth complete", "status": "completed", "outcome": "Added /auth/login endpoint", "lines_added": 150}',
      },
    ],
    relatedTools: ['start_session', 'update_milestone'],
    whenToUse: [
      'When starting a major task',
      'When completing a feature, bug fix, or refactor',
      'When hitting a blocker',
      'Before making a git commit',
    ],
    tips: [
      'Always record milestones to track AI agent contributions',
      'Include self-assessment metrics for analytics',
      'Use markdown in goal, outcome, and summary fields',
    ],
  },

  update_milestone: {
    name: 'update_milestone',
    category: 'Milestones',
    categorySlug: 'milestones',
    description: 'Update metrics on the current active milestone.',
    parameters: [
      {
        name: 'milestone_key',
        type: 'string',
        required: false,
        description: 'Specific milestone to update (defaults to current active)',
      },
      {
        name: 'files_touched',
        type: 'integer',
        required: false,
        description: 'Number of files touched so far',
      },
      {
        name: 'lines_added',
        type: 'integer',
        required: false,
        description: 'Lines of code added so far',
      },
      {
        name: 'lines_removed',
        type: 'integer',
        required: false,
        description: 'Lines of code removed so far',
      },
      {
        name: 'commits_made',
        type: 'integer',
        required: false,
        description: 'Number of commits made so far',
      },
      {
        name: 'complexity_rating',
        type: 'integer',
        required: false,
        description: '1=trivial, 5=very complex (1-5 scale)',
      },
    ],
    returns: 'Updated milestone with current metrics.',
    examples: [
      { description: 'Update progress', code: '{"files_touched": 5, "lines_added": 120}' },
    ],
    relatedTools: ['record_milestone'],
    whenToUse: [
      'To track progress incrementally during an active milestone',
      'To update metrics without completing the milestone',
    ],
  },
};

// Helper function to get tools by category
export function getToolsByCategory(categorySlug: string): ToolDoc[] {
  return Object.values(TOOL_DOCS).filter((tool) => tool.categorySlug === categorySlug);
}

// Helper function to get a tool by name
export function getToolByName(name: string): ToolDoc | undefined {
  return TOOL_DOCS[name];
}

// Helper function to search tools
export function searchTools(query: string): ToolDoc[] {
  const lowerQuery = query.toLowerCase();
  return Object.values(TOOL_DOCS).filter(
    (tool) =>
      tool.name.toLowerCase().includes(lowerQuery) ||
      tool.description.toLowerCase().includes(lowerQuery) ||
      tool.category.toLowerCase().includes(lowerQuery)
  );
}

// Get all tool names
export function getAllToolNames(): string[] {
  return Object.keys(TOOL_DOCS);
}

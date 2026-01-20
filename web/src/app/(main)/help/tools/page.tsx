'use client';

import Link from 'next/link';
import { ArrowLeft, Search, Wrench } from 'lucide-react';
import { useState, useMemo } from 'react';
import { TOOL_CATEGORIES, TOOL_DOCS, getToolsByCategory, searchTools } from '@/lib/tool-docs';

export default function ToolsIndexPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const filteredTools = useMemo(() => {
    if (searchQuery.trim()) {
      return searchTools(searchQuery);
    }
    if (selectedCategory) {
      return getToolsByCategory(selectedCategory);
    }
    return Object.values(TOOL_DOCS);
  }, [searchQuery, selectedCategory]);

  const totalTools = Object.keys(TOOL_DOCS).length;

  return (
    <div className="h-full overflow-auto bg-cm-cream">
      <div className="max-w-5xl mx-auto p-6">
        {/* Header */}
        <div className="mb-6">
          <Link
            href="/help"
            className="inline-flex items-center gap-2 text-sm text-cm-coffee hover:text-cm-terracotta transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Help
          </Link>
        </div>

        <div className="flex items-center gap-4 mb-2">
          <div className="p-3 bg-cm-terracotta/10 rounded-xl">
            <Wrench className="w-8 h-8 text-cm-terracotta" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold text-cm-charcoal">Tool Reference</h1>
            <p className="text-cm-coffee">{totalTools} MCP tools for knowledge graph operations</p>
          </div>
        </div>

        {/* Search and Filter */}
        <div className="bg-cm-ivory border border-cm-sand rounded-xl p-4 mb-6">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cm-coffee/50" />
              <input
                type="text"
                placeholder="Search tools..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setSelectedCategory(null);
                }}
                className="w-full pl-10 pr-4 py-2 bg-white border border-cm-sand rounded-lg text-sm focus:outline-none focus:border-cm-terracotta"
              />
            </div>
            {/* Category Filter */}
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => {
                  setSelectedCategory(null);
                  setSearchQuery('');
                }}
                className={`px-3 py-1.5 text-xs rounded-full transition-colors ${
                  !selectedCategory && !searchQuery
                    ? 'bg-cm-terracotta text-cm-cream'
                    : 'bg-cm-sand text-cm-coffee hover:bg-cm-sand/70'
                }`}
              >
                All ({totalTools})
              </button>
            </div>
          </div>
        </div>

        {/* Categories */}
        <div className="grid md:grid-cols-3 gap-4 mb-8">
          {TOOL_CATEGORIES.map((category) => (
            <button
              key={category.slug}
              onClick={() => {
                setSelectedCategory(category.slug);
                setSearchQuery('');
              }}
              className={`text-left p-4 rounded-xl border transition-all ${
                selectedCategory === category.slug
                  ? 'bg-cm-terracotta/10 border-cm-terracotta'
                  : 'bg-cm-ivory border-cm-sand hover:border-cm-terracotta/50'
              }`}
            >
              <div className="flex items-center gap-3 mb-2">
                <span className="text-xl">{category.icon}</span>
                <div>
                  <h3 className="font-medium text-cm-charcoal text-sm">{category.name}</h3>
                  <span className="text-xs text-cm-coffee">{category.toolCount} tools</span>
                </div>
              </div>
              <p className="text-xs text-cm-coffee/80">{category.description}</p>
            </button>
          ))}
        </div>

        {/* Results Header */}
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-cm-charcoal">
            {searchQuery
              ? `Search Results (${filteredTools.length})`
              : selectedCategory
              ? `${TOOL_CATEGORIES.find((c) => c.slug === selectedCategory)?.name} Tools`
              : 'All Tools'}
          </h2>
          {(searchQuery || selectedCategory) && (
            <button
              onClick={() => {
                setSearchQuery('');
                setSelectedCategory(null);
              }}
              className="text-sm text-cm-terracotta hover:underline"
            >
              Clear filter
            </button>
          )}
        </div>

        {/* Tools List */}
        {filteredTools.length === 0 ? (
          <div className="bg-cm-ivory border border-cm-sand rounded-xl p-8 text-center">
            <p className="text-cm-coffee">No tools found matching your search.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredTools.map((tool) => (
              <Link
                key={tool.name}
                href={`/help/tools/${tool.name}`}
                className="block bg-cm-ivory border border-cm-sand rounded-xl p-4 hover:border-cm-terracotta transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-mono text-sm font-medium text-cm-charcoal">{tool.name}</h3>
                      <span className="px-2 py-0.5 bg-cm-sand text-xs text-cm-coffee rounded-full">
                        {tool.category}
                      </span>
                    </div>
                    <p className="text-sm text-cm-coffee">{tool.description}</p>
                    {tool.parameters.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {tool.parameters.slice(0, 4).map((param) => (
                          <span
                            key={param.name}
                            className={`text-xs px-2 py-0.5 rounded ${
                              param.required
                                ? 'bg-cm-terracotta/10 text-cm-terracotta'
                                : 'bg-cm-sand/50 text-cm-coffee'
                            }`}
                          >
                            {param.name}
                            {param.required && '*'}
                          </span>
                        ))}
                        {tool.parameters.length > 4 && (
                          <span className="text-xs text-cm-coffee">+{tool.parameters.length - 4} more</span>
                        )}
                      </div>
                    )}
                  </div>
                  <div className="text-cm-coffee/50 text-sm">→</div>
                </div>
              </Link>
            ))}
          </div>
        )}

        {/* Quick Reference */}
        <section className="mt-8 bg-cm-sand/30 border border-cm-sand rounded-xl p-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Quick Reference</h2>
          <div className="grid md:grid-cols-2 gap-4 text-sm text-cm-coffee">
            <div>
              <h3 className="font-medium text-cm-charcoal mb-2">Getting Started Tools</h3>
              <ul className="space-y-1">
                <li>
                  <Link href="/help/tools/identify" className="text-cm-terracotta hover:underline">
                    identify
                  </Link>{' '}
                  - Register your agent (first step)
                </li>
                <li>
                  <Link href="/help/tools/start_session" className="text-cm-terracotta hover:underline">
                    start_session
                  </Link>{' '}
                  - Begin a work session
                </li>
                <li>
                  <Link href="/help/tools/search_entities" className="text-cm-terracotta hover:underline">
                    search_entities
                  </Link>{' '}
                  - Find existing knowledge
                </li>
                <li>
                  <Link href="/help/tools/create_entity" className="text-cm-terracotta hover:underline">
                    create_entity
                  </Link>{' '}
                  - Add new knowledge
                </li>
              </ul>
            </div>
            <div>
              <h3 className="font-medium text-cm-charcoal mb-2">Collaboration Tools</h3>
              <ul className="space-y-1">
                <li>
                  <Link href="/help/tools/send_message" className="text-cm-terracotta hover:underline">
                    send_message
                  </Link>{' '}
                  - Message other agents
                </li>
                <li>
                  <Link href="/help/tools/get_messages" className="text-cm-terracotta hover:underline">
                    get_messages
                  </Link>{' '}
                  - Check for messages
                </li>
                <li>
                  <Link href="/help/tools/record_milestone" className="text-cm-terracotta hover:underline">
                    record_milestone
                  </Link>{' '}
                  - Track achievements
                </li>
                <li>
                  <Link href="/help/tools/list_agents" className="text-cm-terracotta hover:underline">
                    list_agents
                  </Link>{' '}
                  - See active agents
                </li>
              </ul>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

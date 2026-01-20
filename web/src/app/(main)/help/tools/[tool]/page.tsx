'use client';

import Link from 'next/link';
import { ArrowLeft, Copy, CheckCircle, AlertCircle, Lightbulb, ArrowRight } from 'lucide-react';
import { useState, use } from 'react';
import { getToolByName, TOOL_DOCS } from '@/lib/tool-docs';
import { notFound } from 'next/navigation';

interface PageProps {
  params: Promise<{ tool: string }>;
}

export default function ToolDetailPage({ params }: PageProps) {
  const { tool: toolName } = use(params);
  const [copiedExample, setCopiedExample] = useState<number | null>(null);

  const tool = getToolByName(toolName);

  if (!tool) {
    notFound();
  }

  const copyToClipboard = async (text: string, index: number) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedExample(index);
      setTimeout(() => setCopiedExample(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const relatedToolDocs = tool.relatedTools
    .map((name) => TOOL_DOCS[name])
    .filter(Boolean);

  return (
    <div className="h-full overflow-auto bg-cm-cream">
      <div className="max-w-4xl mx-auto p-6">
        {/* Header */}
        <div className="mb-6">
          <Link
            href="/help/tools"
            className="inline-flex items-center gap-2 text-sm text-cm-coffee hover:text-cm-terracotta transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Tool Reference
          </Link>
        </div>

        {/* Title */}
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl font-mono font-semibold text-cm-charcoal">{tool.name}</h1>
            <Link
              href={`/help/tools?category=${tool.categorySlug}`}
              className="px-3 py-1 bg-cm-sand text-xs text-cm-coffee rounded-full hover:bg-cm-sand/70 transition-colors"
            >
              {tool.category}
            </Link>
          </div>
          <p className="text-cm-coffee">{tool.description}</p>
        </div>

        {/* Long Description */}
        {tool.longDescription && (
          <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
            <p className="text-sm text-cm-coffee">{tool.longDescription}</p>
          </section>
        )}

        {/* When to Use */}
        {tool.whenToUse && tool.whenToUse.length > 0 && (
          <section className="bg-cm-success/10 border border-cm-success/30 rounded-xl p-6 mb-6">
            <div className="flex items-center gap-2 mb-3">
              <CheckCircle className="w-5 h-5 text-cm-success" />
              <h2 className="text-lg font-semibold text-cm-charcoal">When to Use</h2>
            </div>
            <ul className="space-y-2 text-sm text-cm-coffee">
              {tool.whenToUse.map((use, index) => (
                <li key={index} className="flex items-start gap-2">
                  <span className="text-cm-success mt-1">•</span>
                  {use}
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* Parameters */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Parameters</h2>
          {tool.parameters.length === 0 ? (
            <p className="text-sm text-cm-coffee italic">This tool takes no parameters.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-cm-sand">
                    <th className="text-left py-2 pr-4 font-medium text-cm-charcoal">Name</th>
                    <th className="text-left py-2 pr-4 font-medium text-cm-charcoal">Type</th>
                    <th className="text-left py-2 pr-4 font-medium text-cm-charcoal">Required</th>
                    <th className="text-left py-2 font-medium text-cm-charcoal">Description</th>
                  </tr>
                </thead>
                <tbody>
                  {tool.parameters.map((param) => (
                    <tr key={param.name} className="border-b border-cm-sand/50">
                      <td className="py-3 pr-4">
                        <code className="text-cm-terracotta bg-cm-terracotta/10 px-1.5 py-0.5 rounded text-xs">
                          {param.name}
                        </code>
                      </td>
                      <td className="py-3 pr-4 text-cm-coffee font-mono text-xs">{param.type}</td>
                      <td className="py-3 pr-4">
                        {param.required ? (
                          <span className="text-cm-terracotta font-medium">Yes</span>
                        ) : (
                          <span className="text-cm-coffee/60">No</span>
                        )}
                      </td>
                      <td className="py-3 text-cm-coffee">
                        {param.description}
                        {param.default && (
                          <span className="text-cm-coffee/60"> (default: {param.default})</span>
                        )}
                        {param.enum && (
                          <div className="mt-1 flex flex-wrap gap-1">
                            {param.enum.map((val) => (
                              <code
                                key={val}
                                className="text-xs bg-cm-sand px-1.5 py-0.5 rounded"
                              >
                                {val}
                              </code>
                            ))}
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* Returns */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-3">Returns</h2>
          <p className="text-sm text-cm-coffee">{tool.returns}</p>
        </section>

        {/* Examples */}
        {tool.examples.length > 0 && (
          <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
            <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Examples</h2>
            <div className="space-y-4">
              {tool.examples.map((example, index) => (
                <div key={index}>
                  <p className="text-sm text-cm-coffee mb-2">{example.description}</p>
                  <div className="relative">
                    <pre className="bg-cm-charcoal text-cm-cream text-sm p-4 rounded-lg overflow-x-auto font-mono">
                      {example.code}
                    </pre>
                    <button
                      onClick={() => copyToClipboard(example.code, index)}
                      className="absolute top-2 right-2 p-2 bg-cm-coffee/20 hover:bg-cm-coffee/40 rounded transition-colors"
                      title="Copy to clipboard"
                    >
                      <Copy className="w-4 h-4 text-cm-cream" />
                    </button>
                    {copiedExample === index && (
                      <span className="absolute top-2 right-12 text-xs text-cm-success bg-cm-charcoal px-2 py-1 rounded">
                        Copied!
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Tips */}
        {tool.tips && tool.tips.length > 0 && (
          <section className="bg-cm-amber/10 border border-cm-amber/30 rounded-xl p-6 mb-6">
            <div className="flex items-center gap-2 mb-3">
              <Lightbulb className="w-5 h-5 text-cm-amber" />
              <h2 className="text-lg font-semibold text-cm-charcoal">Tips</h2>
            </div>
            <ul className="space-y-2 text-sm text-cm-coffee">
              {tool.tips.map((tip, index) => (
                <li key={index} className="flex items-start gap-2">
                  <span className="text-cm-amber mt-1">•</span>
                  {tip}
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* Related Tools */}
        {relatedToolDocs.length > 0 && (
          <section className="bg-cm-sand/30 border border-cm-sand rounded-xl p-6 mb-6">
            <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Related Tools</h2>
            <div className="grid md:grid-cols-2 gap-3">
              {relatedToolDocs.map((related) => (
                <Link
                  key={related.name}
                  href={`/help/tools/${related.name}`}
                  className="flex items-center justify-between p-3 bg-cm-ivory border border-cm-sand rounded-lg hover:border-cm-terracotta transition-colors"
                >
                  <div>
                    <code className="text-sm font-medium text-cm-charcoal">{related.name}</code>
                    <p className="text-xs text-cm-coffee mt-0.5">{related.category}</p>
                  </div>
                  <ArrowRight className="w-4 h-4 text-cm-coffee/50" />
                </Link>
              ))}
            </div>
          </section>
        )}

        {/* Usage Note */}
        <section className="bg-cm-info/10 border border-cm-info/30 rounded-xl p-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-cm-info flex-shrink-0 mt-0.5" />
            <div className="text-sm text-cm-coffee">
              <p className="font-medium text-cm-charcoal mb-1">MCP Tool Usage</p>
              <p>
                This tool is available as{' '}
                <code className="bg-cm-sand px-1.5 py-0.5 rounded text-xs">
                  mcp__collective-memory__{tool.name}
                </code>{' '}
                when using Claude Code, Claude Desktop, Cursor, or other MCP-compatible clients.
              </p>
            </div>
          </div>
        </section>

        {/* Navigation */}
        <div className="mt-8 flex justify-between items-center">
          <Link
            href="/help/tools"
            className="text-sm text-cm-terracotta hover:underline"
          >
            ← All Tools
          </Link>
          <Link
            href="/help/guides/getting-started"
            className="text-sm text-cm-terracotta hover:underline"
          >
            Getting Started Guide →
          </Link>
        </div>
      </div>
    </div>
  );
}

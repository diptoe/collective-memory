'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/stores/auth-store';
import { Domain } from '@/types';

interface TableStats {
  table_name: string;
  row_count: number;
  has_domain_key: boolean;
  domain_filtered_count: number | null;
}

interface DatabaseHealth {
  status: 'healthy' | 'unhealthy';
  database: string;
  user: string;
  version: string;
  size: string;
  error?: string;
}

interface ConsistencyIssue {
  entity_key?: string;
  project_key?: string;
  team_key?: string;
  user_key?: string;
  email?: string;
  display_name?: string;
  name: string;
  issue_type: string;
  current_scope_type?: string | null;
  current_scope_key?: string | null;
  expected_scope_type?: string | null;
  expected_scope_key?: string | null;
  work_session_key?: string;
  description?: string;
  current_type?: string;
  expected_type?: string;
  current_entity_key?: string;
  expected_entity_key?: string;
}

interface ConsistencyData {
  issues: {
    milestones: ConsistencyIssue[];
    projects: ConsistencyIssue[];
    teams: ConsistencyIssue[];
    users: ConsistencyIssue[];
    summary: {
      milestone_scope_issues: number;
      milestone_relationship_issues: number;
      project_entity_issues: number;
      team_entity_issues: number;
      user_entity_issues: number;
    };
  };
  total_issues: number;
  domain_key: string | null;
}

export default function DatabaseAdminPage() {
  const router = useRouter();
  const { user: currentUser, isAuthenticated } = useAuthStore();
  const [tables, setTables] = useState<TableStats[]>([]);
  const [health, setHealth] = useState<DatabaseHealth | null>(null);
  const [domains, setDomains] = useState<Domain[]>([]);
  const [selectedDomain, setSelectedDomain] = useState<string>('');
  const [totalRows, setTotalRows] = useState(0);
  const [totalDomainRows, setTotalDomainRows] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Consistency check state
  const [consistencyData, setConsistencyData] = useState<ConsistencyData | null>(null);
  const [isCheckingConsistency, setIsCheckingConsistency] = useState(false);
  const [isFixing, setIsFixing] = useState(false);
  const [fixResult, setFixResult] = useState<{ fixed: number; errors: number; dryRun: boolean } | null>(null);

  const isAdmin = currentUser?.role === 'admin';
  const isDomainAdmin = currentUser?.role === 'domain_admin';

  // Redirect if not admin
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    } else if (!isAdmin && !isDomainAdmin) {
      router.push('/');
    }
  }, [isAuthenticated, currentUser, router, isAdmin, isDomainAdmin]);

  // Load data
  useEffect(() => {
    if (isAdmin || isDomainAdmin) {
      loadData();
    }
  }, [currentUser, selectedDomain]);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const promises: Promise<any>[] = [
        api.database.stats(selectedDomain || undefined),
        api.database.health(),
      ];

      // Only system admins can list domains
      if (isAdmin && domains.length === 0) {
        promises.push(api.domains.list());
      }

      const results = await Promise.all(promises);
      const [statsResponse, healthResponse] = results;

      if (statsResponse.success && statsResponse.data) {
        setTables(statsResponse.data.tables);
        setTotalRows(statsResponse.data.total_rows);
        setTotalDomainRows(statsResponse.data.total_domain_rows);
      }

      if (healthResponse.success && healthResponse.data) {
        setHealth(healthResponse.data);
      }

      if (results[2]?.success && results[2]?.data) {
        setDomains(results[2].data.domains);
      }
    } catch (err: any) {
      setError(err.response?.data?.msg || 'Failed to load database statistics');
    } finally {
      setIsLoading(false);
    }
  };

  const checkConsistency = async () => {
    setIsCheckingConsistency(true);
    setFixResult(null);
    try {
      const response = await api.database.consistency(selectedDomain || undefined);
      if (response.success && response.data) {
        // Ensure backward compatibility with API responses that might not include users
        const data = response.data as ConsistencyData;
        if (!data.issues.users) {
          data.issues.users = [];
        }
        if (data.issues.summary.user_entity_issues === undefined) {
          data.issues.summary.user_entity_issues = 0;
        }
        setConsistencyData(data);
      }
    } catch (err: any) {
      setError(err.response?.data?.msg || 'Failed to check consistency');
    } finally {
      setIsCheckingConsistency(false);
    }
  };

  const fixConsistency = async (dryRun: boolean) => {
    if (!consistencyData) return;

    setIsFixing(true);
    setFixResult(null);
    try {
      const fixTypes: string[] = [];
      if (consistencyData.issues.summary.milestone_scope_issues > 0) {
        fixTypes.push('milestone_scopes');
      }
      if (consistencyData.issues.summary.milestone_relationship_issues > 0) {
        fixTypes.push('milestone_relationships');
      }
      if (consistencyData.issues.summary.project_entity_issues > 0) {
        fixTypes.push('project_entities');
      }
      if (consistencyData.issues.summary.team_entity_issues > 0) {
        fixTypes.push('team_entities');
      }
      if (consistencyData.issues.summary.user_entity_issues > 0) {
        fixTypes.push('user_entities');
      }

      if (fixTypes.length === 0) {
        setFixResult({ fixed: 0, errors: 0, dryRun });
        return;
      }

      const response = await api.database.fixConsistency(
        fixTypes,
        selectedDomain || undefined,
        dryRun
      );

      if (response.success && response.data) {
        setFixResult({
          fixed: response.data.fixed.length,
          errors: response.data.errors.length,
          dryRun: response.data.dry_run,
        });

        // Refresh consistency data if we actually fixed things
        if (!dryRun && response.data.fixed.length > 0) {
          await checkConsistency();
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.msg || 'Failed to fix consistency');
    } finally {
      setIsFixing(false);
    }
  };

  if (!isAuthenticated || (!isAdmin && !isDomainAdmin)) {
    return null;
  }

  // Separate tables with and without domain_key
  const domainTables = tables.filter(t => t.has_domain_key);
  const globalTables = tables.filter(t => !t.has_domain_key);

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-cm-charcoal">Database</h1>
          <p className="text-sm text-cm-coffee mt-1">
            {isAdmin ? 'System-wide database statistics' : 'Domain database statistics'}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/admin/settings"
            className="px-4 py-2 text-cm-coffee hover:text-cm-charcoal transition-colors text-sm"
          >
            Settings
          </Link>
          <button
            onClick={loadData}
            disabled={isLoading}
            className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-md text-sm font-medium hover:bg-cm-terracotta/90 transition-colors disabled:opacity-50"
          >
            {isLoading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Health Status */}
      {health && (
        <div className="mb-6 bg-cm-ivory border border-cm-sand rounded-lg p-4">
          <div className="flex items-center gap-3 mb-3">
            <div className={`w-3 h-3 rounded-full ${health.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'}`} />
            <h2 className="text-sm font-medium text-cm-charcoal">
              Database {health.status === 'healthy' ? 'Healthy' : 'Unhealthy'}
            </h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-cm-coffee">Database</p>
              <p className="font-medium text-cm-charcoal">{health.database}</p>
            </div>
            <div>
              <p className="text-cm-coffee">Size</p>
              <p className="font-medium text-cm-charcoal">{health.size}</p>
            </div>
            <div>
              <p className="text-cm-coffee">User</p>
              <p className="font-medium text-cm-charcoal">{health.user}</p>
            </div>
            <div>
              <p className="text-cm-coffee">Version</p>
              <p className="font-medium text-cm-charcoal truncate" title={health.version}>
                {health.version?.split(' ').slice(0, 2).join(' ')}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <StatCard label="Total Tables" value={tables.length} />
        <StatCard label="Total Rows" value={totalRows.toLocaleString()} />
        <StatCard
          label="Domain-Scoped Tables"
          value={domainTables.length}
          subtitle={`of ${tables.length}`}
        />
        {totalDomainRows !== null && (
          <StatCard
            label="Domain Rows"
            value={totalDomainRows.toLocaleString()}
            color="blue"
          />
        )}
      </div>

      {/* Domain Filter (system admin only) */}
      {isAdmin && domains.length > 0 && (
        <div className="mb-6">
          <label className="block text-sm font-medium text-cm-charcoal mb-2">
            Filter by Domain
          </label>
          <select
            value={selectedDomain}
            onChange={(e) => setSelectedDomain(e.target.value)}
            className="px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal text-sm focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
          >
            <option value="">All domains (entire database)</option>
            {domains.map((domain) => (
              <option key={domain.domain_key} value={domain.domain_key}>
                {domain.name}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Domain-Scoped Tables */}
      <div className="mb-8">
        <h2 className="text-lg font-medium text-cm-charcoal mb-4 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-blue-500" />
          Domain-Scoped Tables
          <span className="text-sm font-normal text-cm-coffee">
            (filtered by domain_key)
          </span>
        </h2>
        <div className="bg-cm-ivory border border-cm-sand rounded-lg overflow-hidden">
          <table className="w-full">
            <thead className="bg-cm-sand/50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Table</th>
                <th className="px-4 py-3 text-right text-sm font-medium text-cm-charcoal">Total Rows</th>
                {(selectedDomain || isDomainAdmin) && (
                  <th className="px-4 py-3 text-right text-sm font-medium text-cm-charcoal">Domain Rows</th>
                )}
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={3} className="px-4 py-8 text-center text-sm text-cm-coffee">
                    Loading...
                  </td>
                </tr>
              ) : domainTables.length === 0 ? (
                <tr>
                  <td colSpan={3} className="px-4 py-8 text-center text-sm text-cm-coffee">
                    No domain-scoped tables found
                  </td>
                </tr>
              ) : (
                domainTables.map((table) => (
                  <tr key={table.table_name} className="border-t border-cm-sand hover:bg-cm-cream/50">
                    <td className="px-4 py-3 text-sm font-mono text-cm-charcoal">
                      {table.table_name}
                    </td>
                    <td className="px-4 py-3 text-sm text-cm-coffee text-right">
                      {table.row_count >= 0 ? table.row_count.toLocaleString() : 'Error'}
                    </td>
                    {(selectedDomain || isDomainAdmin) && (
                      <td className="px-4 py-3 text-sm text-right">
                        {table.domain_filtered_count !== null ? (
                          <span className={table.domain_filtered_count > 0 ? 'text-blue-600 font-medium' : 'text-cm-coffee'}>
                            {table.domain_filtered_count >= 0 ? table.domain_filtered_count.toLocaleString() : 'Error'}
                          </span>
                        ) : (
                          <span className="text-cm-sand">-</span>
                        )}
                      </td>
                    )}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Global Tables (system admin only) */}
      {isAdmin && (
        <div>
          <h2 className="text-lg font-medium text-cm-charcoal mb-4 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-gray-400" />
            Global Tables
            <span className="text-sm font-normal text-cm-coffee">
              (no domain filtering)
            </span>
          </h2>
          <div className="bg-cm-ivory border border-cm-sand rounded-lg overflow-hidden">
            <table className="w-full">
              <thead className="bg-cm-sand/50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Table</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-cm-charcoal">Total Rows</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr>
                    <td colSpan={2} className="px-4 py-8 text-center text-sm text-cm-coffee">
                      Loading...
                    </td>
                  </tr>
                ) : globalTables.length === 0 ? (
                  <tr>
                    <td colSpan={2} className="px-4 py-8 text-center text-sm text-cm-coffee">
                      No global tables found
                    </td>
                  </tr>
                ) : (
                  globalTables.map((table) => (
                    <tr key={table.table_name} className="border-t border-cm-sand hover:bg-cm-cream/50">
                      <td className="px-4 py-3 text-sm font-mono text-cm-charcoal">
                        {table.table_name}
                      </td>
                      <td className="px-4 py-3 text-sm text-cm-coffee text-right">
                        {table.row_count >= 0 ? table.row_count.toLocaleString() : 'Error'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Entity Consistency Check */}
      <div className="mt-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-medium text-cm-charcoal flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-cm-terracotta" />
              Entity Consistency
            </h2>
            <p className="text-sm text-cm-coffee mt-1">
              Check and fix data integrity issues
            </p>
          </div>
          <button
            onClick={checkConsistency}
            disabled={isCheckingConsistency}
            className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-md text-sm font-medium hover:bg-cm-terracotta/90 transition-colors disabled:opacity-50"
          >
            {isCheckingConsistency ? 'Checking...' : 'Check Consistency'}
          </button>
        </div>

        {fixResult && (
          <div className={`mb-4 p-3 rounded-lg text-sm ${
            fixResult.dryRun
              ? 'bg-blue-50 border border-blue-200 text-blue-700'
              : fixResult.errors > 0
                ? 'bg-yellow-50 border border-yellow-200 text-yellow-700'
                : 'bg-green-50 border border-green-200 text-green-700'
          }`}>
            {fixResult.dryRun
              ? `Dry run: Would fix ${fixResult.fixed} issues`
              : `Fixed ${fixResult.fixed} issues${fixResult.errors > 0 ? ` with ${fixResult.errors} errors` : ''}`}
          </div>
        )}

        {consistencyData && (
          <div className="bg-cm-ivory border border-cm-sand rounded-lg p-4">
            {/* Summary */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
              <div className="text-center">
                <p className="text-2xl font-semibold text-cm-charcoal">
                  {consistencyData.total_issues}
                </p>
                <p className="text-xs text-cm-coffee">Total Issues</p>
              </div>
              <div className="text-center">
                <p className={`text-2xl font-semibold ${consistencyData.issues.summary.milestone_scope_issues > 0 ? 'text-red-600' : 'text-green-600'}`}>
                  {consistencyData.issues.summary.milestone_scope_issues}
                </p>
                <p className="text-xs text-cm-coffee">Milestone Scopes</p>
              </div>
              <div className="text-center">
                <p className={`text-2xl font-semibold ${consistencyData.issues.summary.milestone_relationship_issues > 0 ? 'text-red-600' : 'text-green-600'}`}>
                  {consistencyData.issues.summary.milestone_relationship_issues}
                </p>
                <p className="text-xs text-cm-coffee">Milestone Rels</p>
              </div>
              <div className="text-center">
                <p className={`text-2xl font-semibold ${consistencyData.issues.summary.project_entity_issues > 0 ? 'text-red-600' : 'text-green-600'}`}>
                  {consistencyData.issues.summary.project_entity_issues}
                </p>
                <p className="text-xs text-cm-coffee">Project Entities</p>
              </div>
              <div className="text-center">
                <p className={`text-2xl font-semibold ${consistencyData.issues.summary.team_entity_issues > 0 ? 'text-red-600' : 'text-green-600'}`}>
                  {consistencyData.issues.summary.team_entity_issues}
                </p>
                <p className="text-xs text-cm-coffee">Team Entities</p>
              </div>
              <div className="text-center">
                <p className={`text-2xl font-semibold ${consistencyData.issues.summary.user_entity_issues > 0 ? 'text-red-600' : 'text-green-600'}`}>
                  {consistencyData.issues.summary.user_entity_issues}
                </p>
                <p className="text-xs text-cm-coffee">User Entities</p>
              </div>
            </div>

            {consistencyData.total_issues > 0 ? (
              <>
                {/* Issue Lists */}
                {consistencyData.issues.milestones.filter(i => i.issue_type === 'scope_mismatch').length > 0 && (
                  <div className="mb-4">
                    <h3 className="text-sm font-medium text-cm-charcoal mb-2">Milestone Scope Issues</h3>
                    <div className="space-y-2 max-h-40 overflow-y-auto">
                      {consistencyData.issues.milestones
                        .filter(i => i.issue_type === 'scope_mismatch')
                        .slice(0, 10)
                        .map((issue, idx) => (
                        <div key={idx} className="text-xs p-2 bg-cm-sand/30 rounded">
                          <span className="font-medium">{issue.name}</span>
                          <span className="text-cm-coffee ml-2">
                            {issue.current_scope_type || 'none'} → {issue.expected_scope_type || 'none'}
                          </span>
                        </div>
                      ))}
                      {consistencyData.issues.milestones.filter(i => i.issue_type === 'scope_mismatch').length > 10 && (
                        <p className="text-xs text-cm-coffee">
                          ... and {consistencyData.issues.milestones.filter(i => i.issue_type === 'scope_mismatch').length - 10} more
                        </p>
                      )}
                    </div>
                  </div>
                )}

                {consistencyData.issues.milestones.filter(i => i.issue_type === 'missing_relationship').length > 0 && (
                  <div className="mb-4">
                    <h3 className="text-sm font-medium text-cm-charcoal mb-2">Milestone Relationship Issues</h3>
                    <div className="space-y-2 max-h-40 overflow-y-auto">
                      {consistencyData.issues.milestones
                        .filter(i => i.issue_type === 'missing_relationship')
                        .slice(0, 10)
                        .map((issue, idx) => (
                        <div key={idx} className="text-xs p-2 bg-cm-sand/30 rounded">
                          <span className="font-medium">{issue.name}</span>
                          <span className="text-cm-coffee ml-2">
                            missing BELONGS_TO → {(issue as any).target_type}
                          </span>
                        </div>
                      ))}
                      {consistencyData.issues.milestones.filter(i => i.issue_type === 'missing_relationship').length > 10 && (
                        <p className="text-xs text-cm-coffee">
                          ... and {consistencyData.issues.milestones.filter(i => i.issue_type === 'missing_relationship').length - 10} more
                        </p>
                      )}
                    </div>
                  </div>
                )}

                {consistencyData.issues.projects.length > 0 && (
                  <div className="mb-4">
                    <h3 className="text-sm font-medium text-cm-charcoal mb-2">Project Entity Issues</h3>
                    <div className="space-y-2 max-h-40 overflow-y-auto">
                      {consistencyData.issues.projects.slice(0, 10).map((issue, idx) => (
                        <div key={idx} className="text-xs p-2 bg-cm-sand/30 rounded">
                          <span className="font-medium">{issue.name}</span>
                          <span className="text-cm-coffee ml-2">({issue.issue_type})</span>
                        </div>
                      ))}
                      {consistencyData.issues.projects.length > 10 && (
                        <p className="text-xs text-cm-coffee">
                          ... and {consistencyData.issues.projects.length - 10} more
                        </p>
                      )}
                    </div>
                  </div>
                )}

                {consistencyData.issues.teams.length > 0 && (
                  <div className="mb-4">
                    <h3 className="text-sm font-medium text-cm-charcoal mb-2">Team Entity Issues</h3>
                    <div className="space-y-2 max-h-40 overflow-y-auto">
                      {consistencyData.issues.teams.slice(0, 10).map((issue, idx) => (
                        <div key={idx} className="text-xs p-2 bg-cm-sand/30 rounded">
                          <span className="font-medium">{issue.name}</span>
                          <span className="text-cm-coffee ml-2">({issue.issue_type})</span>
                        </div>
                      ))}
                      {consistencyData.issues.teams.length > 10 && (
                        <p className="text-xs text-cm-coffee">
                          ... and {consistencyData.issues.teams.length - 10} more
                        </p>
                      )}
                    </div>
                  </div>
                )}

                {consistencyData.issues.users.length > 0 && (
                  <div className="mb-4">
                    <h3 className="text-sm font-medium text-cm-charcoal mb-2">User Entity Issues</h3>
                    <div className="space-y-2 max-h-40 overflow-y-auto">
                      {consistencyData.issues.users.slice(0, 10).map((issue, idx) => (
                        <div key={idx} className="text-xs p-2 bg-cm-sand/30 rounded">
                          <span className="font-medium">{issue.display_name || issue.email}</span>
                          <span className="text-cm-coffee ml-2">({issue.issue_type})</span>
                          {issue.description && (
                            <span className="text-cm-coffee ml-1">- {issue.description}</span>
                          )}
                        </div>
                      ))}
                      {consistencyData.issues.users.length > 10 && (
                        <p className="text-xs text-cm-coffee">
                          ... and {consistencyData.issues.users.length - 10} more
                        </p>
                      )}
                    </div>
                  </div>
                )}

                {/* Fix Buttons */}
                <div className="flex gap-3 mt-4 pt-4 border-t border-cm-sand">
                  <button
                    onClick={() => fixConsistency(true)}
                    disabled={isFixing}
                    className="px-4 py-2 border border-cm-sand text-cm-charcoal rounded-md text-sm font-medium hover:bg-cm-sand/50 transition-colors disabled:opacity-50"
                  >
                    {isFixing ? 'Processing...' : 'Dry Run'}
                  </button>
                  <button
                    onClick={() => fixConsistency(false)}
                    disabled={isFixing}
                    className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-md text-sm font-medium hover:bg-cm-terracotta/90 transition-colors disabled:opacity-50"
                  >
                    {isFixing ? 'Fixing...' : 'Fix Issues'}
                  </button>
                </div>
              </>
            ) : (
              <p className="text-sm text-green-600 text-center py-4">
                No consistency issues found
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  subtitle,
  color,
}: {
  label: string;
  value: string | number;
  subtitle?: string;
  color?: 'blue' | 'green';
}) {
  const colorClasses = {
    blue: 'text-blue-600',
    green: 'text-green-600',
  };

  return (
    <div className="bg-cm-ivory border border-cm-sand rounded-lg p-4">
      <p className="text-sm text-cm-coffee">{label}</p>
      <p className={`text-2xl font-semibold mt-1 ${color ? colorClasses[color] : 'text-cm-charcoal'}`}>
        {value}
      </p>
      {subtitle && (
        <p className="text-xs text-cm-coffee mt-0.5">{subtitle}</p>
      )}
    </div>
  );
}

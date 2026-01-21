'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
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
        <button
          onClick={loadData}
          disabled={isLoading}
          className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-md text-sm font-medium hover:bg-cm-terracotta/90 transition-colors disabled:opacity-50"
        >
          {isLoading ? 'Loading...' : 'Refresh'}
        </button>
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

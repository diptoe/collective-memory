'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { cn } from '@/lib/utils';

interface EntityTypeInfo {
  type: string;
  count: number;
}

export default function TypesPage() {
  const [types, setTypes] = useState<EntityTypeInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalEntities, setTotalEntities] = useState(0);

  useEffect(() => {
    async function loadTypes() {
      try {
        const res = await api.entities.types();
        const typeData = res.data?.types || [];
        setTypes(typeData);
        setTotalEntities(typeData.reduce((sum, t) => sum + t.count, 0));
      } catch (err) {
        console.error('Failed to load entity types:', err);
      } finally {
        setLoading(false);
      }
    }
    loadTypes();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-cm-coffee">Loading types...</p>
      </div>
    );
  }

  // Color palette for type cards
  const colors = [
    'bg-cm-terracotta',
    'bg-cm-sienna',
    'bg-cm-sage',
    'bg-amber-600',
    'bg-indigo-500',
    'bg-rose-500',
    'bg-teal-500',
    'bg-purple-500',
  ];

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="font-serif text-2xl font-semibold text-cm-charcoal">
          Entity Types
        </h1>
        <p className="text-cm-coffee mt-1">
          Overview of entity categorization in the knowledge graph
        </p>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-cm-ivory rounded-xl p-4 border border-cm-sand">
          <p className="text-sm text-cm-coffee">Total Types</p>
          <p className="text-3xl font-semibold text-cm-charcoal mt-1">{types.length}</p>
        </div>
        <div className="bg-cm-ivory rounded-xl p-4 border border-cm-sand">
          <p className="text-sm text-cm-coffee">Total Entities</p>
          <p className="text-3xl font-semibold text-cm-charcoal mt-1">{totalEntities}</p>
        </div>
        <div className="bg-cm-ivory rounded-xl p-4 border border-cm-sand">
          <p className="text-sm text-cm-coffee">Avg per Type</p>
          <p className="text-3xl font-semibold text-cm-charcoal mt-1">
            {types.length > 0 ? Math.round(totalEntities / types.length) : 0}
          </p>
        </div>
        <div className="bg-cm-ivory rounded-xl p-4 border border-cm-sand">
          <p className="text-sm text-cm-coffee">Most Common</p>
          <p className="text-xl font-semibold text-cm-charcoal mt-1 truncate">
            {types.length > 0 ? types.reduce((a, b) => a.count > b.count ? a : b).type : '-'}
          </p>
        </div>
      </div>

      {/* Types grid */}
      {types.length === 0 ? (
        <div className="text-center py-12 bg-cm-ivory rounded-xl border border-cm-sand">
          <p className="text-cm-coffee mb-2">No entity types found.</p>
          <p className="text-sm text-cm-coffee/70">
            Create entities to see types appear here.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {types
            .sort((a, b) => b.count - a.count)
            .map((typeInfo, index) => {
              const percentage = totalEntities > 0
                ? Math.round((typeInfo.count / totalEntities) * 100)
                : 0;
              const colorClass = colors[index % colors.length];

              return (
                <a
                  key={typeInfo.type}
                  href={`/entities?type=${encodeURIComponent(typeInfo.type)}`}
                  className="bg-cm-ivory rounded-xl border border-cm-sand p-4 hover:shadow-md transition-shadow group"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className={cn(
                      'w-10 h-10 rounded-lg flex items-center justify-center text-white font-semibold',
                      colorClass
                    )}>
                      {typeInfo.type.charAt(0).toUpperCase()}
                    </div>
                    <span className="text-xs text-cm-coffee bg-cm-sand px-2 py-1 rounded-full">
                      {percentage}%
                    </span>
                  </div>

                  <h3 className="font-medium text-cm-charcoal group-hover:text-cm-terracotta transition-colors">
                    {typeInfo.type}
                  </h3>

                  <p className="text-2xl font-semibold text-cm-charcoal mt-1">
                    {typeInfo.count}
                    <span className="text-sm font-normal text-cm-coffee ml-1">
                      {typeInfo.count === 1 ? 'entity' : 'entities'}
                    </span>
                  </p>

                  {/* Progress bar */}
                  <div className="mt-3 h-1.5 bg-cm-sand rounded-full overflow-hidden">
                    <div
                      className={cn('h-full rounded-full transition-all', colorClass)}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </a>
              );
            })}
        </div>
      )}
    </div>
  );
}

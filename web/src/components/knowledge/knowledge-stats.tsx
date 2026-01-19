'use client';

interface KnowledgeStatsProps {
  totals: {
    entities: number;
    relationships: number;
    scopes: number;
  };
}

export function KnowledgeStats({ totals }: KnowledgeStatsProps) {
  const stats = [
    { label: 'Entities', value: totals.entities, icon: '🗃️' },
    { label: 'Relationships', value: totals.relationships, icon: '🔗' },
    { label: 'Scopes', value: totals.scopes, icon: '📊' },
  ];

  return (
    <div className="grid grid-cols-3 gap-4">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="bg-cm-ivory rounded-xl border border-cm-sand p-4 text-center"
        >
          <span className="text-2xl mb-2 block">{stat.icon}</span>
          <p className="text-3xl font-semibold text-cm-charcoal">{stat.value.toLocaleString()}</p>
          <p className="text-sm text-cm-coffee">{stat.label}</p>
        </div>
      ))}
    </div>
  );
}

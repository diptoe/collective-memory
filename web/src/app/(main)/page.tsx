'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import Link from 'next/link';
import * as d3 from 'd3';
import { api } from '@/lib/api';
import { Activity, ActivityType, ActivityTimelinePoint } from '@/types';

// Activity type colors using existing palette
const ACTIVITY_COLORS: Record<ActivityType, string> = {
  message_sent: '#d97757',       // terracotta
  agent_heartbeat: '#6b8fa8',    // blue
  agent_registered: '#4a90a4',   // teal
  search_performed: '#9b7bb8',   // lavender
  entity_created: '#5d8a66',     // green
  entity_updated: '#e8a756',     // amber
  entity_deleted: '#c45c5c',     // red
  entity_read: '#7b6b8a',        // purple
  relationship_created: '#a85a3b', // sienna
  relationship_deleted: '#5c4d3c', // coffee
};

// Activity type labels (for tooltips and details)
const ACTIVITY_LABELS: Record<ActivityType, string> = {
  message_sent: 'Message',
  agent_heartbeat: 'Heartbeat',
  agent_registered: 'Agent Connected',
  search_performed: 'Search',
  entity_created: 'Entity Created',
  entity_updated: 'Entity Updated',
  entity_deleted: 'Entity Deleted',
  entity_read: 'Entity Read',
  relationship_created: 'Relationship Created',
  relationship_deleted: 'Relationship Deleted',
};

// Activity type icons (for radial graph)
const ACTIVITY_ICONS: Record<ActivityType, string> = {
  message_sent: 'M',
  agent_heartbeat: 'H',
  agent_registered: '@',
  search_performed: '?',
  entity_created: '+',
  entity_updated: '~',
  entity_deleted: '-',
  entity_read: 'R',
  relationship_created: '>',
  relationship_deleted: 'x',
};

// Aggregated tile categories
interface TileCategory {
  label: string;
  color: string;
  types: ActivityType[];
}

const TILE_CATEGORIES: TileCategory[] = [
  { label: 'Messages', color: '#d97757', types: ['message_sent'] },
  { label: 'Connections', color: '#4a90a4', types: ['agent_registered'] },
  { label: 'Heartbeats', color: '#6b8fa8', types: ['agent_heartbeat'] },
  { label: 'Searches', color: '#9b7bb8', types: ['search_performed'] },
  { label: 'Reads', color: '#7b6b8a', types: ['entity_read'] },
  { label: 'Creates', color: '#5d8a66', types: ['entity_created', 'relationship_created'] },
  { label: 'Updates', color: '#e8a756', types: ['entity_updated'] },
  { label: 'Deletes', color: '#c45c5c', types: ['entity_deleted', 'relationship_deleted'] },
];

type TimeRange = '1h' | '24h' | '7d';

interface RadialNode {
  id: string;
  label: string;
  type: 'center' | 'time' | 'activity';
  activityType?: ActivityType;
  count?: number;
  x?: number;
  y?: number;
}

interface RadialLink {
  source: string;
  target: string;
}

export default function ActivityPage() {
  const [summary, setSummary] = useState<Record<string, number>>({});
  const [total, setTotal] = useState(0);
  const [timeline, setTimeline] = useState<ActivityTimelinePoint[]>([]);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<TimeRange>('24h');
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [hideHeartbeats, setHideHeartbeats] = useState(true);
  const svgRef = useRef<SVGSVGElement>(null);

  const hours = timeRange === '1h' ? 1 : timeRange === '24h' ? 24 : 168;
  const bucketMinutes = timeRange === '1h' ? 1 : timeRange === '24h' ? 60 : 360;

  const loadData = useCallback(async () => {
    try {
      const [summaryRes, timelineRes, activitiesRes] = await Promise.all([
        api.activities.summary({ hours }),
        api.activities.timeline({ hours, bucket_minutes: bucketMinutes }),
        api.activities.list({ limit: 30, hours }),
      ]);

      if (summaryRes.data) {
        setSummary(summaryRes.data.summary || {});
        setTotal(summaryRes.data.total || 0);
      }

      if (timelineRes.data) {
        setTimeline(timelineRes.data.timeline || []);
      }

      if (activitiesRes.data) {
        setActivities(activitiesRes.data.activities || []);
      }

      setLastUpdate(new Date());
    } catch (err) {
      console.error('Failed to load activity data:', err);
    } finally {
      setLoading(false);
    }
  }, [hours, bucketMinutes]);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, [loadData]);

  // Build radial graph data
  useEffect(() => {
    if (!svgRef.current || timeline.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = svgRef.current.clientWidth;
    const height = svgRef.current.clientHeight;
    const centerX = width / 2;
    // Use a fixed size for the graph and position at top, not centered
    const graphSize = Math.min(width, height, 500); // Cap at 500px
    const maxRadius = graphSize / 2 - 40;
    const centerY = maxRadius + 50; // Position graph near the top

    // Build nodes and links from timeline data
    const nodes: RadialNode[] = [];
    const links: RadialLink[] = [];

    // Center node
    const centerLabel = timeRange === '1h' ? 'Hour' : timeRange === '24h' ? 'Today' : 'Week';
    nodes.push({
      id: 'center',
      label: centerLabel,
      type: 'center',
    });

    // Time nodes (hours or days) arranged in a circle
    // Filter out time points that only have heartbeat activity
    const timePoints = timeline.filter(t => {
      const nonHeartbeatTotal = Object.keys(ACTIVITY_COLORS)
        .filter(type => type !== 'agent_heartbeat')
        .reduce((sum, type) => sum + ((t[type] as number) || 0), 0);
      return nonHeartbeatTotal > 0;
    });
    const angleStep = (2 * Math.PI) / Math.max(timePoints.length, 1);

    timePoints.forEach((point, i) => {
      const date = new Date(point.timestamp);
      let label: string;
      if (timeRange === '1h') {
        label = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      } else if (timeRange === '24h') {
        label = date.toLocaleTimeString([], { hour: '2-digit' });
      } else {
        // Include day number to distinguish between same weekdays (e.g., "Fri 10" vs "Fri 17")
        const weekday = date.toLocaleDateString([], { weekday: 'short' });
        const day = date.getDate();
        label = `${weekday} ${day}`;
      }

      const angle = i * angleStep - Math.PI / 2;
      const timeRadius = maxRadius * 0.4;

      const timeNodeId = `time-${i}`;
      nodes.push({
        id: timeNodeId,
        label,
        type: 'time',
        count: point.total,
        x: centerX + Math.cos(angle) * timeRadius,
        y: centerY + Math.sin(angle) * timeRadius,
      });

      links.push({ source: 'center', target: timeNodeId });

      // Activity type nodes branching from each time node (exclude heartbeats)
      const activityTypes = Object.keys(ACTIVITY_COLORS) as ActivityType[];
      const activeTypes = activityTypes.filter(type => type !== 'agent_heartbeat' && (point[type] as number) > 0);

      if (activeTypes.length > 0) {
        const activityAngleSpread = Math.PI / 6; // Spread for activity nodes
        const activityRadius = maxRadius * 0.75;

        activeTypes.forEach((actType, j) => {
          const actCount = point[actType] as number;
          const actAngle = angle + (j - (activeTypes.length - 1) / 2) * (activityAngleSpread / Math.max(activeTypes.length - 1, 1));

          const actNodeId = `act-${i}-${actType}`;
          nodes.push({
            id: actNodeId,
            label: String(actCount),
            type: 'activity',
            activityType: actType,
            count: actCount,
            x: centerX + Math.cos(actAngle) * activityRadius,
            y: centerY + Math.sin(actAngle) * activityRadius,
          });

          links.push({ source: timeNodeId, target: actNodeId });
        });
      }
    });

    // If no data, show empty state
    if (timePoints.length === 0) {
      svg.append('text')
        .attr('x', centerX)
        .attr('y', centerY)
        .attr('text-anchor', 'middle')
        .attr('fill', '#6b5b4f')
        .attr('font-size', '14px')
        .text('No activity in this time range');
      return;
    }

    // Draw links
    svg.selectAll('line')
      .data(links)
      .enter()
      .append('line')
      .attr('x1', d => {
        const source = nodes.find(n => n.id === d.source);
        return source?.x ?? centerX;
      })
      .attr('y1', d => {
        const source = nodes.find(n => n.id === d.source);
        return source?.y ?? centerY;
      })
      .attr('x2', d => {
        const target = nodes.find(n => n.id === d.target);
        return target?.x ?? centerX;
      })
      .attr('y2', d => {
        const target = nodes.find(n => n.id === d.target);
        return target?.y ?? centerY;
      })
      .attr('stroke', '#e5d5c3')
      .attr('stroke-width', 1)
      .attr('opacity', 0.6);

    // Draw center node
    const centerNode = nodes.find(n => n.type === 'center')!;
    svg.append('circle')
      .attr('cx', centerX)
      .attr('cy', centerY)
      .attr('r', 30)
      .attr('fill', '#d97757')
      .attr('stroke', '#fff')
      .attr('stroke-width', 2);

    svg.append('text')
      .attr('x', centerX)
      .attr('y', centerY + 5)
      .attr('text-anchor', 'middle')
      .attr('fill', '#fff')
      .attr('font-size', '12px')
      .attr('font-weight', 'bold')
      .text(centerNode.label);

    // Draw time nodes
    const timeNodes = nodes.filter(n => n.type === 'time');
    timeNodes.forEach(node => {
      const radius = 8 + Math.min((node.count || 0) * 2, 20);

      svg.append('circle')
        .attr('cx', node.x!)
        .attr('cy', node.y!)
        .attr('r', radius)
        .attr('fill', '#faf8f5')
        .attr('stroke', '#a89888')
        .attr('stroke-width', 2);

      svg.append('text')
        .attr('x', node.x!)
        .attr('y', node.y! + 4)
        .attr('text-anchor', 'middle')
        .attr('fill', '#5c4d3c')
        .attr('font-size', '9px')
        .text(node.label);
    });

    // Draw activity nodes
    const actNodes = nodes.filter(n => n.type === 'activity');
    actNodes.forEach(node => {
      const color = ACTIVITY_COLORS[node.activityType!];
      const radius = 6 + Math.min((node.count || 0) * 1.5, 12);
      const tooltip = `${ACTIVITY_LABELS[node.activityType!]}: ${node.count}`;

      // Group for circle and text so tooltip works on both
      const g = svg.append('g')
        .attr('cursor', 'pointer');

      g.append('title')
        .text(tooltip);

      g.append('circle')
        .attr('cx', node.x!)
        .attr('cy', node.y!)
        .attr('r', radius)
        .attr('fill', color)
        .attr('stroke', '#fff')
        .attr('stroke-width', 1)
        .attr('opacity', 0.9);

      if ((node.count || 0) > 0) {
        g.append('text')
          .attr('x', node.x!)
          .attr('y', node.y! + 3)
          .attr('text-anchor', 'middle')
          .attr('fill', '#fff')
          .attr('font-size', '8px')
          .attr('font-weight', 'bold')
          .attr('pointer-events', 'none')
          .text(node.label);
      }
    });

  }, [timeline, timeRange]);

  const getActivityLink = (activity: Activity): string | null => {
    const meta = activity.extra_data || {};

    switch (activity.target_type) {
      case 'entity': {
        const entityType = (meta.entity_type as string)?.toLowerCase() || 'unknown';
        return `/entities/${entityType}/${activity.target_key}`;
      }
      case 'message':
        return `/messages`;
      case 'agent':
        return `/agents/${activity.actor}`;
      case 'relationship':
        return null;
      default:
        return null;
    }
  };

  const formatActivityTime = (timestamp: string): string => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m`;
    if (diffHours < 24) return `${diffHours}h`;
    return `${diffDays}d`;
  };

  const getActivityDescription = (activity: Activity): string => {
    const meta = activity.extra_data || {};

    switch (activity.activity_type) {
      case 'message_sent':
        return `Message to ${meta.channel || 'channel'}`;
      case 'agent_heartbeat':
        return `Heartbeat`;
      case 'agent_registered':
        return `Connected${meta.client ? ` via ${meta.client}` : ''}`;
      case 'search_performed': {
        const query = meta.query as string;
        const searchType = meta.search_type as string || 'entity';
        const resultCount = meta.result_count as number || 0;
        return query
          ? `Searched "${query}" (${resultCount} results)`
          : `Listed ${meta.entity_type || searchType}s (${resultCount} results)`;
      }
      case 'entity_created':
        return `Created ${meta.entity_type}: ${meta.entity_name}`;
      case 'entity_updated':
        return `Updated ${meta.entity_type}: ${meta.entity_name}`;
      case 'entity_deleted':
        return `Deleted ${meta.entity_type}: ${meta.entity_name}`;
      case 'entity_read':
        return `Read ${meta.entity_type}: ${meta.entity_name}`;
      case 'relationship_created':
        return `Linked ${meta.from_entity_name} → ${meta.to_entity_name}`;
      case 'relationship_deleted':
        return `Unlinked relationship`;
      default:
        return activity.activity_type;
    }
  };

  // Filter activities for sidebar
  const filteredActivities = hideHeartbeats
    ? activities.filter(a => a.activity_type !== 'agent_heartbeat')
    : activities;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-cm-coffee">Loading activity data...</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header with compact tiles */}
      <div className="border-b border-cm-sand bg-cm-ivory p-3">
        <div className="flex items-center justify-between gap-4">
          {/* Title */}
          <div className="flex items-center gap-4">
            <h1 className="font-serif text-xl font-semibold text-cm-charcoal">
              Activity
            </h1>
            <span className="text-sm text-cm-coffee bg-cm-sand/50 px-2 py-0.5 rounded">
              {total} total
            </span>
          </div>

          {/* Aggregated activity tiles - single row */}
          <div className="flex items-center gap-2">
            {TILE_CATEGORIES.map((category) => {
              const count = category.types.reduce((sum, type) => sum + (summary[type] || 0), 0);
              return (
                <div
                  key={category.label}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-cm-cream border border-cm-sand"
                  title={category.types.map(t => ACTIVITY_LABELS[t]).join(', ')}
                >
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: category.color }}
                  />
                  <span className="text-xs text-cm-coffee">{category.label}</span>
                  <span className="text-sm font-semibold text-cm-charcoal">{count}</span>
                </div>
              );
            })}
          </div>

          {/* Time range toggle */}
          <div className="flex items-center gap-3">
            <div className="flex rounded-lg bg-cm-sand/50 p-0.5">
              <button
                onClick={() => setTimeRange('1h')}
                className={`px-2 py-1 text-xs rounded-md transition-colors ${
                  timeRange === '1h'
                    ? 'bg-cm-ivory text-cm-charcoal shadow-sm'
                    : 'text-cm-coffee hover:text-cm-charcoal'
                }`}
              >
                1h
              </button>
              <button
                onClick={() => setTimeRange('24h')}
                className={`px-2 py-1 text-xs rounded-md transition-colors ${
                  timeRange === '24h'
                    ? 'bg-cm-ivory text-cm-charcoal shadow-sm'
                    : 'text-cm-coffee hover:text-cm-charcoal'
                }`}
              >
                24h
              </button>
              <button
                onClick={() => setTimeRange('7d')}
                className={`px-2 py-1 text-xs rounded-md transition-colors ${
                  timeRange === '7d'
                    ? 'bg-cm-ivory text-cm-charcoal shadow-sm'
                    : 'text-cm-coffee hover:text-cm-charcoal'
                }`}
              >
                7d
              </button>
            </div>
            <span className="text-[10px] text-cm-coffee/70">
              {lastUpdate.toLocaleTimeString()}
            </span>
          </div>
        </div>
      </div>

      {/* Main content: Radial graph + Activity stream */}
      <div className="flex-1 flex min-h-0 overflow-hidden">
        {/* Radial Network Graph */}
        <div className="flex-1 bg-cm-cream p-4 h-full min-h-0">
          <div className="w-full h-full bg-cm-ivory rounded-lg border border-cm-sand">
            <svg ref={svgRef} className="w-full h-full" />
          </div>
        </div>

        {/* Activity Stream */}
        <div className="w-80 h-full bg-cm-ivory border-l border-cm-sand flex flex-col min-h-0">
          <div className="p-3 border-b border-cm-sand flex-shrink-0">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-medium text-cm-charcoal">Recent Activity</h2>
              <label className="flex items-center gap-1.5 text-[10px] text-cm-coffee cursor-pointer">
                <input
                  type="checkbox"
                  checked={hideHeartbeats}
                  onChange={(e) => setHideHeartbeats(e.target.checked)}
                  className="w-3 h-3 rounded border-cm-sand"
                />
                Hide heartbeats
              </label>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {filteredActivities.length > 0 ? (
              filteredActivities.map((activity) => {
                const link = getActivityLink(activity);
                const content = (
                  <div className="flex items-start gap-2 p-2 rounded-lg hover:bg-cm-cream transition-colors">
                    <div
                      className="w-5 h-5 rounded-full flex-shrink-0 flex items-center justify-center text-cm-ivory text-[9px] font-bold mt-0.5"
                      style={{ backgroundColor: ACTIVITY_COLORS[activity.activity_type] }}
                    >
                      {ACTIVITY_ICONS[activity.activity_type]}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-cm-charcoal truncate">
                        {getActivityDescription(activity)}
                      </p>
                      <p className="text-[10px] text-cm-coffee/70">
                        {activity.actor} &bull; {formatActivityTime(activity.created_at)}
                      </p>
                    </div>
                  </div>
                );

                return link ? (
                  <Link key={activity.activity_key} href={link} className="block cursor-pointer">
                    {content}
                  </Link>
                ) : (
                  <div key={activity.activity_key}>{content}</div>
                );
              })
            ) : (
              <div className="text-center text-cm-coffee/70 py-8 text-sm">
                No recent activity
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

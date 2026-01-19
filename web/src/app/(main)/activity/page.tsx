'use client';

import { useEffect, useState, useCallback, useRef, useMemo } from 'react';
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

type TimeRange = 'period' | 'today' | 'week';

// Get the current period of day label based on local time
function getCurrentPeriodLabel(): string {
  const hour = new Date().getHours();
  if (hour < 12) return 'Morning';
  if (hour < 18) return 'Afternoon';
  return 'Evening';
}

// Get time range parameters based on user's local timezone
function getTimeRangeParams(range: TimeRange): { hours: number; bucketMinutes: number; since: Date } {
  const now = new Date();

  if (range === 'period') {
    // Current period: Morning (0-11:59), Afternoon (12-17:59), Evening (18-23:59)
    const hour = now.getHours();
    let periodStart: Date;

    if (hour < 12) {
      // Morning: midnight to now
      periodStart = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0);
    } else if (hour < 18) {
      // Afternoon: noon to now
      periodStart = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 12, 0, 0);
    } else {
      // Evening: 6pm to now
      periodStart = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 18, 0, 0);
    }

    const hoursSincePeriodStart = Math.max(1, Math.ceil((now.getTime() - periodStart.getTime()) / (1000 * 60 * 60)));
    return { hours: hoursSincePeriodStart, bucketMinutes: 30, since: periodStart };
  }

  if (range === 'today') {
    // Today: from midnight local time
    const startOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0);
    const hoursSinceStartOfDay = Math.max(1, Math.ceil((now.getTime() - startOfDay.getTime()) / (1000 * 60 * 60)));
    return { hours: hoursSinceStartOfDay, bucketMinutes: 60, since: startOfDay };
  }

  // Week: today + previous 6 days
  const startOfWeek = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 6, 0, 0, 0);
  return { hours: 168, bucketMinutes: 360, since: startOfWeek };
}

interface RadialNode {
  id: string;
  label: string;
  type: 'center' | 'time' | 'activity';
  activityType?: ActivityType;
  count?: number;
  x?: number;
  y?: number;
  timestamp?: string;  // For filtering activities
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
  const [timeRange, setTimeRange] = useState<TimeRange>('today');
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [hideHeartbeats, setHideHeartbeats] = useState(true);
  const [selectedActivity, setSelectedActivity] = useState<{
    timestamp: string;
    activityType: ActivityType;
    count: number;
    activities: Activity[];
    loading: boolean;
  } | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  // Memoize time range params to prevent infinite re-renders
  // Only recalculate when timeRange changes
  const { bucketMinutes, sinceISO } = useMemo(() => {
    const params = getTimeRangeParams(timeRange);
    return {
      bucketMinutes: params.bucketMinutes,
      sinceISO: params.since.toISOString(),
    };
  }, [timeRange]);

  const loadData = useCallback(async () => {
    try {
      const [summaryRes, timelineRes, activitiesRes] = await Promise.all([
        api.activities.summary({ since: sinceISO }),
        api.activities.timeline({ since: sinceISO, bucket_minutes: bucketMinutes }),
        api.activities.list({ limit: 30, since: sinceISO }),
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
  }, [sinceISO, bucketMinutes]);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, [loadData]);

  // Fetch activities for a specific time bucket and type (called on click)
  const fetchActivitiesForBucket = useCallback(async (
    timestamp: string,
    activityType: ActivityType,
    count: number
  ) => {
    // Show popup immediately with loading state
    setSelectedActivity({
      timestamp,
      activityType,
      count,
      activities: [],
      loading: true,
    });

    try {
      const bucketStart = new Date(timestamp);
      // Since we aggregate by hour (or day for week), use 60 minutes (or 24 hours) for the bucket
      // For period/today views, nodes are aggregated by hour so use 60 minutes
      // For week view, nodes are aggregated by day so use 24 hours (1440 minutes)
      const bucketDurationMs = timeRange === 'week' ? 24 * 60 * 60 * 1000 : 60 * 60 * 1000;
      const bucketEnd = new Date(bucketStart.getTime() + bucketDurationMs);

      const res = await api.activities.list({
        type: activityType,
        since: bucketStart.toISOString(),
        until: bucketEnd.toISOString(),
        limit: 100,
      });

      setSelectedActivity({
        timestamp,
        activityType,
        count,
        activities: res.data?.activities || [],
        loading: false,
      });
    } catch (err) {
      console.error('Failed to fetch activities:', err);
      setSelectedActivity({
        timestamp,
        activityType,
        count,
        activities: [],
        loading: false,
      });
    }
  }, [timeRange]);

  // Aggregate timeline points by local hour to prevent duplicate labels
  const aggregateTimelineByLocalHour = useCallback((timelineData: ActivityTimelinePoint[]): ActivityTimelinePoint[] => {
    if (timeRange === 'week') {
      // For week view, aggregate by day instead
      const dayMap = new Map<string, ActivityTimelinePoint>();

      timelineData.forEach(point => {
        const date = new Date(point.timestamp);
        const dayKey = `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`;

        if (!dayMap.has(dayKey)) {
          // Create new aggregated point with the day start as timestamp
          const dayStart = new Date(date.getFullYear(), date.getMonth(), date.getDate(), 0, 0, 0);
          dayMap.set(dayKey, {
            timestamp: dayStart.toISOString(),
            total: 0,
          });
        }

        const existing = dayMap.get(dayKey)!;
        existing.total += point.total;

        // Sum all activity type counts
        Object.keys(ACTIVITY_COLORS).forEach(type => {
          const count = (point[type] as number) || 0;
          existing[type] = ((existing[type] as number) || 0) + count;
        });
      });

      return Array.from(dayMap.values()).sort(
        (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
      );
    }

    // For period and today views, aggregate by local hour
    const hourMap = new Map<string, ActivityTimelinePoint>();

    timelineData.forEach(point => {
      const date = new Date(point.timestamp);
      // Create a key based on local date and hour
      const hourKey = `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}-${date.getHours()}`;

      if (!hourMap.has(hourKey)) {
        // Create new aggregated point with the hour start as timestamp
        const hourStart = new Date(date.getFullYear(), date.getMonth(), date.getDate(), date.getHours(), 0, 0);
        hourMap.set(hourKey, {
          timestamp: hourStart.toISOString(),
          total: 0,
        });
      }

      const existing = hourMap.get(hourKey)!;
      existing.total += point.total;

      // Sum all activity type counts
      Object.keys(ACTIVITY_COLORS).forEach(type => {
        const count = (point[type] as number) || 0;
        existing[type] = ((existing[type] as number) || 0) + count;
      });
    });

    return Array.from(hourMap.values()).sort(
      (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );
  }, [timeRange]);

  // Build radial graph data
  useEffect(() => {
    if (!svgRef.current || timeline.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = svgRef.current.clientWidth;
    const height = svgRef.current.clientHeight;
    const centerX = width / 2;
    const centerY = height / 2;
    // Use available space - no cap, fits container
    const graphSize = Math.min(width, height);
    const maxRadius = graphSize / 2 - 60;

    // Aggregate timeline by local hour/day to prevent duplicate labels
    const aggregatedTimeline = aggregateTimelineByLocalHour(timeline);

    // Build nodes and links from aggregated timeline data
    const nodes: RadialNode[] = [];
    const links: RadialLink[] = [];

    // Center node - always show day and month
    const now = new Date();
    const centerLabel = now.toLocaleDateString([], { day: 'numeric', month: 'short' });
    nodes.push({
      id: 'center',
      label: centerLabel,
      type: 'center',
    });

    // Time nodes (hours or days) arranged in a circle
    // Filter out time points that only have heartbeat activity
    const timePoints = aggregatedTimeline.filter(t => {
      const nonHeartbeatTotal = Object.keys(ACTIVITY_COLORS)
        .filter(type => type !== 'agent_heartbeat')
        .reduce((sum, type) => sum + ((t[type] as number) || 0), 0);
      return nonHeartbeatTotal > 0;
    });
    const angleStep = (2 * Math.PI) / Math.max(timePoints.length, 1);

    timePoints.forEach((point, i) => {
      const date = new Date(point.timestamp);
      let label: string;
      if (timeRange === 'period') {
        // Show am/pm hours for current period
        const hour = date.getHours();
        const ampm = hour >= 12 ? 'pm' : 'am';
        const hour12 = hour % 12 || 12;
        label = `${hour12}${ampm}`;
      } else if (timeRange === 'today') {
        // Show am/pm hours for today
        const hour = date.getHours();
        const ampm = hour >= 12 ? 'pm' : 'am';
        const hour12 = hour % 12 || 12;
        label = `${hour12}${ampm}`;
      } else {
        // Week view: show day and month (e.g., "12 Jan")
        label = date.toLocaleDateString([], { day: 'numeric', month: 'short' });
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
            timestamp: point.timestamp,  // Store for click filtering
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

    // Draw activity nodes with click handlers
    const actNodes = nodes.filter(n => n.type === 'activity');
    actNodes.forEach(node => {
      const color = ACTIVITY_COLORS[node.activityType!];
      const radius = 6 + Math.min((node.count || 0) * 1.5, 12);
      const tooltip = `${ACTIVITY_LABELS[node.activityType!]}: ${node.count} - Click to view`;

      // Group for circle and text so tooltip and click work on both
      const g = svg.append('g')
        .attr('cursor', 'pointer')
        .on('click', () => {
          // Fetch activities via API for this time bucket and type
          fetchActivitiesForBucket(node.timestamp!, node.activityType!, node.count || 0);
        });

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

  }, [timeline, timeRange, bucketMinutes, aggregateTimelineByLocalHour, fetchActivitiesForBucket]);

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
    <div className="h-full flex flex-col overflow-hidden bg-cm-cream">
      {/* Header */}
      <div className="p-6 pb-4">
        {/* First row: Title + Time range */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-serif text-2xl font-semibold text-cm-charcoal">
              Activity
            </h1>
            <p className="text-cm-coffee mt-1">
              {total} events tracked across the platform
            </p>
          </div>

          {/* Time range dropdown */}
          <div className="flex items-center gap-3">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value as TimeRange)}
              className="px-3 py-1.5 text-sm rounded-lg bg-cm-cream border border-cm-sand text-cm-charcoal focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
            >
              <option value="period">{getCurrentPeriodLabel()}</option>
              <option value="today">Today</option>
              <option value="week">Week</option>
            </select>
            <span className="text-[10px] text-cm-coffee/70">
              {lastUpdate.toLocaleTimeString()}
            </span>
          </div>
        </div>

        {/* Second row: Activity tiles */}
        <div className="flex items-center gap-2 mt-4 flex-wrap">
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

      {/* Activity Detail Popup */}
      {selectedActivity && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          onClick={() => setSelectedActivity(null)}
        >
          <div
            className="bg-cm-ivory rounded-xl shadow-xl max-w-lg w-full mx-4 max-h-[80vh] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-4 border-b border-cm-sand flex items-center justify-between flex-shrink-0">
              <div className="flex items-center gap-3">
                <div
                  className="w-8 h-8 rounded-full flex items-center justify-center text-cm-ivory text-sm font-bold"
                  style={{ backgroundColor: ACTIVITY_COLORS[selectedActivity.activityType] }}
                >
                  {ACTIVITY_ICONS[selectedActivity.activityType]}
                </div>
                <div>
                  <h2 className="font-serif text-lg font-semibold text-cm-charcoal">
                    {ACTIVITY_LABELS[selectedActivity.activityType]}
                  </h2>
                  <p className="text-xs text-cm-coffee">
                    {new Date(selectedActivity.timestamp).toLocaleString([], {
                      month: 'short',
                      day: 'numeric',
                      hour: 'numeric',
                      minute: '2-digit',
                      hour12: true,
                    })}
                    {' '}&bull;{' '}
                    {selectedActivity.count} {selectedActivity.count === 1 ? 'activity' : 'activities'}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setSelectedActivity(null)}
                className="text-cm-coffee hover:text-cm-charcoal p-1"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-2">
              {selectedActivity.loading ? (
                <div className="text-center text-cm-coffee/70 py-8">
                  <div className="inline-block animate-spin rounded-full h-6 w-6 border-2 border-cm-terracotta border-t-transparent mb-3" />
                  <p>Loading activities...</p>
                </div>
              ) : selectedActivity.activities.length > 0 ? (
                selectedActivity.activities.map((activity) => {
                  const link = getActivityLink(activity);
                  const content = (
                    <div className="flex items-start gap-3 p-3 rounded-lg bg-cm-cream/50 hover:bg-cm-cream transition-colors">
                      <div
                        className="w-6 h-6 rounded-full flex-shrink-0 flex items-center justify-center text-cm-ivory text-[10px] font-bold"
                        style={{ backgroundColor: ACTIVITY_COLORS[activity.activity_type] }}
                      >
                        {ACTIVITY_ICONS[activity.activity_type]}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-cm-charcoal">
                          {getActivityDescription(activity)}
                        </p>
                        <p className="text-xs text-cm-coffee/70 mt-1">
                          {activity.actor} &bull;{' '}
                          {new Date(activity.created_at).toLocaleTimeString([], {
                            hour: 'numeric',
                            minute: '2-digit',
                            hour12: true,
                          })}
                        </p>
                      </div>
                    </div>
                  );

                  return link ? (
                    <Link
                      key={activity.activity_key}
                      href={link}
                      className="block cursor-pointer"
                      onClick={() => setSelectedActivity(null)}
                    >
                      {content}
                    </Link>
                  ) : (
                    <div key={activity.activity_key}>{content}</div>
                  );
                })
              ) : (
                <div className="text-center text-cm-coffee/70 py-8">
                  <p>No activities found for this time bucket.</p>
                </div>
              )}
            </div>

            <div className="p-3 border-t border-cm-sand flex-shrink-0">
              <button
                onClick={() => setSelectedActivity(null)}
                className="w-full px-4 py-2 text-sm bg-cm-sand text-cm-coffee rounded-lg hover:bg-cm-sand/80 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

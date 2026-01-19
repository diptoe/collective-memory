'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Metric, MilestoneMetricTypes } from '@/types';
import { cn } from '@/lib/utils';

interface MilestoneMetricsProps {
  entityKey: string;
  className?: string;
  compact?: boolean;
}

// Display names for metric types
const METRIC_LABELS: Record<string, string> = {
  [MilestoneMetricTypes.TOOL_CALLS]: 'Tool Calls',
  [MilestoneMetricTypes.FILES_TOUCHED]: 'Files',
  [MilestoneMetricTypes.LINES_ADDED]: 'Lines +',
  [MilestoneMetricTypes.LINES_REMOVED]: 'Lines -',
  [MilestoneMetricTypes.COMMITS_MADE]: 'Commits',
  [MilestoneMetricTypes.DURATION_MINUTES]: 'Duration',
  [MilestoneMetricTypes.HUMAN_GUIDANCE]: 'Human Guidance',
  [MilestoneMetricTypes.MODEL_UNDERSTANDING]: 'Understanding',
  [MilestoneMetricTypes.MODEL_ACCURACY]: 'Accuracy',
  [MilestoneMetricTypes.COLLABORATION_RATING]: 'Collaboration',
  [MilestoneMetricTypes.COMPLEXITY_RATING]: 'Complexity',
};

// Metrics that are self-assessment (1-5 scale)
const SELF_ASSESSMENT_METRICS = new Set<string>([
  MilestoneMetricTypes.HUMAN_GUIDANCE,
  MilestoneMetricTypes.MODEL_UNDERSTANDING,
  MilestoneMetricTypes.MODEL_ACCURACY,
  MilestoneMetricTypes.COLLABORATION_RATING,
  MilestoneMetricTypes.COMPLEXITY_RATING,
]);

// Auto-capture metrics
const AUTO_CAPTURE_METRICS = new Set<string>([
  MilestoneMetricTypes.TOOL_CALLS,
  MilestoneMetricTypes.FILES_TOUCHED,
  MilestoneMetricTypes.LINES_ADDED,
  MilestoneMetricTypes.LINES_REMOVED,
  MilestoneMetricTypes.COMMITS_MADE,
  MilestoneMetricTypes.DURATION_MINUTES,
]);

export function MilestoneMetrics({ entityKey, className, compact = false }: MilestoneMetricsProps) {
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchMetrics() {
      try {
        setLoading(true);
        const response = await api.metrics.list({ entity_key: entityKey });
        if (response.success && response.data) {
          setMetrics(response.data.metrics);
        } else {
          setError(response.msg || 'Failed to load metrics');
        }
      } catch (err) {
        setError('Failed to load metrics');
      } finally {
        setLoading(false);
      }
    }

    if (entityKey) {
      fetchMetrics();
    }
  }, [entityKey]);

  if (loading) {
    return (
      <div className={cn('text-xs text-cm-coffee/50', className)}>
        Loading metrics...
      </div>
    );
  }

  if (error || metrics.length === 0) {
    return null; // Don't show anything if no metrics
  }

  // Group metrics by type (auto-capture vs self-assessment)
  const autoCaptureValues = new Map<string, number>();
  const selfAssessmentValues = new Map<string, number>();

  for (const metric of metrics) {
    if (AUTO_CAPTURE_METRICS.has(metric.metric_type)) {
      autoCaptureValues.set(metric.metric_type, metric.value);
    } else if (SELF_ASSESSMENT_METRICS.has(metric.metric_type)) {
      selfAssessmentValues.set(metric.metric_type, metric.value);
    }
  }

  const formatValue = (type: string, value: number): string => {
    if (type === MilestoneMetricTypes.DURATION_MINUTES) {
      if (value < 60) return `${Math.round(value)}m`;
      return `${Math.round(value / 60 * 10) / 10}h`;
    }
    if (type === MilestoneMetricTypes.LINES_ADDED) return `+${value}`;
    if (type === MilestoneMetricTypes.LINES_REMOVED) return `-${value}`;
    return String(value);
  };

  if (compact) {
    // Compact mode: single row of badges
    return (
      <div className={cn('flex flex-wrap gap-1', className)}>
        {Array.from(autoCaptureValues.entries()).map(([type, value]) => (
          <span
            key={type}
            className="px-1.5 py-0.5 text-xs bg-cm-sand/70 text-cm-coffee rounded"
            title={METRIC_LABELS[type]}
          >
            {formatValue(type, value)}
          </span>
        ))}
        {Array.from(selfAssessmentValues.entries()).map(([type, value]) => (
          <span
            key={type}
            className="px-1.5 py-0.5 text-xs bg-amber-100 text-amber-800 rounded"
            title={METRIC_LABELS[type]}
          >
            {value}/5
          </span>
        ))}
      </div>
    );
  }

  // Full mode: two sections
  return (
    <div className={cn('space-y-2', className)}>
      {/* Auto-capture metrics */}
      {autoCaptureValues.size > 0 && (
        <div>
          <p className="text-xs text-cm-coffee/50 mb-1">Auto-captured</p>
          <div className="flex flex-wrap gap-1">
            {Array.from(autoCaptureValues.entries()).map(([type, value]) => (
              <span
                key={type}
                className="px-2 py-0.5 text-xs bg-cm-sand text-cm-coffee rounded-full"
              >
                {METRIC_LABELS[type]}: {formatValue(type, value)}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Self-assessment metrics */}
      {selfAssessmentValues.size > 0 && (
        <div>
          <p className="text-xs text-cm-coffee/50 mb-1">Self-assessment</p>
          <div className="flex flex-wrap gap-1">
            {Array.from(selfAssessmentValues.entries()).map(([type, value]) => (
              <span
                key={type}
                className="px-2 py-0.5 text-xs bg-amber-100 text-amber-800 rounded-full"
              >
                {METRIC_LABELS[type]}: {value}/5
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

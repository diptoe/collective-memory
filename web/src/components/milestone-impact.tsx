'use client';

import { cn } from '@/lib/utils';
import { Metric, MilestoneMetricTypes } from '@/types';

interface MilestoneImpactProps {
  linesAdded?: number;
  linesRemoved?: number;
  filesTouched?: number;
  toolCalls?: number;
  complexity?: number; // 1-5
  className?: string;
}

interface FullMetricsProps extends MilestoneImpactProps {
  // Self-assessment metrics (1-5 scale)
  modelUnderstanding?: number;
  modelAccuracy?: number;
  collaborationRating?: number;
  humanGuidance?: number;
  duration?: number; // in minutes
  commits?: number;
}

/**
 * Extract all metrics from a Metric array
 */
export function extractAllMetrics(metrics?: Metric[]): FullMetricsProps {
  if (!metrics || metrics.length === 0) return {};

  const getMetricValue = (type: string): number | undefined => {
    const metric = metrics.find(m => m.metric_type === type);
    return metric?.value;
  };

  return {
    linesAdded: getMetricValue(MilestoneMetricTypes.LINES_ADDED),
    linesRemoved: getMetricValue(MilestoneMetricTypes.LINES_REMOVED),
    filesTouched: getMetricValue(MilestoneMetricTypes.FILES_TOUCHED),
    toolCalls: getMetricValue(MilestoneMetricTypes.TOOL_CALLS),
    complexity: getMetricValue(MilestoneMetricTypes.COMPLEXITY_RATING),
    modelUnderstanding: getMetricValue(MilestoneMetricTypes.MODEL_UNDERSTANDING),
    modelAccuracy: getMetricValue(MilestoneMetricTypes.MODEL_ACCURACY),
    collaborationRating: getMetricValue(MilestoneMetricTypes.COLLABORATION_RATING),
    humanGuidance: getMetricValue(MilestoneMetricTypes.HUMAN_GUIDANCE),
    duration: getMetricValue(MilestoneMetricTypes.DURATION_MINUTES),
    commits: getMetricValue(MilestoneMetricTypes.COMMITS_MADE),
  };
}

/**
 * Legacy extract function for backwards compatibility
 */
export function extractImpactFromMetrics(metrics?: Metric[]): MilestoneImpactProps {
  const all = extractAllMetrics(metrics);
  return {
    linesAdded: all.linesAdded,
    linesRemoved: all.linesRemoved,
    filesTouched: all.filesTouched,
    toolCalls: all.toolCalls,
    complexity: all.complexity,
  };
}

/**
 * Full metrics panel for right side of milestone card
 * Shows all metrics in a structured layout
 */
export function MilestoneMetricsPanel({
  linesAdded = 0,
  linesRemoved = 0,
  filesTouched = 0,
  toolCalls = 0,
  complexity,
  modelUnderstanding,
  modelAccuracy,
  collaborationRating,
  humanGuidance,
  duration,
  commits,
  className
}: FullMetricsProps) {
  const codeChurn = linesAdded + linesRemoved;
  const netChange = linesAdded - linesRemoved;

  // Check if there are any metrics to show
  const hasCodeMetrics = codeChurn > 0 || filesTouched > 0 || commits;
  const hasActivityMetrics = toolCalls > 0 || duration;
  const hasSelfAssessments = modelUnderstanding || modelAccuracy || collaborationRating || humanGuidance || complexity;

  if (!hasCodeMetrics && !hasActivityMetrics && !hasSelfAssessments) {
    return (
      <div className={cn('min-w-[120px] flex flex-col items-center justify-center text-xs text-cm-coffee/50', className)}>
        <span>No metrics</span>
        <span>recorded</span>
      </div>
    );
  }

  // Determine color based on net change and churn magnitude
  const isHighChurn = codeChurn > 500;
  const isAddition = netChange >= 0;

  // Calculate circle size: 24-60px based on churn
  const churnSize = codeChurn > 0
    ? Math.min(60, Math.max(28, 24 + Math.sqrt(codeChurn) * 2))
    : 0;

  return (
    <div className={cn('min-w-[120px] flex flex-col items-center gap-2 text-xs', className)}>
      {/* Impact circle with code churn */}
      {codeChurn > 0 && (
        <div
          className={cn(
            'rounded-full flex items-center justify-center font-semibold shadow-sm',
            isHighChurn
              ? 'bg-amber-100 text-amber-700 border-2 border-amber-300'
              : isAddition
                ? 'bg-green-100 text-green-700 border-2 border-green-300'
                : 'bg-red-100 text-red-700 border-2 border-red-300'
          )}
          style={{ width: churnSize, height: churnSize }}
          title={`${codeChurn} lines changed`}
        >
          {isAddition ? '+' : ''}{netChange}
        </div>
      )}

      {/* Code metrics */}
      {hasCodeMetrics && (
        <div className="flex flex-col items-center gap-0.5 text-cm-coffee">
          {codeChurn > 0 && (
            <div className="flex items-center gap-1.5">
              <span className="text-green-600">+{linesAdded}</span>
              <span className="text-red-600">-{linesRemoved}</span>
            </div>
          )}
          {filesTouched > 0 && (
            <span>{filesTouched} file{filesTouched !== 1 ? 's' : ''}</span>
          )}
          {commits && commits > 0 && (
            <span>{commits} commit{commits !== 1 ? 's' : ''}</span>
          )}
        </div>
      )}

      {/* Activity metrics */}
      {hasActivityMetrics && (
        <div className="flex flex-col items-center gap-0.5 text-cm-coffee/70 border-t border-cm-sand/50 pt-1 mt-1">
          {toolCalls > 0 && (
            <span title="Tool calls">{toolCalls} tools</span>
          )}
          {duration && duration > 0 && (
            <span title="Duration">
              {duration >= 60 ? `${Math.round(duration / 6) / 10}h` : `${Math.round(duration)}m`}
            </span>
          )}
        </div>
      )}

      {/* Self-assessment indicators */}
      {hasSelfAssessments && (
        <div className="flex flex-col items-center gap-1 border-t border-cm-sand/50 pt-1 mt-1 w-full">
          {/* Complexity bar */}
          {complexity && complexity > 0 && (
            <div className="flex items-center gap-1" title={`Complexity: ${complexity}/5`}>
              <span className="text-cm-coffee/50 text-[10px]">Cmplx</span>
              <div className="flex gap-0.5">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div
                    key={i}
                    className={cn(
                      'w-1.5 h-1.5 rounded-full',
                      i < complexity ? 'bg-cm-terracotta' : 'bg-cm-sand'
                    )}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Other ratings as compact badges */}
          <div className="flex flex-wrap justify-center gap-1">
            {modelUnderstanding && (
              <span className="px-1 py-0.5 bg-amber-100 text-amber-700 rounded text-[10px]" title="Model Understanding">
                🎯{modelUnderstanding}
              </span>
            )}
            {modelAccuracy && (
              <span className="px-1 py-0.5 bg-green-100 text-green-700 rounded text-[10px]" title="Model Accuracy">
                ✓{modelAccuracy}
              </span>
            )}
            {collaborationRating && (
              <span className="px-1 py-0.5 bg-blue-100 text-blue-700 rounded text-[10px]" title="Collaboration">
                🤝{collaborationRating}
              </span>
            )}
            {humanGuidance && (
              <span className="px-1 py-0.5 bg-purple-100 text-purple-700 rounded text-[10px]" title="Human Guidance Level">
                👤{humanGuidance}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Original MilestoneImpact component (kept for backwards compatibility)
 * Visual impact indicator for milestones
 */
export function MilestoneImpact({
  linesAdded = 0,
  linesRemoved = 0,
  filesTouched = 0,
  toolCalls = 0,
  complexity,
  className
}: MilestoneImpactProps) {
  const codeChurn = linesAdded + linesRemoved;
  const netChange = linesAdded - linesRemoved;

  if (codeChurn === 0 && filesTouched === 0) {
    return null;
  }

  const churnSize = Math.min(80, Math.max(28, 20 + Math.sqrt(codeChurn) * 3));
  const isHighChurn = codeChurn > 500;
  const isAddition = netChange >= 0;

  return (
    <div className={cn('flex flex-col items-center gap-1 min-w-[80px]', className)}>
      <div
        className={cn(
          'rounded-full flex items-center justify-center text-xs font-semibold transition-all shadow-sm',
          isHighChurn
            ? 'bg-amber-100 text-amber-700 border-2 border-amber-300'
            : isAddition
              ? 'bg-green-100 text-green-700 border-2 border-green-300'
              : 'bg-red-100 text-red-700 border-2 border-red-300'
        )}
        style={{ width: churnSize, height: churnSize }}
        title={`${codeChurn} lines changed (${linesAdded}+ / ${linesRemoved}-)`}
      >
        {codeChurn > 0 ? (
          <span>{isAddition ? '+' : ''}{netChange}</span>
        ) : (
          <span className="text-cm-coffee/50">-</span>
        )}
      </div>

      {filesTouched > 0 && (
        <span className="text-xs text-cm-coffee whitespace-nowrap">
          {filesTouched} file{filesTouched !== 1 ? 's' : ''}
        </span>
      )}

      {complexity !== undefined && complexity > 0 && (
        <div className="flex gap-0.5" title={`Complexity: ${complexity}/5`}>
          {Array.from({ length: 5 }).map((_, i) => (
            <div
              key={i}
              className={cn(
                'w-1.5 h-1.5 rounded-full',
                i < complexity ? 'bg-cm-terracotta' : 'bg-cm-sand'
              )}
            />
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Compact inline impact indicator for smaller spaces
 */
export function MilestoneImpactInline({
  linesAdded = 0,
  linesRemoved = 0,
  filesTouched = 0,
  className
}: Omit<MilestoneImpactProps, 'complexity' | 'toolCalls'>) {
  const codeChurn = linesAdded + linesRemoved;
  const netChange = linesAdded - linesRemoved;

  if (codeChurn === 0) {
    return null;
  }

  const isHighChurn = codeChurn > 500;
  const isAddition = netChange >= 0;

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-1.5 py-0.5 text-xs rounded',
        isHighChurn
          ? 'bg-amber-100 text-amber-700'
          : isAddition
            ? 'bg-green-100 text-green-700'
            : 'bg-red-100 text-red-700',
        className
      )}
      title={`${linesAdded}+ / ${linesRemoved}- (${filesTouched} files)`}
    >
      <span className="font-medium">{isAddition ? '+' : ''}{netChange}</span>
      {filesTouched > 0 && (
        <>
          <span className="opacity-50">|</span>
          <span>{filesTouched}f</span>
        </>
      )}
    </span>
  );
}

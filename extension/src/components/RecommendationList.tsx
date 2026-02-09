import React from 'react';
import { AlertTriangle, AlertCircle, Info, Lightbulb, ChevronRight } from 'lucide-react';

interface Violation {
  type: string;
  severity: 'high' | 'medium' | 'low';
  description: string;
  suggestion?: string;
}

interface RecommendationListProps {
  violations: Violation[];
  recommendations: string[];
  isLoading?: boolean;
}

const severityConfig = {
  high: {
    icon: AlertTriangle,
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    textColor: 'text-red-700',
    iconColor: 'text-red-500',
    label: 'High Priority',
  },
  medium: {
    icon: AlertCircle,
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
    textColor: 'text-yellow-700',
    iconColor: 'text-yellow-500',
    label: 'Medium Priority',
  },
  low: {
    icon: Info,
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    textColor: 'text-blue-700',
    iconColor: 'text-blue-500',
    label: 'Low Priority',
  },
};

function ViolationItem({ violation }: { violation: Violation }) {
  const config = severityConfig[violation.severity];
  const Icon = config.icon;

  return (
    <div className={`p-3 rounded-lg border ${config.borderColor} ${config.bgColor}`}>
      <div className="flex items-start gap-2">
        <Icon className={`w-4 h-4 ${config.iconColor} mt-0.5 flex-shrink-0`} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs font-semibold uppercase ${config.textColor}`}>
              {violation.type}
            </span>
            <span className={`text-[10px] px-1.5 py-0.5 rounded ${config.bgColor} ${config.textColor} border ${config.borderColor}`}>
              {config.label}
            </span>
          </div>
          <p className="text-sm text-dark-text leading-relaxed">
            {violation.description}
          </p>
          {violation.suggestion && (
            <div className="mt-2 flex items-start gap-1.5 text-xs text-dark-secondary">
              <ChevronRight className="w-3 h-3 mt-0.5 text-brand-500" />
              <span><strong>Suggestion:</strong> {violation.suggestion}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function RecommendationItem({ text }: { text: string }) {
  return (
    <div className="flex items-start gap-2 p-2 rounded-lg hover:bg-gray-50 transition-colors">
      <Lightbulb className="w-4 h-4 text-brand-500 mt-0.5 flex-shrink-0" />
      <span className="text-sm text-dark-secondary leading-relaxed">{text}</span>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-3">
      {[1, 2, 3].map((i) => (
        <div key={i} className="p-3 rounded-lg border border-gray-200">
          <div className="flex items-start gap-2">
            <div className="w-4 h-4 rounded bg-gray-200 loading-shimmer" />
            <div className="flex-1">
              <div className="w-20 h-3 rounded bg-gray-200 loading-shimmer mb-2" />
              <div className="w-full h-4 rounded bg-gray-200 loading-shimmer" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export function RecommendationList({ 
  violations, 
  recommendations, 
  isLoading 
}: RecommendationListProps) {
  if (isLoading) {
    return <LoadingSkeleton />;
  }

  const hasContent = violations.length > 0 || recommendations.length > 0;

  if (!hasContent) {
    return (
      <div className="text-center py-8 px-4">
        <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-green-100 flex items-center justify-center">
          <Info className="w-6 h-6 text-green-600" />
        </div>
        <p className="text-sm text-dark-secondary">
          No issues found! Your content looks great.
        </p>
      </div>
    );
  }

  // Sort violations by severity
  const sortedViolations = [...violations].sort((a, b) => {
    const order = { high: 0, medium: 1, low: 2 };
    return order[a.severity] - order[b.severity];
  });

  return (
    <div className="space-y-4">
      {sortedViolations.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-dark-tertiary uppercase tracking-wide mb-2">
            Issues Found ({sortedViolations.length})
          </h3>
          <div className="space-y-2">
            {sortedViolations.map((violation, index) => (
              <ViolationItem key={index} violation={violation} />
            ))}
          </div>
        </div>
      )}

      {recommendations.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-dark-tertiary uppercase tracking-wide mb-2">
            Recommendations ({recommendations.length})
          </h3>
          <div className="space-y-1">
            {recommendations.map((rec, index) => (
              <RecommendationItem key={index} text={rec} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

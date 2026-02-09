import React from 'react';
import { AlertTriangle, AlertCircle, Info, Lightbulb, ChevronRight } from 'lucide-react';
import type { AnalysisViolation } from '../lib/types';

interface RecommendationListProps {
  violations: AnalysisViolation[];
  recommendations: string[];
  isLoading?: boolean;
}

const severityConfig = {
  high: { icon: AlertTriangle, bgColor: '#fef2f2', borderColor: '#fecaca', textColor: '#b91c1c', iconColor: '#ef4444' },
  medium: { icon: AlertCircle, bgColor: '#fefce8', borderColor: '#fde047', textColor: '#a16207', iconColor: '#eab308' },
  low: { icon: Info, bgColor: '#eff6ff', borderColor: '#bfdbfe', textColor: '#1d4ed8', iconColor: '#3b82f6' },
};

function ViolationItem({ violation }: { violation: AnalysisViolation }) {
  const config = severityConfig[violation.severity];
  const Icon = config.icon;

  return (
    <div style={{
      padding: '12px',
      borderRadius: '8px',
      border: `1px solid ${config.borderColor}`,
      backgroundColor: config.bgColor
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
        <Icon style={{ width: '16px', height: '16px', color: config.iconColor, marginTop: '2px', flexShrink: 0 }} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span style={{ fontSize: '11px', fontWeight: '600', textTransform: 'uppercase', color: config.textColor }}>
              {violation.type}
            </span>
          </div>
          <p style={{ fontSize: '13px', color: '#101828', lineHeight: '1.5', margin: 0 }}>
            {violation.description}
          </p>
          {violation.suggestion && (
            <div style={{ marginTop: '8px', display: 'flex', alignItems: 'flex-start', gap: '6px', fontSize: '12px', color: '#4b5563' }}>
              <ChevronRight style={{ width: '12px', height: '12px', marginTop: '2px', color: '#6941C6' }} />
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
    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', padding: '8px', borderRadius: '8px' }}>
      <Lightbulb style={{ width: '16px', height: '16px', color: '#6941C6', marginTop: '2px', flexShrink: 0 }} />
      <span style={{ fontSize: '13px', color: '#4b5563', lineHeight: '1.5' }}>{text}</span>
    </div>
  );
}

export function RecommendationList({ violations, recommendations, isLoading }: RecommendationListProps) {
  if (isLoading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {[1, 2].map((i) => (
          <div key={i} style={{ padding: '12px', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
              <div style={{ width: '16px', height: '16px', borderRadius: '4px', backgroundColor: '#e5e7eb' }} />
              <div style={{ flex: 1 }}>
                <div style={{ width: '80px', height: '12px', borderRadius: '4px', backgroundColor: '#e5e7eb', marginBottom: '8px' }} />
                <div style={{ width: '100%', height: '16px', borderRadius: '4px', backgroundColor: '#e5e7eb' }} />
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  const hasContent = violations.length > 0 || recommendations.length > 0;

  if (!hasContent) {
    return (
      <div style={{ textAlign: 'center', padding: '32px 16px' }}>
        <div style={{
          width: '48px',
          height: '48px',
          margin: '0 auto 12px',
          borderRadius: '50%',
          backgroundColor: '#f0fdf4',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <Info style={{ width: '24px', height: '24px', color: '#16a34a' }} />
        </div>
        <p style={{ fontSize: '14px', color: '#4b5563', margin: 0 }}>
          No issues found! Your content looks great.
        </p>
      </div>
    );
  }

  const sortedViolations = [...violations].sort((a, b) => {
    const order = { high: 0, medium: 1, low: 2 };
    return order[a.severity] - order[b.severity];
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {sortedViolations.length > 0 && (
        <div>
          <h3 style={{ fontSize: '11px', fontWeight: '600', color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>
            Issues Found ({sortedViolations.length})
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {sortedViolations.map((violation, index) => (
              <ViolationItem key={index} violation={violation} />
            ))}
          </div>
        </div>
      )}

      {recommendations.length > 0 && (
        <div>
          <h3 style={{ fontSize: '11px', fontWeight: '600', color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>
            Recommendations ({recommendations.length})
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {recommendations.map((rec, index) => (
              <RecommendationItem key={index} text={rec} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

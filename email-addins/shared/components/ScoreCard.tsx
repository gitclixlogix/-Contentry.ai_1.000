import React from 'react';
import { Shield, Users, Target, TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface ScoreCardProps {
  label: string;
  score: number;
  type: 'compliance' | 'cultural' | 'accuracy' | 'overall';
  isLoading?: boolean;
}

const scoreConfig = {
  compliance: { icon: Shield, color: 'blue' },
  cultural: { icon: Users, color: 'purple' },
  accuracy: { icon: Target, color: 'green' },
  overall: { icon: Target, color: 'brand' },
};

const getScoreColor = (score: number): string => {
  if (score >= 80) return '#16a34a';
  if (score >= 60) return '#ca8a04';
  return '#dc2626';
};

const getScoreBgColor = (score: number): string => {
  if (score >= 80) return '#f0fdf4';
  if (score >= 60) return '#fefce8';
  return '#fef2f2';
};

export function ScoreCard({ label, score, type, isLoading }: ScoreCardProps) {
  const config = scoreConfig[type];
  const Icon = config.icon;

  if (isLoading) {
    return (
      <div style={{
        padding: '12px',
        borderRadius: '8px',
        border: '1px solid #e5e7eb',
        backgroundColor: '#f9fafb'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
          <div style={{ width: '16px', height: '16px', borderRadius: '4px', backgroundColor: '#e5e7eb' }} />
          <div style={{ width: '64px', height: '12px', borderRadius: '4px', backgroundColor: '#e5e7eb' }} />
        </div>
        <div style={{ width: '48px', height: '24px', borderRadius: '4px', backgroundColor: '#e5e7eb' }} />
      </div>
    );
  }

  return (
    <div style={{
      padding: '12px',
      borderRadius: '8px',
      border: '1px solid #e5e7eb',
      backgroundColor: getScoreBgColor(score),
      transition: 'all 0.3s'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
        <Icon style={{ width: '16px', height: '16px', color: '#6941C6' }} />
        <span style={{ fontSize: '11px', fontWeight: '500', color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          {label}
        </span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontSize: '24px', fontWeight: '700', color: getScoreColor(score) }}>
          {score}
        </span>
        {score >= 80 ? (
          <TrendingUp style={{ width: '12px', height: '12px', color: getScoreColor(score) }} />
        ) : score >= 60 ? (
          <Minus style={{ width: '12px', height: '12px', color: getScoreColor(score) }} />
        ) : (
          <TrendingDown style={{ width: '12px', height: '12px', color: getScoreColor(score) }} />
        )}
      </div>
    </div>
  );
}

export function ScoreGrid({ 
  scores, 
  isLoading 
}: { 
  scores: { compliance: number; cultural: number; accuracy: number; overall: number };
  isLoading?: boolean;
}) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
      <ScoreCard label="Compliance" score={scores.compliance} type="compliance" isLoading={isLoading} />
      <ScoreCard label="Cultural" score={scores.cultural} type="cultural" isLoading={isLoading} />
      <ScoreCard label="Accuracy" score={scores.accuracy} type="accuracy" isLoading={isLoading} />
      <ScoreCard label="Overall" score={scores.overall} type="overall" isLoading={isLoading} />
    </div>
  );
}

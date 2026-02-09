import React from 'react';
import { Shield, Users, Target, TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface ScoreCardProps {
  label: string;
  score: number;
  type: 'compliance' | 'cultural' | 'accuracy' | 'overall';
  isLoading?: boolean;
}

const scoreConfig = {
  compliance: {
    icon: Shield,
    color: 'blue',
    bgLight: 'bg-blue-50',
    textColor: 'text-blue-600',
    borderColor: 'border-blue-200',
  },
  cultural: {
    icon: Users,
    color: 'purple',
    bgLight: 'bg-purple-50',
    textColor: 'text-purple-600',
    borderColor: 'border-purple-200',
  },
  accuracy: {
    icon: Target,
    color: 'green',
    bgLight: 'bg-green-50',
    textColor: 'text-green-600',
    borderColor: 'border-green-200',
  },
  overall: {
    icon: Target,
    color: 'brand',
    bgLight: 'bg-brand-50',
    textColor: 'text-brand-500',
    borderColor: 'border-brand-200',
  },
};

function getScoreColor(score: number): string {
  if (score >= 80) return 'text-green-600';
  if (score >= 60) return 'text-yellow-600';
  return 'text-red-600';
}

function getScoreBgColor(score: number): string {
  if (score >= 80) return 'bg-green-50';
  if (score >= 60) return 'bg-yellow-50';
  return 'bg-red-50';
}

function getTrendIcon(score: number) {
  if (score >= 80) return <TrendingUp className="w-3 h-3" />;
  if (score >= 60) return <Minus className="w-3 h-3" />;
  return <TrendingDown className="w-3 h-3" />;
}

export function ScoreCard({ label, score, type, isLoading }: ScoreCardProps) {
  const config = scoreConfig[type];
  const Icon = config.icon;

  if (isLoading) {
    return (
      <div className={`p-3 rounded-lg border ${config.borderColor} ${config.bgLight}`}>
        <div className="flex items-center gap-2 mb-2">
          <div className="w-4 h-4 rounded bg-gray-200 loading-shimmer" />
          <div className="w-16 h-3 rounded bg-gray-200 loading-shimmer" />
        </div>
        <div className="w-12 h-6 rounded bg-gray-200 loading-shimmer" />
      </div>
    );
  }

  return (
    <div className={`p-3 rounded-lg border ${config.borderColor} ${getScoreBgColor(score)} transition-all duration-300`}>
      <div className="flex items-center gap-2 mb-1">
        <Icon className={`w-4 h-4 ${config.textColor}`} />
        <span className="text-xs font-medium text-dark-tertiary uppercase tracking-wide">
          {label}
        </span>
      </div>
      <div className="flex items-center gap-2">
        <span className={`text-2xl font-bold ${getScoreColor(score)} score-pulse`}>
          {score}
        </span>
        <span className={`${getScoreColor(score)}`}>
          {getTrendIcon(score)}
        </span>
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
    <div className="grid grid-cols-2 gap-2">
      <ScoreCard label="Compliance" score={scores.compliance} type="compliance" isLoading={isLoading} />
      <ScoreCard label="Cultural" score={scores.cultural} type="cultural" isLoading={isLoading} />
      <ScoreCard label="Accuracy" score={scores.accuracy} type="accuracy" isLoading={isLoading} />
      <ScoreCard label="Overall" score={scores.overall} type="overall" isLoading={isLoading} />
    </div>
  );
}

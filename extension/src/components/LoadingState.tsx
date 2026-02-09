import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingStateProps {
  message?: string;
}

export function LoadingState({ message = 'Loading...' }: LoadingStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4">
      <div className="relative">
        <div className="w-12 h-12 rounded-full border-4 border-brand-100" />
        <Loader2 className="absolute inset-0 w-12 h-12 text-brand-500 animate-spin" />
      </div>
      <p className="mt-4 text-sm text-dark-tertiary">{message}</p>
    </div>
  );
}

export function AnalyzingState() {
  return (
    <div className="flex items-center gap-3 p-4 rounded-lg bg-brand-50 border border-brand-200">
      <Loader2 className="w-5 h-5 text-brand-500 animate-spin" />
      <div>
        <p className="text-sm font-medium text-brand-700">Analyzing content...</p>
        <p className="text-xs text-brand-600">This may take a few seconds</p>
      </div>
    </div>
  );
}

export function EmptyState({ 
  title, 
  description, 
  icon: Icon 
}: { 
  title: string; 
  description: string; 
  icon: React.ComponentType<{ className?: string }>;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <div className="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center mb-4">
        <Icon className="w-8 h-8 text-gray-400" />
      </div>
      <h3 className="text-sm font-semibold text-dark-text mb-1">{title}</h3>
      <p className="text-xs text-dark-tertiary max-w-[200px]">{description}</p>
    </div>
  );
}

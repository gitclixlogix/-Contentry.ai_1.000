import React from 'react';
import { ChevronDown, Briefcase, User } from 'lucide-react';
import type { StrategicProfile } from '~/lib/api';

interface ProfileSelectorProps {
  profiles: StrategicProfile[];
  selectedId: string | null;
  onSelect: (profileId: string) => void;
  isLoading?: boolean;
}

export function ProfileSelector({ 
  profiles, 
  selectedId, 
  onSelect, 
  isLoading 
}: ProfileSelectorProps) {
  const selectedProfile = profiles.find(p => p.id === selectedId);

  if (isLoading) {
    return (
      <div className="w-full p-3 rounded-lg border border-gray-200 bg-white">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 rounded bg-gray-200 loading-shimmer" />
          <div className="flex-1 h-4 rounded bg-gray-200 loading-shimmer" />
        </div>
      </div>
    );
  }

  return (
    <div className="relative">
      <label className="block text-xs font-medium text-dark-tertiary mb-1.5 uppercase tracking-wide">
        Strategic Profile (Brand Brain)
      </label>
      <div className="relative">
        <select
          value={selectedId || ''}
          onChange={(e) => onSelect(e.target.value)}
          className="w-full p-3 pr-10 rounded-lg border border-gray-200 bg-white 
                     text-dark-text font-medium appearance-none cursor-pointer
                     hover:border-brand-500 focus:border-brand-500 focus:ring-2 
                     focus:ring-brand-100 transition-all duration-200
                     text-sm"
        >
          <option value="">No profile selected</option>
          {profiles.map((profile) => (
            <option key={profile.id} value={profile.id}>
              {profile.profile_type === 'company' ? '🏢 ' : '👤 '}
              {profile.name}
            </option>
          ))}
        </select>
        <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
      </div>
      {selectedProfile && (
        <div className="mt-2 flex items-center gap-2 text-xs text-dark-tertiary">
          {selectedProfile.profile_type === 'company' ? (
            <Briefcase className="w-3 h-3" />
          ) : (
            <User className="w-3 h-3" />
          )}
          <span>{selectedProfile.writing_tone || 'Professional'} tone</span>
        </div>
      )}
    </div>
  );
}

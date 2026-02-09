import React from 'react';
import { ChevronDown, Briefcase, User } from 'lucide-react';
import type { StrategicProfile } from '../lib/types';

interface ProfileSelectorProps {
  profiles: StrategicProfile[];
  selectedId: string | null;
  onSelect: (profileId: string) => void;
  isLoading?: boolean;
}

export function ProfileSelector({ profiles, selectedId, onSelect, isLoading }: ProfileSelectorProps) {
  const selectedProfile = profiles.find(p => p.id === selectedId);

  if (isLoading) {
    return (
      <div style={{ padding: '12px', borderRadius: '8px', border: '1px solid #e5e7eb', backgroundColor: 'white' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '20px', height: '20px', borderRadius: '4px', backgroundColor: '#e5e7eb' }} />
          <div style={{ flex: 1, height: '16px', borderRadius: '4px', backgroundColor: '#e5e7eb' }} />
        </div>
      </div>
    );
  }

  return (
    <div>
      <label style={{
        display: 'block',
        fontSize: '11px',
        fontWeight: '500',
        color: '#6b7280',
        marginBottom: '6px',
        textTransform: 'uppercase',
        letterSpacing: '0.05em'
      }}>
        Strategic Profile (Brand Brain)
      </label>
      <div style={{ position: 'relative' }}>
        <select
          value={selectedId || ''}
          onChange={(e) => onSelect(e.target.value)}
          style={{
            width: '100%',
            padding: '12px 40px 12px 12px',
            borderRadius: '8px',
            border: '1px solid #e5e7eb',
            backgroundColor: 'white',
            fontSize: '14px',
            fontWeight: '500',
            color: '#101828',
            appearance: 'none',
            cursor: 'pointer',
            outline: 'none'
          }}
        >
          <option value="">No profile selected</option>
          {profiles.map((profile) => (
            <option key={profile.id} value={profile.id}>
              {profile.profile_type === 'company' ? '🏢 ' : '👤 '}
              {profile.name}
            </option>
          ))}
        </select>
        <ChevronDown style={{
          position: 'absolute',
          right: '12px',
          top: '50%',
          transform: 'translateY(-50%)',
          width: '16px',
          height: '16px',
          color: '#9ca3af',
          pointerEvents: 'none'
        }} />
      </div>
      {selectedProfile && (
        <div style={{ marginTop: '8px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: '#6b7280' }}>
          {selectedProfile.profile_type === 'company' ? (
            <Briefcase style={{ width: '12px', height: '12px' }} />
          ) : (
            <User style={{ width: '12px', height: '12px' }} />
          )}
          <span>{selectedProfile.writing_tone || 'Professional'} tone</span>
        </div>
      )}
    </div>
  );
}

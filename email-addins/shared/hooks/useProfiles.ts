import { useState, useEffect, useCallback } from 'react';
import { api } from '../lib/api';
import type { StrategicProfile } from '../lib/types';

export function useProfiles() {
  const [profiles, setProfiles] = useState<StrategicProfile[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadProfiles = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const fetchedProfiles = await api.getStrategicProfiles();
        setProfiles(fetchedProfiles);

        // Load saved selection
        const savedId = await api.getSelectedProfile();
        if (savedId && fetchedProfiles.some(p => p.id === savedId)) {
          setSelectedProfileId(savedId);
        } else if (fetchedProfiles.length > 0) {
          setSelectedProfileId(fetchedProfiles[0].id);
        }
      } catch (err) {
        console.error('Failed to load profiles:', err);
        setError('Failed to load profiles');
      } finally {
        setIsLoading(false);
      }
    };

    loadProfiles();
  }, []);

  const selectProfile = useCallback(async (profileId: string) => {
    setSelectedProfileId(profileId);
    await api.setSelectedProfile(profileId);
  }, []);

  const selectedProfile = profiles.find(p => p.id === selectedProfileId) || null;

  return {
    profiles,
    selectedProfileId,
    selectedProfile,
    isLoading,
    error,
    selectProfile,
  };
}

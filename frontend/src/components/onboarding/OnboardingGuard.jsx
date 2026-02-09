'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { Flex, Spinner } from '@chakra-ui/react';
import api from '@/lib/api';
import { useAuth } from '@/context/AuthContext';

// Pages that should skip onboarding check
const SKIP_ONBOARDING_CHECK = [
  '/onboarding',
  '/contentry/auth',
  '/contentry/terms',
  '/contentry/privacy',
];

export default function OnboardingGuard({ children }) {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [isChecking, setIsChecking] = useState(true);
  const [shouldShowContent, setShouldShowContent] = useState(false);

  useEffect(() => {
    const checkOnboarding = async () => {
      // Wait for auth to load
      if (authLoading) return;

      // If no user, let auth handle redirect
      if (!user?.id) {
        setShouldShowContent(true);
        setIsChecking(false);
        return;
      }

      // Skip check for certain paths
      const shouldSkip = SKIP_ONBOARDING_CHECK.some(path => pathname?.startsWith(path));
      if (shouldSkip) {
        setShouldShowContent(true);
        setIsChecking(false);
        return;
      }

      try {
        const response = await api.get('/onboarding/status');

        if (response.data.should_show_wizard) {
          // Redirect to onboarding
          router.push('/onboarding');
          return;
        }

        // User has completed onboarding, show content
        setShouldShowContent(true);
      } catch (error) {
        console.error('Error checking onboarding status:', error);
        // On error, allow access (don't block user)
        setShouldShowContent(true);
      } finally {
        setIsChecking(false);
      }
    };

    checkOnboarding();
  }, [user?.id, authLoading, pathname, router]);

  // Show loading while checking
  if (isChecking && !shouldShowContent) {
    return (
      <Flex minH="100vh" align="center" justify="center">
        <Spinner size="xl" color="brand.500" />
      </Flex>
    );
  }

  return children;
}

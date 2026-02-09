'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Settings() {
  const router = useRouter();
  
  useEffect(() => {
    // Redirect to the Contentry settings page
    router.replace('/contentry/settings');
  }, [router]);

  return null;
}

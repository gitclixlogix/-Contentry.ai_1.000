'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function AIAssistant() {
  const router = useRouter();
  
  useEffect(() => {
    router.replace('/contentry/content-moderation');
  }, [router]);

  return null;
}
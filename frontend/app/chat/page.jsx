'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Chat() {
  const router = useRouter();
  
  useEffect(() => {
    router.replace('/contentry/content-moderation');
  }, [router]);

  return null;
}
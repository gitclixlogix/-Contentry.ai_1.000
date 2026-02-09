'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function History() {
  const router = useRouter();
  
  useEffect(() => {
    // Redirect to content moderation page which has the posts/history
    router.replace('/contentry/content-moderation');
  }, [router]);

  return null;
}
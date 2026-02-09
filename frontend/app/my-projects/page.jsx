'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function MyProjects() {
  const router = useRouter();
  
  useEffect(() => {
    router.replace('/contentry/posts');
  }, [router]);

  return null;
}
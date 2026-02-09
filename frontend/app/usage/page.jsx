'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Usage() {
  const router = useRouter();
  
  useEffect(() => {
    router.replace('/contentry/dashboard');
  }, [router]);

  return null;
}
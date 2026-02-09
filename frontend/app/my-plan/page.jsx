'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function MyPlan() {
  const router = useRouter();
  
  useEffect(() => {
    router.replace('/contentry/subscription');
  }, [router]);

  return null;
}
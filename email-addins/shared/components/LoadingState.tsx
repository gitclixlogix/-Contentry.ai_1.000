import React from 'react';
import { Loader2, FileText } from 'lucide-react';

export function LoadingState({ message = 'Loading...' }: { message?: string }) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '48px 16px'
    }}>
      <div style={{ position: 'relative' }}>
        <div style={{
          width: '48px',
          height: '48px',
          borderRadius: '50%',
          border: '4px solid #F9F5FF'
        }} />
        <Loader2 style={{
          position: 'absolute',
          inset: 0,
          width: '48px',
          height: '48px',
          color: '#6941C6',
          animation: 'spin 1s linear infinite'
        }} />
      </div>
      <p style={{ marginTop: '16px', fontSize: '14px', color: '#6b7280' }}>{message}</p>
    </div>
  );
}

export function AnalyzingState() {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      padding: '16px',
      borderRadius: '8px',
      backgroundColor: '#F9F5FF',
      border: '1px solid #E9D7FE'
    }}>
      <Loader2 style={{ width: '20px', height: '20px', color: '#6941C6', animation: 'spin 1s linear infinite' }} />
      <div>
        <p style={{ fontSize: '14px', fontWeight: '500', color: '#6941C6', margin: 0 }}>Analyzing email...</p>
        <p style={{ fontSize: '12px', color: '#7F56D9', margin: 0 }}>This may take a few seconds</p>
      </div>
    </div>
  );
}

export function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '48px 16px',
      textAlign: 'center'
    }}>
      <div style={{
        width: '64px',
        height: '64px',
        borderRadius: '50%',
        backgroundColor: '#f3f4f6',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: '16px'
      }}>
        <FileText style={{ width: '32px', height: '32px', color: '#9ca3af' }} />
      </div>
      <h3 style={{ fontSize: '14px', fontWeight: '600', color: '#101828', margin: '0 0 4px' }}>{title}</h3>
      <p style={{ fontSize: '12px', color: '#6b7280', maxWidth: '200px', margin: 0 }}>{description}</p>
    </div>
  );
}

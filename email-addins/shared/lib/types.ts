export interface User {
  id: string;
  email: string;
  full_name: string;
  enterprise_id?: string;
  profile_picture?: string;
}

export interface StrategicProfile {
  id: string;
  name: string;
  description?: string;
  writing_tone?: string;
  profile_type: 'personal' | 'company';
}

export interface AnalysisViolation {
  type: string;
  severity: 'high' | 'medium' | 'low';
  description: string;
  suggestion?: string;
}

export interface AnalysisResult {
  compliance_score: number;
  cultural_sensitivity_score: number;
  accuracy_score: number;
  overall_score: number;
  detailed_analysis: string;
  violations: AnalysisViolation[];
  recommendations: string[];
}

export interface EmailContent {
  subject: string;
  body: string;
}

export interface AnalysisRequest {
  content: string;
  user_id: string;
  profile_id?: string;
  source: 'gmail' | 'outlook' | 'web' | 'extension';
  metadata?: {
    email_subject?: string;
    platform?: string;
  };
}

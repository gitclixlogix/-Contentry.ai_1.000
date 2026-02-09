import { API_BASE_URL, STORAGE_KEYS } from './config';

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

class ContentryAPI {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  private async getAuthHeaders(): Promise<Record<string, string>> {
    const result = await chrome.storage.local.get([STORAGE_KEYS.USER_DATA]);
    const userData = result[STORAGE_KEYS.USER_DATA];
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    if (userData?.id) {
      headers['X-User-ID'] = userData.id;
    }
    
    return headers;
  }

  async isAuthenticated(): Promise<boolean> {
    const result = await chrome.storage.local.get([STORAGE_KEYS.USER_DATA]);
    return !!result[STORAGE_KEYS.USER_DATA]?.id;
  }

  async getUser(): Promise<User | null> {
    const result = await chrome.storage.local.get([STORAGE_KEYS.USER_DATA]);
    return result[STORAGE_KEYS.USER_DATA] || null;
  }

  async saveUser(user: User): Promise<void> {
    await chrome.storage.local.set({ [STORAGE_KEYS.USER_DATA]: user });
  }

  async clearAuth(): Promise<void> {
    await chrome.storage.local.remove([
      STORAGE_KEYS.USER_DATA,
      STORAGE_KEYS.AUTH_TOKEN,
      STORAGE_KEYS.SELECTED_PROFILE,
    ]);
  }

  async login(email: string, password: string): Promise<{ success: boolean; user?: User; error?: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/auth/extension/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const error = await response.json();
        return { success: false, error: error.detail || 'Login failed' };
      }

      const data = await response.json();
      if (data.success && data.user) {
        await this.saveUser(data.user);
        return { success: true, user: data.user };
      }

      return { success: false, error: 'Login failed' };
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: 'Connection failed. Please try again.' };
    }
  }

  async getStrategicProfiles(): Promise<StrategicProfile[]> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${this.baseUrl}/api/profiles/strategic`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        throw new Error('Failed to fetch profiles');
      }

      const data = await response.json();
      return data.profiles || [];
    } catch (error) {
      console.error('Error fetching profiles:', error);
      return [];
    }
  }

  async analyzeContent(
    content: string,
    profileId?: string
  ): Promise<AnalysisResult | null> {
    try {
      const headers = await this.getAuthHeaders();
      const user = await this.getUser();
      
      if (!user?.id) {
        throw new Error('User not authenticated');
      }

      const response = await fetch(`${this.baseUrl}/api/content/analyze`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          content,
          user_id: user.id,
          profile_id: profileId,
          language: 'en',
        }),
      });

      if (!response.ok) {
        throw new Error('Analysis failed');
      }

      const result = await response.json();
      
      // Parse violations from the response
      const violations: AnalysisViolation[] = [];
      const recommendations: string[] = [];
      
      // Extract violations from detailed_analysis if present
      if (result.detailed_analysis) {
        // Parse any structured violations
        const analysis = result.detailed_analysis;
        
        // Look for compliance violations
        if (result.compliance_score < 80) {
          violations.push({
            type: 'Compliance',
            severity: result.compliance_score < 50 ? 'high' : 'medium',
            description: 'Content may not fully comply with brand guidelines',
            suggestion: 'Review against your brand guidelines'
          });
        }
        
        // Look for cultural sensitivity issues
        if (result.cultural_sensitivity_score < 80) {
          violations.push({
            type: 'Cultural Sensitivity',
            severity: result.cultural_sensitivity_score < 50 ? 'high' : 'medium',
            description: 'Content may need cultural sensitivity review',
            suggestion: 'Consider your target audience diversity'
          });
        }
        
        // Look for accuracy issues
        if (result.accuracy_score < 80) {
          violations.push({
            type: 'Accuracy',
            severity: result.accuracy_score < 50 ? 'high' : 'medium',
            description: 'Some claims may need verification',
            suggestion: 'Verify factual claims and statistics'
          });
        }
      }
      
      // Extract recommendations from detailed_analysis
      if (result.detailed_analysis) {
        recommendations.push('Review the detailed analysis for specific improvement suggestions');
      }
      
      if (result.overall_score < 70) {
        recommendations.push('Consider revising content to improve overall score');
      }

      return {
        ...result,
        violations,
        recommendations,
      };
    } catch (error) {
      console.error('Error analyzing content:', error);
      return null;
    }
  }

  async getSelectedProfile(): Promise<string | null> {
    const result = await chrome.storage.local.get([STORAGE_KEYS.SELECTED_PROFILE]);
    return result[STORAGE_KEYS.SELECTED_PROFILE] || null;
  }

  async setSelectedProfile(profileId: string): Promise<void> {
    await chrome.storage.local.set({ [STORAGE_KEYS.SELECTED_PROFILE]: profileId });
  }

  getLoginUrl(): string {
    return `${this.baseUrl}/contentry/auth?extension=true&callback=extension`;
  }
}

export const api = new ContentryAPI();

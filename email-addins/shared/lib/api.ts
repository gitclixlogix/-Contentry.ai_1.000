import { getApiBaseUrl, STORAGE_KEYS } from './config';
import type { User, StrategicProfile, AnalysisResult, AnalysisRequest, AnalysisViolation } from './types';

class ContentryAPI {
  private getBaseUrl(): string {
    return getApiBaseUrl();
  }

  private getStoredUser(): User | null {
    try {
      const stored = localStorage.getItem(STORAGE_KEYS.USER_DATA);
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  }

  private getAuthHeaders(): Record<string, string> {
    const user = this.getStoredUser();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (user?.id) {
      headers['X-User-ID'] = user.id;
    }
    return headers;
  }

  async isAuthenticated(): Promise<boolean> {
    return !!this.getStoredUser()?.id;
  }

  async getUser(): Promise<User | null> {
    return this.getStoredUser();
  }

  async saveUser(user: User): Promise<void> {
    localStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(user));
  }

  async clearAuth(): Promise<void> {
    localStorage.removeItem(STORAGE_KEYS.USER_DATA);
    localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.SELECTED_PROFILE);
  }

  async login(email: string, password: string): Promise<{ success: boolean; user?: User; error?: string }> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/auth/extension/login`, {
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
      const response = await fetch(`${this.getBaseUrl()}/api/profiles/strategic`, {
        method: 'GET',
        headers: this.getAuthHeaders(),
      });

      if (!response.ok) throw new Error('Failed to fetch profiles');
      const data = await response.json();
      return data.profiles || [];
    } catch (error) {
      console.error('Error fetching profiles:', error);
      return [];
    }
  }

  async analyzeContent(
    content: string,
    profileId?: string,
    source: 'gmail' | 'outlook' | 'extension' = 'extension',
    metadata?: { email_subject?: string }
  ): Promise<AnalysisResult | null> {
    try {
      const user = this.getStoredUser();
      if (!user?.id) throw new Error('User not authenticated');

      const response = await fetch(`${this.getBaseUrl()}/api/content/analyze`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({
          content,
          user_id: user.id,
          profile_id: profileId,
          language: 'en',
          source,
          metadata,
        }),
      });

      if (!response.ok) throw new Error('Analysis failed');
      const result = await response.json();

      // Parse violations from response
      const violations: AnalysisViolation[] = [];
      const recommendations: string[] = [];

      if (result.compliance_score < 80) {
        violations.push({
          type: 'Compliance',
          severity: result.compliance_score < 50 ? 'high' : 'medium',
          description: 'Content may not fully comply with brand guidelines',
          suggestion: 'Review against your brand guidelines'
        });
      }

      if (result.cultural_sensitivity_score < 80) {
        violations.push({
          type: 'Cultural Sensitivity',
          severity: result.cultural_sensitivity_score < 50 ? 'high' : 'medium',
          description: 'Content may need cultural sensitivity review',
          suggestion: 'Consider your target audience diversity'
        });
      }

      if (result.accuracy_score < 80) {
        violations.push({
          type: 'Accuracy',
          severity: result.accuracy_score < 50 ? 'high' : 'medium',
          description: 'Some claims may need verification',
          suggestion: 'Verify factual claims and statistics'
        });
      }

      if (result.overall_score < 70) {
        recommendations.push('Consider revising content to improve overall score');
      }

      return { ...result, violations, recommendations };
    } catch (error) {
      console.error('Error analyzing content:', error);
      return null;
    }
  }

  async getSelectedProfile(): Promise<string | null> {
    return localStorage.getItem(STORAGE_KEYS.SELECTED_PROFILE);
  }

  async setSelectedProfile(profileId: string): Promise<void> {
    localStorage.setItem(STORAGE_KEYS.SELECTED_PROFILE, profileId);
  }
}

export const api = new ContentryAPI();

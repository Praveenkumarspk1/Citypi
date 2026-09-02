export interface User {
  id: string;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
  locale: string;
  timezone: string;
  email_verified: boolean;
  role: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserPreferences {
  interests: string[];
  budget_level: string;
  accessibility_needs: string[];
  dietary_restrictions: string[];
  preferred_transport_modes: string[];
}

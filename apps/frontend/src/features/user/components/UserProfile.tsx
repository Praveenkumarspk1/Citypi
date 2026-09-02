// UserProfile Component
// User profile display and editing

import { useState } from 'react';
import { 
  User as UserIcon, 
  Mail, 
  Calendar, 
  CreditCard, 
  Shield, 
  Globe, 
  Edit2,
  Save,
  X,
  Camera,
  Layers,
  Settings,
  LogOut,
} from 'lucide-react';
import { useCurrentUser, useUpdateUser } from '@shared/hooks/useApi';
import type { User, TransportMode } from '@shared/types';

interface UserProfileProps {
  onLogout?: () => void;
  className?: string;
}

export function UserProfile({ onLogout, className = '' }: UserProfileProps) {
  const { data: user, isLoading, error } = useCurrentUser();
  const updateProfileMutation = useUpdateUser();
  
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    display_name: '',
    email: '',
    locale: 'en',
    timezone: 'UTC',
    interests: [] as string[],
    budget_level: 'mid_range' as 'budget' | 'mid_range' | 'luxury',
    accessibility_needs: [] as string[],
    dietary_restrictions: [] as string[],
    preferred_transport_modes: [] as TransportMode[],
  });
  
  const [activeTab, setActiveTab] = useState<'profile' | 'preferences' | 'trips' | 'settings'>('profile');
  
  // Initialize form data when user loads
  useState(() => {
    if (user) {
      setFormData({
        display_name: user.display_name,
        email: user.email,
        locale: user.locale,
        timezone: user.timezone,
        interests: user.interests,
        budget_level: user.budget_level,
        accessibility_needs: user.accessibility_needs,
        dietary_restrictions: user.dietary_restrictions,
        preferred_transport_modes: user.preferred_transport_modes,
      });
    }
  });
  
  const handleSave = async () => {
    try {
      await updateProfileMutation.mutateAsync(formData);
      setIsEditing(false);
    } catch (err) {
      console.error('Failed to update profile:', err);
    }
  };
  
  const handleCancel = () => {
    if (user) {
      setFormData({
        display_name: user.display_name,
        email: user.email,
        locale: user.locale,
        timezone: user.timezone,
        interests: user.interests,
        budget_level: user.budget_level,
        accessibility_needs: user.accessibility_needs,
        dietary_restrictions: user.dietary_restrictions,
        preferred_transport_modes: user.preferred_transport_modes,
      });
    }
    setIsEditing(false);
  };
  
  const toggleInterest = (interest: string) => {
    setFormData(prev => ({
      ...prev,
      interests: prev.interests.includes(interest)
        ? prev.interests.filter(i => i !== interest)
        : [...prev.interests, interest],
    }));
  };
  
  const toggleTransportMode = (mode: TransportMode) => {
    setFormData(prev => ({
      ...prev,
      preferred_transport_modes: prev.preferred_transport_modes.includes(mode)
        ? prev.preferred_transport_modes.filter(m => m !== mode)
        : [...prev.preferred_transport_modes, mode],
    }));
  };
  
  const addCustomItem = (field: 'accessibility_needs' | 'dietary_restrictions', value: string) => {
    if (!value.trim()) return;
    setFormData(prev => ({
      ...prev,
      [field]: [...prev[field], value.trim()],
    }));
  };
  
  const removeCustomItem = (field: 'accessibility_needs' | 'dietary_restrictions', value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: prev[field].filter(item => item !== value),
    }));
  };
  
  if (isLoading) {
    return (
      <div className={`card p-8 text-center ${className}`}>
        <div className="w-8 h-8 animate-spin mx-auto border-2 border-primary-600 border-t-transparent rounded-full mb-4" />
        <p className="text-gray-500">Loading profile...</p>
      </div>
    );
  }
  
  if (error || !user) {
    return (
      <div className={`card p-8 text-center ${className}`}>
        <UserIcon className="w-12 h-12 mx-auto text-gray-300 mb-4" />
        <p className="text-gray-500">Unable to load profile</p>
      </div>
    );
  }
  
  const commonInterests = [
    'museums', 'parks', 'restaurants', 'shopping', 'nightlife',
    'history', 'art', 'architecture', 'nature', 'photography',
    'food', 'wine', 'beer', 'coffee', 'music', 'theater',
    'sports', 'hiking', 'cycling', 'beaches', 'markets',
  ];
  
  const transportModes: TransportMode[] = [
    'walking', 'cycling', 'transit', 'driving', 'rideshare', 'scooter', 'wheelchair'
  ];
  
  const budgetLevels = [
    { value: 'budget', label: 'Budget', icon: <DollarSign className="w-4 h-4" /> },
    { value: 'mid_range', label: 'Mid Range', icon: <CreditCard className="w-4 h-4" /> },
    { value: 'luxury', label: 'Luxury', icon: <Crown className="w-4 h-4" /> },
  ];
  
  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Header */}
      <div className="card p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="w-20 h-20 rounded-full bg-primary-100 flex items-center justify-center overflow-hidden">
                {user.avatar_url ? (
                  <img src={user.avatar_url} alt={user.display_name} className="w-full h-full object-cover" />
                ) : (
                  <UserIcon className="w-10 h-10 text-primary-600" />
                )}
              </div>
              {isEditing && (
                <label className="absolute bottom-0 right-0 w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center cursor-pointer">
                  <Camera className="w-4 h-4 text-white" />
                  <input type="file" accept="image/*" className="absolute inset-0 opacity-0 cursor-pointer" />
                </label>
              )}
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">{user.display_name}</h2>
              <p className="text-sm text-gray-500">@{user.email.split('@')[0]}</p>
              <div className="flex items-center gap-2 mt-1">
                <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                  user.role === 'premium' ? 'bg-yellow-100 text-yellow-700' :
                  user.role === 'admin' ? 'bg-purple-100 text-purple-700' :
                  'bg-gray-100 text-gray-700'
                }`}>
                  {user.role}
                </span>
                <span className={`w-2 h-2 rounded-full ${user.status === 'active' ? 'bg-green-500' : 'bg-gray-400'}`} />
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {isEditing ? (
              <>
                <button onClick={handleCancel} className="btn-outline">Cancel</button>
                <button onClick={handleSave} className="btn-primary" disabled={updateProfileMutation.isPending}>
                  <Save className="w-4 h-4 mr-1" /> Save
                </button>
              </>
            ) : (
              <button onClick={() => setIsEditing(true)} className="btn-outline flex items-center gap-2">
                <Edit2 className="w-4 h-4" />
                Edit Profile
              </button>
            )}
          </div>
        </div>
      </div>
      
      {/* Tab Navigation */}
      <div className="card border-b border-gray-200">
        <nav className="flex overflow-x-auto px-4" aria-label="Profile tabs">
          {[
            { id: 'profile', label: 'Profile', icon: <UserIcon className="w-4 h-4" /> },
            { id: 'preferences', label: 'Preferences', icon: <Settings className="w-4 h-4" /> },
            { id: 'trips', label: 'My Trips', icon: <Layers className="w-4 h-4" /> },
            { id: 'settings', label: 'Settings', icon: <Shield className="w-4 h-4" /> },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex-shrink-0 px-4 py-3 border-b-2 font-medium text-sm transition-colors flex items-center gap-2 ${
                activeTab === tab.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </nav>
      </div>
      
      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'profile' && (
          <ProfileTab user={user} isEditing={isEditing} formData={formData} setFormData={setFormData} />
        )}
        
        {activeTab === 'preferences' && (
          <PreferencesTab 
            formData={formData} 
            setFormData={setFormData}
            commonInterests={commonInterests}
            transportModes={transportModes}
            budgetLevels={budgetLevels}
            toggleInterest={toggleInterest}
            toggleTransportMode={toggleTransportMode}
            addCustomItem={addCustomItem}
            removeCustomItem={removeCustomItem}
            isEditing={isEditing}
          />
        )}
        
        {activeTab === 'trips' && (
          <TripsTab />
        )}
        
        {activeTab === 'settings' && (
          <SettingsTab onLogout={onLogout} />
        )}
      </div>
    </div>
  );
}

// Profile Tab
interface ProfileTabProps {
  user: User;
  isEditing: boolean;
  formData: any;
  setFormData: React.Dispatch<React.SetStateAction<any>>;
}

function ProfileTab({ user, isEditing, formData, setFormData }: ProfileTabProps) {
  return (
    <div className="p-6 space-y-6">
      <div className="grid gap-6 md:grid-cols-2">
        <div>
          <h3 className="font-medium text-gray-900 mb-4">Basic Information</h3>
          <div className="space-y-4">
            <FormField label="Display Name" icon={<UserIcon className="w-4 h-4" />}>
              {isEditing ? (
                <input
                  type="text"
                  value={formData.display_name}
                  onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                  className="input"
                />
              ) : (
                <p className="text-gray-900">{user.display_name}</p>
              )}
            </FormField>
            
            <FormField label="Email" icon={<Mail className="w-4 h-4" />}>
              {isEditing ? (
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="input"
                />
              ) : (
                <p className="text-gray-900">{user.email}</p>
              )}
            </FormField>
            
            <FormField label="Locale" icon={<Globe className="w-4 h-4" />}>
              {isEditing ? (
                <select
                  value={formData.locale}
                  onChange={(e) => setFormData({ ...formData, locale: e.target.value })}
                  className="input"
                >
                  <option value="en">English</option>
                  <option value="es">Spanish</option>
                  <option value="fr">French</option>
                  <option value="de">German</option>
                  <option value="zh">Chinese</option>
                  <option value="ja">Japanese</option>
                </select>
              ) : (
                <p className="text-gray-900">{user.locale.toUpperCase()}</p>
              )}
            </FormField>
            
            <FormField label="Timezone" icon={<Clock className="w-4 h-4" />}>
              {isEditing ? (
                <select
                  value={formData.timezone}
                  onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
                  className="input"
                >
                  <option value="UTC">UTC</option>
                  <option value="America/New_York">Eastern Time</option>
                  <option value="America/Chicago">Central Time</option>
                  <option value="America/Denver">Mountain Time</option>
                  <option value="America/Los_Angeles">Pacific Time</option>
                  <option value="Europe/London">London</option>
                  <option value="Europe/Paris">Paris</option>
                  <option value="Asia/Tokyo">Tokyo</option>
                </select>
              ) : (
                <p className="text-gray-900">{user.timezone}</p>
              )}
            </FormField>
          </div>
        </div>
        
        <div>
          <h3 className="font-medium text-gray-900 mb-4">Account Details</h3>
          <div className="space-y-4">
            <InfoRow label="Member since" value={new Date(user.created_at).toLocaleDateString()} icon={<Calendar className="w-4 h-4" />} />
            <InfoRow label="Last login" value={user.last_login_at ? new Date(user.last_login_at).toLocaleDateString() : 'Never'} icon={<Clock className="w-4 h-4" />} />
            <InfoRow label="Email verified" value={user.email_verified ? 'Yes' : 'No'} icon={<Shield className="w-4 h-4" />} />
            <InfoRow label="Status" value={user.status} icon={<UserIcon className="w-4 h-4" />} />
          </div>
        </div>
      </div>
    </div>
  );
}

// Preferences Tab
type UserCustomField = 'accessibility_needs' | 'dietary_restrictions';

interface PreferencesTabProps {
  formData: any;
  setFormData: React.Dispatch<React.SetStateAction<any>>;
  commonInterests: string[];
  transportModes: TransportMode[];
  budgetLevels: any[];
  toggleInterest: (interest: string) => void;
  toggleTransportMode: (mode: TransportMode) => void;
  addCustomItem: (field: UserCustomField, value: string) => void;
  removeCustomItem: (field: UserCustomField, value: string) => void;
  isEditing: boolean;
}

function PreferencesTab({ 
  formData, 
  setFormData, 
  commonInterests, 
  transportModes, 
  budgetLevels,
  toggleInterest, 
  toggleTransportMode, 
  addCustomItem, 
  removeCustomItem,
  isEditing 
}: PreferencesTabProps) {
  const [newAccessibility, setNewAccessibility] = useState('');
  const [newDietary, setNewDietary] = useState('');
  
  return (
    <div className="p-6 space-y-8">
      {/* Budget Level */}
      <div>
        <h3 className="font-medium text-gray-900 mb-4">Budget Level</h3>
        <div className="grid grid-cols-3 gap-4">
          {budgetLevels.map(level => (
            <button
              key={level.value}
              onClick={() => setFormData({ ...formData, budget_level: level.value })}
              disabled={!isEditing}
              className={`p-4 rounded-lg border-2 text-center transition-all ${
                formData.budget_level === level.value
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className={`mx-auto mb-2 ${formData.budget_level === level.value ? 'text-primary-600' : 'text-gray-400'}`}>
                {level.icon}
              </div>
              <p className="font-medium text-gray-900">{level.label}</p>
            </button>
          ))}
        </div>
      </div>
      
      {/* Interests */}
      <div>
        <h3 className="font-medium text-gray-900 mb-4">Interests</h3>
        <div className="flex flex-wrap gap-2">
          {commonInterests.map(interest => (
            <button
              key={interest}
              onClick={() => toggleInterest(interest)}
              disabled={!isEditing}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                formData.interests.includes(interest)
                  ? 'bg-primary-100 text-primary-700'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {interest.charAt(0).toUpperCase() + interest.slice(1)}
            </button>
          ))}
        </div>
      </div>
      
      {/* Transport Modes */}
      <div>
        <h3 className="font-medium text-gray-900 mb-4">Preferred Transport</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {transportModes.map(mode => (
            <label key={mode} className="flex items-center gap-2 cursor-pointer p-3 rounded-lg border hover:bg-gray-50">
              <input
                type="checkbox"
                checked={formData.preferred_transport_modes.includes(mode)}
                onChange={() => toggleTransportMode(mode)}
                disabled={!isEditing}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="capitalize">{mode}</span>
            </label>
          ))}
        </div>
      </div>
      
      {/* Accessibility Needs */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-medium text-gray-900">Accessibility Needs</h3>
          {isEditing && (
            <div className="flex gap-2">
              <input
                type="text"
                value={newAccessibility}
                onChange={(e) => setNewAccessibility(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && (addCustomItem('accessibility_needs', newAccessibility), setNewAccessibility(''))}
                placeholder="Add custom need..."
                className="input w-48"
              />
            </div>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          {formData.accessibility_needs.map((need: string) => (
            <span key={need} className="inline-flex items-center gap-1 px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm">
              {need}
              {isEditing && (
                <button onClick={() => removeCustomItem('accessibility_needs', need)} className="ml-1 hover:text-blue-500">
                  <X className="w-3 h-3" />
                </button>
              )}
            </span>
          ))}
        </div>
      </div>
      
      {/* Dietary Restrictions */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-medium text-gray-900">Dietary Restrictions</h3>
          {isEditing && (
            <div className="flex gap-2">
              <input
                type="text"
                value={newDietary}
                onChange={(e) => setNewDietary(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && (addCustomItem('dietary_restrictions', newDietary), setNewDietary(''))}
                placeholder="Add restriction..."
                className="input w-48"
              />
            </div>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          {formData.dietary_restrictions.map((restriction: string) => (
            <span key={restriction} className="inline-flex items-center gap-1 px-3 py-1 bg-green-50 text-green-700 rounded-full text-sm">
              {restriction}
              {isEditing && (
                <button onClick={() => removeCustomItem('dietary_restrictions', restriction)} className="ml-1 hover:text-green-500">
                  <X className="w-3 h-3" />
                </button>
              )}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

// Trips Tab
function TripsTab(): JSX.Element {
  return (
    <div className="p-6">
      <div className="card p-8 text-center">
        <Layers className="w-12 h-12 mx-auto text-gray-300 mb-4" />
        <h3 className="font-medium text-gray-900 mb-2">Your Trips</h3>
        <p className="text-gray-500 mb-4">Your saved itineraries and trip history will appear here.</p>
        <button className="btn-primary">Create New Trip</button>
      </div>
    </div>
  );
}

// Settings Tab
interface SettingsTabProps {
  onLogout?: () => void;
}

function SettingsTab({ onLogout }: SettingsTabProps) {
  return (
    <div className="p-6 space-y-6">
      <div className="card p-4">
        <h3 className="font-medium text-gray-900 mb-4">Account Settings</h3>
        <div className="space-y-4">
          <SettingsRow 
            label="Change Password" 
            description="Update your account password"
            action={<button className="btn-outline">Change</button>}
          />
          <SettingsRow 
            label="Two-Factor Authentication" 
            description="Add an extra layer of security"
            action={<span className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded">Enabled</span>}
          />
          <SettingsRow 
            label="Connected Accounts" 
            description="Manage linked services"
            action={<button className="btn-outline">Manage</button>}
          />
        </div>
      </div>
      
      <div className="card p-4">
        <h3 className="font-medium text-gray-900 mb-4">Notifications</h3>
        <div className="space-y-4">
          <SettingsRow 
            label="Email Notifications" 
            description="Receive updates via email"
            action={<input type="checkbox" defaultChecked className="rounded border-gray-300 text-primary-600" />}
          />
          <SettingsRow 
            label="Push Notifications" 
            description="Receive updates on your device"
            action={<input type="checkbox" defaultChecked className="rounded border-gray-300 text-primary-600" />}
          />
          <SettingsRow 
            label="Trip Reminders" 
            description="Get reminded about upcoming trips"
            action={<input type="checkbox" className="rounded border-gray-300 text-primary-600" />}
          />
        </div>
      </div>
      
      <div className="card p-4 border-red-200 bg-red-50">
        <h3 className="font-medium text-red-900 mb-4">Danger Zone</h3>
        <div className="space-y-4">
          <SettingsRow 
            label="Delete Account" 
            description="Permanently delete your account and all data"
            action={<button className="btn-outline text-red-600 hover:bg-red-50">Delete Account</button>}
          />
        </div>
      </div>
      
      {onLogout && (
        <button onClick={onLogout} className="btn-outline text-red-600 hover:bg-red-50 w-full">
          <LogOut className="w-4 h-4 mr-2" />
          Sign Out
        </button>
      )}
    </div>
  );
}

// Helper Components
function FormField({ label, icon, children }: { label: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div>
      <label className="label flex items-center gap-2">
        {icon}
        {label}
      </label>
      {children}
    </div>
  );
}

function InfoRow({ label, value, icon }: { label: string; value: string; icon: React.ReactNode }) {
  return (
    <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
      <div className="w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center text-gray-500">
        {icon}
      </div>
      <div className="flex-1">
        <p className="text-sm text-gray-500">{label}</p>
        <p className="font-medium text-gray-900">{value}</p>
      </div>
    </div>
  );
}

function SettingsRow({ label, description, action }: { label: string; description: string; action: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <p className="font-medium text-gray-900">{label}</p>
        <p className="text-sm text-gray-500">{description}</p>
      </div>
      <div>{action}</div>
    </div>
  );
}

// Missing imports
import { Clock, DollarSign, Crown } from 'lucide-react';
import { User, Shield, Edit, Camera, Bell, Key } from 'lucide-react';
import { useState } from 'react';
import { useAuthStore } from '@shared/stores/authStore';
import type { User as UserType } from '@shared/types';

const mockUser: UserType = {
  id: '1',
  email: 'john.doe@example.com',
  display_name: 'John Doe',
  avatar_url: undefined,
  locale: 'en',
  timezone: 'America/New_York',
  interests: ['museums', 'food', 'parks', 'history'],
  budget_level: 'mid_range',
  accessibility_needs: [],
  dietary_restrictions: ['vegetarian'],
  preferred_transport_modes: ['walking', 'transit'],
  role: 'user',
  status: 'active',
  email_verified: true,
  created_at: '2024-01-15T10:00:00Z',
  updated_at: '2024-01-20T15:30:00Z',
  last_login_at: '2024-01-25T08:00:00Z',
};

const budgetOptions = ['budget', 'mid_range', 'luxury'] as const;
const transportModes = ['walking', 'cycling', 'transit', 'driving', 'rideshare', 'scooter', 'wheelchair'] as const;
const locales = ['en', 'es', 'fr', 'de', 'zh', 'ja', 'ko'] as const;

export function ProfilePage() {
  const { updateUser } = useAuthStore();
  const [activeTab, setActiveTab] = useState<'profile' | 'preferences' | 'security' | 'notifications'>('profile');
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    display_name: mockUser.display_name,
    email: mockUser.email,
    locale: mockUser.locale,
    timezone: mockUser.timezone,
    budget_level: mockUser.budget_level,
    interests: mockUser.interests.join(', '),
    dietary_restrictions: mockUser.dietary_restrictions.join(', '),
    accessibility_needs: mockUser.accessibility_needs.join(', '),
    preferred_transport_modes: mockUser.preferred_transport_modes.join(', '),
  });

  const handleSave = () => {
    const updatedUser = {
      ...mockUser,
      display_name: formData.display_name,
      email: formData.email,
      locale: formData.locale,
      timezone: formData.timezone,
      budget_level: formData.budget_level,
      interests: formData.interests.split(',').map(s => s.trim()).filter(Boolean),
      dietary_restrictions: formData.dietary_restrictions.split(',').map(s => s.trim()).filter(Boolean),
      accessibility_needs: formData.accessibility_needs.split(',').map(s => s.trim()).filter(Boolean),
      preferred_transport_modes: formData.preferred_transport_modes.split(',').map(s => s.trim()).filter(Boolean) as any,
    };
    updateUser(updatedUser);
    setIsEditing(false);
  };

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'preferences', label: 'Preferences', icon: Shield },
    { id: 'security', label: 'Security', icon: Key },
    { id: 'notifications', label: 'Notifications', icon: Bell },
  ];

  return (
    <div className="space-y-6">
      {/* Profile Header */}
      <div className="card p-6">
        <div className="flex flex-col lg:flex-row lg:items-center gap-6">
          <div className="relative">
            <div className="w-24 h-24 rounded-full bg-primary-100 flex items-center justify-center">
              {mockUser.avatar_url ? (
                <img src={mockUser.avatar_url} alt={mockUser.display_name} className="w-24 h-24 rounded-full" />
              ) : (
                <span className="text-3xl font-bold text-primary-700">
                  {mockUser.display_name.charAt(0)}
                </span>
              )}
            </div>
            {isEditing && (
              <button className="absolute bottom-0 right-0 w-8 h-8 rounded-full bg-primary-600 text-white flex items-center justify-center">
                <Camera className="w-4 h-4" />
              </button>
            )}
          </div>
          
          <div className="flex-1 text-center lg:text-left">
            <div className="flex items-center justify-center lg:justify-start gap-3 mb-2">
              <h1 className="text-2xl font-bold text-gray-900">{mockUser.display_name}</h1>
              {mockUser.email_verified && (
                <span className="badge badge-success flex items-center gap-1">
                  <Shield className="w-3 h-3" />
                  Verified
                </span>
              )}
            </div>
            <p className="text-gray-500">{mockUser.email}</p>
            <p className="text-sm text-gray-400 mt-1">
              Member since {new Date(mockUser.created_at).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
            </p>
          </div>
          
          <div className="flex items-center gap-2 lg:ml-auto">
            <button
              onClick={() => setIsEditing(!isEditing)}
              className={isEditing ? 'btn-primary' : 'btn-outline'}
            >
              {isEditing ? (
                <>
                  <Edit className="w-4 h-4 mr-2" />
                  Save
                </>
              ) : (
                <>
                  <Edit className="w-4 h-4 mr-2" />
                  Edit Profile
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="card">
        <div className="border-b border-gray-200">
          <nav className="flex gap-1 p-1" aria-label="Profile sections">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'profile' && (
            <div className="space-y-6 max-w-2xl">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="label">Display Name</label>
                  {isEditing ? (
                    <input
                      value={formData.display_name}
                      onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                      className="input"
                    />
                  ) : (
                    <p className="text-gray-900">{mockUser.display_name}</p>
                  )}
                </div>
                <div>
                  <label className="label">Email</label>
                  {isEditing ? (
                    <input
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      className="input"
                      type="email"
                    />
                  ) : (
                    <p className="text-gray-900">{mockUser.email}</p>
                  )}
                </div>
                <div>
                  <label className="label">Language</label>
                  {isEditing ? (
                    <select
                      value={formData.locale}
                      onChange={(e) => setFormData({ ...formData, locale: e.target.value })}
                      className="input"
                    >
                      {locales.map(locale => (
                        <option key={locale} value={locale}>{locale.toUpperCase()}</option>
                      ))}
                    </select>
                  ) : (
                    <p className="text-gray-900 capitalize">{mockUser.locale}</p>
                  )}
                </div>
                <div>
                  <label className="label">Timezone</label>
                  {isEditing ? (
                    <input
                      value={formData.timezone}
                      onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
                      className="input"
                    />
                  ) : (
                    <p className="text-gray-900">{mockUser.timezone}</p>
                  )}
                </div>
              </div>

              <div>
                <label className="label">Interests</label>
                {isEditing ? (
                  <input
                    value={formData.interests}
                    onChange={(e) => setFormData({ ...formData, interests: e.target.value })}
                    className="input"
                    placeholder="museums, food, parks, history"
                  />
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {mockUser.interests.map((interest) => (
                      <span key={interest} className="badge badge-primary">{interest}</span>
                    ))}
                  </div>
                )}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="label">Dietary Restrictions</label>
                  {isEditing ? (
                    <input
                      value={formData.dietary_restrictions}
                      onChange={(e) => setFormData({ ...formData, dietary_restrictions: e.target.value })}
                      className="input"
                      placeholder="vegetarian, gluten-free"
                    />
                  ) : (
                    <div className="flex flex-wrap gap-2">
                      {mockUser.dietary_restrictions.map((restriction) => (
                        <span key={restriction} className="badge badge-secondary">{restriction}</span>
                      ))}
                    </div>
                  )}
                </div>
                <div>
                  <label className="label">Accessibility Needs</label>
                  {isEditing ? (
                    <input
                      value={formData.accessibility_needs}
                      onChange={(e) => setFormData({ ...formData, accessibility_needs: e.target.value })}
                      className="input"
                      placeholder="wheelchair, screen reader"
                    />
                  ) : (
                    <div className="flex flex-wrap gap-2">
                      {mockUser.accessibility_needs.map((need) => (
                        <span key={need} className="badge badge-secondary">{need}</span>
                      ))}
                      {mockUser.accessibility_needs.length === 0 && (
                        <span className="text-gray-400 text-sm">None specified</span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'preferences' && (
            <div className="space-y-6 max-w-2xl">
              <div>
                <label className="label">Budget Level</label>
                <div className="grid grid-cols-3 gap-3">
                  {budgetOptions.map((level) => (
                    <button
                      key={level}
                      onClick={() => setFormData({ ...formData, budget_level: level })}
                      className={`p-4 rounded-xl border-2 text-center transition-all ${
                        formData.budget_level === level
                          ? 'border-primary-500 bg-primary-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <p className="font-medium capitalize text-gray-900">{level.replace('_', ' ')}</p>
                      <p className="text-sm text-gray-500 mt-1">
                        {level === 'budget' ? '$' : level === 'mid_range' ? '$$' : '$$$'}
                      </p>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="label">Preferred Transport Modes</label>
                <div className="flex flex-wrap gap-2">
                  {transportModes.map((mode) => {
                    const isSelected = formData.preferred_transport_modes.split(',').map(s => s.trim()).includes(mode);
                    return (
                      <button
                        key={mode}
                        onClick={() => {
                          const modes = formData.preferred_transport_modes.split(',').map(s => s.trim()).filter(Boolean);
                          const index = modes.indexOf(mode);
                          if (index > -1) {
                            modes.splice(index, 1);
                          } else {
                            modes.push(mode);
                          }
                          setFormData({ ...formData, preferred_transport_modes: modes.join(', ') });
                        }}
                        className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                          isSelected
                            ? 'bg-primary-100 text-primary-700'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        {mode.charAt(0).toUpperCase() + mode.slice(1)}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="space-y-6 max-w-2xl">
              <div className="p-4 bg-gray-50 rounded-xl">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-gray-900">Two-Factor Authentication</h3>
                    <p className="text-sm text-gray-500">Add an extra layer of security to your account</p>
                  </div>
                  <button className="btn-outline btn-sm">Enable</button>
                </div>
              </div>
              <div className="p-4 bg-gray-50 rounded-xl">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-gray-900">Change Password</h3>
                    <p className="text-sm text-gray-500">Last changed 30 days ago</p>
                  </div>
                  <button className="btn-outline btn-sm">Change</button>
                </div>
              </div>
              <div className="p-4 bg-gray-50 rounded-xl">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-gray-900">Active Sessions</h3>
                    <p className="text-sm text-gray-500">Manage your logged-in devices</p>
                  </div>
                  <button className="btn-outline btn-sm">View</button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="space-y-4 max-w-2xl">
              {[
                { title: 'Trip Reminders', desc: 'Get notified about upcoming trips', enabled: true },
                { title: 'Weather Alerts', desc: 'Severe weather warnings for your trips', enabled: true },
                { title: 'Transit Updates', desc: 'Real-time transit delays and changes', enabled: false },
                { title: 'New Recommendations', desc: 'Personalized place suggestions', enabled: true },
                { title: 'Marketing Emails', desc: 'News, tips, and special offers', enabled: false },
              ].map((notification) => (
                <div key={notification.title} className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                  <div>
                    <h3 className="font-medium text-gray-900">{notification.title}</h3>
                    <p className="text-sm text-gray-500">{notification.desc}</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" defaultChecked={notification.enabled} className="sr-only peer" />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                  </label>
                </div>
              ))}
            </div>
          )}

          {isEditing && activeTab === 'profile' && (
            <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
              <button onClick={() => setIsEditing(false)} className="btn-outline">Cancel</button>
              <button onClick={handleSave} className="btn-primary">Save Changes</button>
            </div>
          )}
        </div>
      </div>

      {/* Account Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="card p-4 text-center">
          <p className="text-3xl font-bold text-gray-900">12</p>
          <p className="text-sm text-gray-500">Itineraries Created</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-3xl font-bold text-gray-900">47</p>
          <p className="text-sm text-gray-500">Places Saved</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-3xl font-bold text-gray-900">8</p>
          <p className="text-sm text-gray-500">Cities Explored</p>
        </div>
      </div>
    </div>
  );
}
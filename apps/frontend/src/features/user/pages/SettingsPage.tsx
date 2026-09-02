import { User, Bell, Shield, Palette, Database, Trash2, LogOut, Moon, Sun, Monitor } from 'lucide-react';
import { useState } from 'react';
import { useAuthStore } from '@shared/stores/authStore';

export function SettingsPage() {
  const { logout } = useAuthStore();
  const [activeSection, setActiveSection] = useState<'appearance' | 'notifications' | 'privacy' | 'data' | 'account'>('appearance');
  const [theme, setTheme] = useState<'light' | 'dark' | 'system'>('system');
  const [notifications, setNotifications] = useState({
    email: true,
    push: true,
    tripReminders: true,
    weatherAlerts: true,
    transitUpdates: false,
    recommendations: true,
    marketing: false,
  });
  const [privacy, setPrivacy] = useState({
    profileVisibility: 'private',
    locationSharing: false,
    analytics: true,
    personalizedAds: false,
  });
  const [data, setData] = useState({
    autoSync: true,
    offlineMaps: false,
    dataSaver: false,
  });

  const sections = [
    { id: 'appearance', label: 'Appearance', icon: Palette },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'privacy', label: 'Privacy', icon: Shield },
    { id: 'data', label: 'Data & Storage', icon: Database },
    { id: 'account', label: 'Account', icon: User },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-500 mt-1">Manage your preferences and account settings</p>
      </div>

      <div className="card">
        <div className="border-b border-gray-200">
          <nav className="flex gap-1 p-1" aria-label="Settings sections">
            {sections.map((section) => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id as any)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeSection === section.id
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <section.icon className="w-4 h-4" />
                {section.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6 max-w-3xl">
          {activeSection === 'appearance' && (
            <div className="space-y-8">
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Theme</h2>
                <div className="grid grid-cols-3 gap-4">
                  {[
                    { value: 'light', label: 'Light', icon: Sun, desc: 'Always use light mode' },
                    { value: 'dark', label: 'Dark', icon: Moon, desc: 'Always use dark mode' },
                    { value: 'system', label: 'System', icon: Monitor, desc: 'Match system preference' },
                  ].map((option) => (
                    <button
                      key={option.value}
                      onClick={() => setTheme(option.value as 'light' | 'dark' | 'system')}
                      className={`p-4 rounded-xl border-2 text-center transition-all ${
                        theme === option.value
                          ? 'border-primary-500 bg-primary-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}>
                      <option.icon className="w-8 h-8 mx-auto mb-2 text-gray-600" />
                      <p className="font-medium text-gray-900">{option.label}</p>
                      <p className="text-sm text-gray-500 mt-1">{option.desc}</p>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Language & Region</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="label">Language</label>
                    <select className="input" defaultValue="en">
                      <option value="en">English</option>
                      <option value="es">Spanish</option>
                      <option value="fr">French</option>
                      <option value="de">German</option>
                      <option value="zh">Chinese</option>
                      <option value="ja">Japanese</option>
                      <option value="ko">Korean</option>
                    </select>
                  </div>
                  <div>
                    <label className="label">Date Format</label>
                    <select className="input" defaultValue="MM/DD/YYYY">
                      <option value="MM/DD/YYYY">MM/DD/YYYY</option>
                      <option value="DD/MM/YYYY">DD/MM/YYYY</option>
                      <option value="YYYY-MM-DD">YYYY-MM-DD</option>
                    </select>
                  </div>
                  <div>
                    <label className="label">Time Format</label>
                    <select className="input" defaultValue="12h">
                      <option value="12h">12 Hour</option>
                      <option value="24h">24 Hour</option>
                    </select>
                  </div>
                  <div>
                    <label className="label">Units</label>
                    <select className="input" defaultValue="imperial">
                      <option value="imperial">Imperial (mi, °F)</option>
                      <option value="metric">Metric (km, °C)</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeSection === 'notifications' && (
            <div className="space-y-6">
              <div className="p-4 bg-blue-50 rounded-xl border border-blue-100">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                    <Bell className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">Notification Permissions</h3>
                    <p className="text-sm text-gray-500">Enable browser notifications to receive real-time updates</p>
                  </div>
                  <button className="btn-primary ml-auto">Enable</button>
                </div>
              </div>

              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Email Notifications</h2>
                <div className="space-y-3">
                  {(Object.entries(notifications) as Array<[keyof typeof notifications, boolean]>).map(([key, enabled]) => (
                    <div key={key} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <h3 className="font-medium text-gray-900 capitalize">{key.replace(/([A-Z])/g, ' $1')}</h3>
                        <p className="text-sm text-gray-500">
                          {key === 'email' ? 'General email notifications' :
                           key === 'push' ? 'Push notifications to your device' :
                           key === 'tripReminders' ? 'Reminders for upcoming trips' :
                           key === 'weatherAlerts' ? 'Severe weather warnings' :
                           key === 'transitUpdates' ? 'Real-time transit changes' :
                           key === 'recommendations' ? 'Personalized suggestions' :
                           'Marketing emails and news'}
                        </p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={Boolean(enabled)}
                          onChange={(e) => setNotifications({ ...notifications, [key]: e.target.checked })}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                      </label>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeSection === 'privacy' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Profile Visibility</h2>
                <div className="space-y-3">
                  {['public', 'friends', 'private'].map((level) => (
                    <button
                      key={level}
                      onClick={() => setPrivacy({ ...privacy, profileVisibility: level })}
                      className={`w-full p-4 rounded-xl border-2 text-left transition-all ${
                        privacy.profileVisibility === level
                          ? 'border-primary-500 bg-primary-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}>
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium capitalize text-gray-900">{level}</p>
                          <p className="text-sm text-gray-500">
                            {level === 'public' ? 'Anyone can see your profile and saved places' :
                             level === 'friends' ? 'Only your connections can see your profile' :
                             'Only you can see your profile'}
                          </p>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-3">
                {(Object.entries(privacy).filter(([key]) => key !== 'profileVisibility') as Array<[keyof typeof privacy, boolean]>).map(([key, enabled]) => (
                  <div key={key} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <h3 className="font-medium text-gray-900 capitalize">{key.replace(/([A-Z])/g, ' $1')}</h3>
                      <p className="text-sm text-gray-500">
                        {key === 'locationSharing' ? 'Share your location with the app for better recommendations' :
                         key === 'analytics' ? 'Help improve the app with anonymous usage data' :
                         'Receive personalized advertisements based on your activity'}
                      </p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={Boolean(enabled)}
                        onChange={(e) => setPrivacy({ ...privacy, [key]: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                    </label>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeSection === 'data' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Storage & Sync</h2>
                <div className="space-y-3">
                  {(Object.entries(data) as Array<[keyof typeof data, boolean]>).map(([key, enabled]) => (
                    <div key={key} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <h3 className="font-medium text-gray-900 capitalize">{key.replace(/([A-Z])/g, ' $1')}</h3>
                        <p className="text-sm text-gray-500">
                          {key === 'autoSync' ? 'Automatically sync data when online' :
                           key === 'offlineMaps' ? 'Download maps for offline use' :
                           'Reduce data usage on mobile networks'}
                        </p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={Boolean(enabled)}
                          onChange={(e) => setData({ ...data, [key]: e.target.checked })}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                      </label>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-4 bg-gray-50 rounded-xl border border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-gray-900">Clear Cache</h3>
                    <p className="text-sm text-gray-500">Free up storage space by removing cached data</p>
                  </div>
                  <button className="btn-outline btn-sm">Clear Cache</button>
                </div>
              </div>

              <div className="p-4 bg-gray-50 rounded-xl border border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-gray-900">Export Data</h3>
                    <p className="text-sm text-gray-500">Download all your data in JSON format</p>
                  </div>
                  <button className="btn-outline btn-sm">Export</button>
                </div>
              </div>
            </div>
          )}

          {activeSection === 'account' && (
            <div className="space-y-8">
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Security</h2>
                <div className="space-y-4">
                  <div className="p-4 bg-gray-50 rounded-xl border border-gray-200">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium text-gray-900">Two-Factor Authentication</h3>
                        <p className="text-sm text-gray-500">Add an extra layer of security</p>
                      </div>
                      <button className="btn-outline btn-sm">Enable</button>
                    </div>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-xl border border-gray-200">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium text-gray-900">Change Password</h3>
                        <p className="text-sm text-gray-500">Last updated 30 days ago</p>
                      </div>
                      <button className="btn-outline btn-sm">Change</button>
                    </div>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-xl border border-gray-200">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium text-gray-900">Active Sessions</h3>
                        <p className="text-sm text-gray-500">Manage logged-in devices</p>
                      </div>
                      <button className="btn-outline btn-sm">View Sessions</button>
                    </div>
                  </div>
                </div>
              </div>

              <div className="pt-6 border-t border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Danger Zone</h2>
                <div className="p-4 bg-red-50 rounded-xl border border-red-100">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-red-100 flex items-center justify-center">
                        <Trash2 className="w-5 h-5 text-red-600" />
                      </div>
                      <div>
                        <h3 className="font-medium text-red-900">Delete Account</h3>
                        <p className="text-sm text-red-700">Permanently delete your account and all data. This action cannot be undone.</p>
                      </div>
                    </div>
                    <button className="btn-danger">Delete Account</button>
                  </div>
                </div>
              </div>

              <div className="pt-6 border-t border-gray-200">
                <button
                  onClick={logout}
                  className="btn-outline w-full justify-center text-red-600 border-red-200 hover:bg-red-50"
                >
                  <LogOut className="w-4 h-4 mr-2" />
                  Sign Out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
import { useState } from 'react';
import type { UserPreferences } from '../types/user';

interface PreferencesProps {
  preferences: UserPreferences;
  onSave: (preferences: UserPreferences) => void;
}

export function Preferences({ preferences, onSave }: PreferencesProps) {
  const [localPrefs, setLocalPrefs] = useState(preferences);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(localPrefs);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Interests</label>
        <input
          type="text"
          value={localPrefs.interests.join(', ')}
          onChange={(e) => setLocalPrefs({ ...localPrefs, interests: e.target.value.split(',').map((s) => s.trim()) })}
          className="w-full px-3 py-2 border border-gray-200 rounded-lg"
          placeholder="museums, parks, food..."
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Budget Level</label>
        <select
          value={localPrefs.budget_level}
          onChange={(e) => setLocalPrefs({ ...localPrefs, budget_level: e.target.value })}
          className="w-full px-3 py-2 border border-gray-200 rounded-lg"
        >
          <option value="budget">Budget</option>
          <option value="moderate">Moderate</option>
          <option value="luxury">Luxury</option>
        </select>
      </div>
      <button type="submit" className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
        Save Preferences
      </button>
    </form>
  );
}

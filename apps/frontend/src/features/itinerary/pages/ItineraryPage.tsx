import { Plus, Calendar, MapPin, Clock, DollarSign, Trash2, GripVertical, Edit, Copy, Share2, Download } from 'lucide-react';
import { useState } from 'react';
import type { Itinerary } from '@shared/types';

const mockItinerary: Itinerary = {
  id: '1',
  user_id: '1',
  title: 'NYC 3-Day Adventure',
  description: 'Perfect mix of culture, food, and iconic sights',
  status: 'active',
  start_date: '2024-02-15',
  end_date: '2024-02-17',
  budget_level: 'mid_range',
  pace: 'moderate',
  interests: ['museums', 'food', 'parks'],
  accessibility_needs: [],
  dietary_restrictions: [],
  transport_preferences: ['walking', 'transit'],
  base_location: { latitude: 40.7580, longitude: -73.9855 },
  base_address: 'Times Square, New York, NY',
  city: 'New York',
  country: 'USA',
  tags: ['weekend', 'culture', 'foodie'],
  is_public: false,
  collaborators: [],
  total_estimated_cost: 450,
  currency: 'USD',
  days: [
    {
      id: 'day1',
      itinerary_id: '1',
      day_number: 1,
      date: '2024-02-15',
      title: 'Midtown & Museums',
      notes: 'Start early to beat crowds at MoMA',
      start_time: '09:00',
      end_time: '22:00',
      base_location: { latitude: 40.7580, longitude: -73.9855 },
      base_address: 'Times Square',
      items: [
        { id: '1', day_id: 'day1', type: 'meal', title: 'Breakfast at Cafe', description: 'Light breakfast near hotel', coordinates: { latitude: 40.7580, longitude: -73.9855 }, address: 'Near Times Square', start_time: '09:00', end_time: '10:00', duration_minutes: 60, estimated_cost: 25, currency: 'USD', notes: '', is_flexible: true, is_required: false, order_index: 0, created_at: '', updated_at: '' },
        { id: '2', day_id: 'day1', type: 'poi_visit', title: 'MoMA', description: 'Museum of Modern Art', coordinates: { latitude: 40.7614, longitude: -73.9776 }, address: '11 W 53rd St', start_time: '10:30', end_time: '13:30', duration_minutes: 180, estimated_cost: 25, currency: 'USD', notes: 'Buy tickets online', is_flexible: false, is_required: true, order_index: 1, created_at: '', updated_at: '' },
        { id: '3', day_id: 'day1', type: 'meal', title: 'Lunch at Joe\'s Pizza', description: 'Classic NYC slice', coordinates: { latitude: 40.7589, longitude: -73.9851 }, address: '1435 Broadway', start_time: '13:45', end_time: '14:30', duration_minutes: 45, estimated_cost: 15, currency: 'USD', notes: '', is_flexible: true, is_required: false, order_index: 2, created_at: '', updated_at: '' },
        { id: '4', day_id: 'day1', type: 'poi_visit', title: 'Central Park Walk', description: 'Stroll through the park', coordinates: { latitude: 40.7829, longitude: -73.9654 }, address: 'Central Park', start_time: '15:00', end_time: '17:00', duration_minutes: 120, estimated_cost: 0, currency: 'USD', notes: '', is_flexible: true, is_required: false, order_index: 3, created_at: '', updated_at: '' },
        { id: '5', day_id: 'day1', type: 'poi_visit', title: 'Top of the Rock', description: 'Sunset views', coordinates: { latitude: 40.7590, longitude: -73.9790 }, address: '30 Rockefeller Plaza', start_time: '17:30', end_time: '19:00', duration_minutes: 90, estimated_cost: 38, currency: 'USD', notes: 'Book sunset slot', is_flexible: false, is_required: true, order_index: 4, created_at: '', updated_at: '' },
        { id: '6', day_id: 'day1', type: 'meal', title: 'Dinner in Hell\'s Kitchen', description: 'Great restaurant row', coordinates: { latitude: 40.7650, longitude: -73.9930 }, address: '9th Ave', start_time: '19:30', end_time: '21:00', duration_minutes: 90, estimated_cost: 60, currency: 'USD', notes: '', is_flexible: true, is_required: false, order_index: 5, created_at: '', updated_at: '' },
      ],
      created_at: '',
      updated_at: '',
    },
    {
      id: 'day2',
      itinerary_id: '1',
      day_number: 2,
      date: '2024-02-16',
      title: 'Downtown & Culture',
      notes: 'Take subway downtown',
      start_time: '09:00',
      end_time: '22:00',
      base_location: { latitude: 40.7580, longitude: -73.9855 },
      base_address: 'Times Square',
      items: [
        { id: '7', day_id: 'day2', type: 'meal', title: 'Brunch', description: 'Late breakfast', coordinates: { latitude: 40.7128, longitude: -74.0060 }, address: 'Downtown', start_time: '09:30', end_time: '11:00', duration_minutes: 90, estimated_cost: 35, currency: 'USD', notes: '', is_flexible: true, is_required: false, order_index: 0, created_at: '', updated_at: '' },
        { id: '8', day_id: 'day2', type: 'poi_visit', title: '9/11 Memorial', description: 'Reflecting pools & museum', coordinates: { latitude: 40.7116, longitude: -74.0124 }, address: '180 Greenwich St', start_time: '11:30', end_time: '14:00', duration_minutes: 150, estimated_cost: 26, currency: 'USD', notes: '', is_flexible: false, is_required: true, order_index: 1, created_at: '', updated_at: '' },
        { id: '9', day_id: 'day2', type: 'meal', title: 'Lunch in Chinatown', description: 'Dim sum', coordinates: { latitude: 40.7158, longitude: -73.9980 }, address: 'Chinatown', start_time: '14:15', end_time: '15:30', duration_minutes: 75, estimated_cost: 30, currency: 'USD', notes: '', is_flexible: true, is_required: false, order_index: 2, created_at: '', updated_at: '' },
        { id: '10', day_id: 'day2', type: 'poi_visit', title: 'SoHo & Greenwich Village', description: 'Shopping & exploring', coordinates: { latitude: 40.7230, longitude: -74.0020 }, address: 'SoHo', start_time: '15:45', end_time: '18:00', duration_minutes: 135, estimated_cost: 0, currency: 'USD', notes: '', is_flexible: true, is_required: false, order_index: 3, created_at: '', updated_at: '' },
        { id: '11', day_id: 'day2', type: 'poi_visit', title: 'Brooklyn Bridge Walk', description: 'Sunset walk', coordinates: { latitude: 40.7061, longitude: -73.9969 }, address: 'Brooklyn Bridge', start_time: '18:15', end_time: '19:30', duration_minutes: 75, estimated_cost: 0, currency: 'USD', notes: '', is_flexible: true, is_required: false, order_index: 4, created_at: '', updated_at: '' },
        { id: '12', day_id: 'day2', type: 'meal', title: 'Dinner in DUMBO', description: 'Waterfront dining', coordinates: { latitude: 40.7033, longitude: -73.9880 }, address: 'DUMBO, Brooklyn', start_time: '20:00', end_time: '21:30', duration_minutes: 90, estimated_cost: 70, currency: 'USD', notes: '', is_flexible: true, is_required: false, order_index: 5, created_at: '', updated_at: '' },
      ],
      created_at: '',
      updated_at: '',
    },
    {
      id: 'day3',
      itinerary_id: '1',
      day_number: 3,
      date: '2024-02-17',
      title: 'Uptown & Parks',
      notes: 'Relaxed final day',
      start_time: '09:00',
      end_time: '18:00',
      base_location: { latitude: 40.7580, longitude: -73.9855 },
      base_address: 'Times Square',
      items: [
        { id: '13', day_id: 'day3', type: 'meal', title: 'Brunch', description: 'Leisurely brunch', coordinates: { latitude: 40.7794, longitude: -73.9632 }, address: 'Upper East Side', start_time: '10:00', end_time: '11:30', duration_minutes: 90, estimated_cost: 40, currency: 'USD', notes: '', is_flexible: true, is_required: false, order_index: 0, created_at: '', updated_at: '' },
        { id: '14', day_id: 'day3', type: 'poi_visit', title: 'The Met', description: 'Metropolitan Museum of Art', coordinates: { latitude: 40.7794, longitude: -73.9632 }, address: '1000 5th Ave', start_time: '12:00', end_time: '15:00', duration_minutes: 180, estimated_cost: 30, currency: 'USD', notes: '', is_flexible: false, is_required: true, order_index: 1, created_at: '', updated_at: '' },
        { id: '15', day_id: 'day3', type: 'poi_visit', title: 'Central Park Zoo', description: 'Quick visit', coordinates: { latitude: 40.7678, longitude: -73.9718 }, address: 'Central Park', start_time: '15:30', end_time: '16:30', duration_minutes: 60, estimated_cost: 18, currency: 'USD', notes: '', is_flexible: true, is_required: false, order_index: 2, created_at: '', updated_at: '' },
        { id: '16', day_id: 'day3', type: 'meal', title: 'Coffee Break', description: 'Cafe near park', coordinates: { latitude: 40.7678, longitude: -73.9718 }, address: 'Central Park', start_time: '16:45', end_time: '17:15', duration_minutes: 30, estimated_cost: 12, currency: 'USD', notes: '', is_flexible: true, is_required: false, order_index: 3, created_at: '', updated_at: '' },
        { id: '17', day_id: 'day3', type: 'meal', title: 'Early Dinner', description: 'Before show', coordinates: { latitude: 40.7590, longitude: -73.9840 }, address: 'Theater District', start_time: '17:30', end_time: '19:00', duration_minutes: 90, estimated_cost: 55, currency: 'USD', notes: '', is_flexible: true, is_required: false, order_index: 4, created_at: '', updated_at: '' },
        { id: '18', day_id: 'day3', type: 'activity', title: 'Broadway Show', description: 'Evening entertainment', coordinates: { latitude: 40.7590, longitude: -73.9840 }, address: 'Broadway', start_time: '19:30', end_time: '22:00', duration_minutes: 150, estimated_cost: 120, currency: 'USD', notes: 'Book in advance', is_flexible: false, is_required: true, order_index: 5, created_at: '', updated_at: '' },
      ],
      created_at: '',
      updated_at: '',
    },
  ],
  created_at: '2024-01-15T10:06:00Z',
  updated_at: '2024-01-15T10:06:00Z',
};

const typeIcons: Record<string, React.ReactNode> = {
  poi_visit: <MapPin className="w-4 h-4" />,
  meal: <DollarSign className="w-4 h-4" />,
  activity: <Clock className="w-4 h-4" />,
  transit: <Clock className="w-4 h-4" />,
  rest: <Clock className="w-4 h-4" />,
  custom: <MapPin className="w-4 h-4" />,
  accommodation: <MapPin className="w-4 h-4" />,
};

const typeColors: Record<string, string> = {
  poi_visit: 'bg-blue-100 text-blue-700',
  meal: 'bg-green-100 text-green-700',
  activity: 'bg-purple-100 text-purple-700',
  transit: 'bg-orange-100 text-orange-700',
  rest: 'bg-gray-100 text-gray-700',
  custom: 'bg-pink-100 text-pink-700',
  accommodation: 'bg-indigo-100 text-indigo-700',
};

export function ItineraryPage() {
  const [itinerary] = useState<Itinerary>(mockItinerary);
  const [activeDay, setActiveDay] = useState<string>(mockItinerary.days[0].id);
  const [isEditing, setIsEditing] = useState(false);

  const currentDay = itinerary.days.find(d => d.id === activeDay);
  const totalCost = itinerary.days.reduce((sum, day) => 
    sum + day.items.reduce((s, item) => s + (item.estimated_cost || 0), 0), 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{itinerary.title}</h1>
          <p className="text-gray-500 mt-1">{itinerary.description}</p>
        </div>
        <div className="flex items-center gap-2">
          <button className="btn-outline">
            <Share2 className="w-4 h-4 mr-2" />
            Share
          </button>
          <button className="btn-outline">
            <Download className="w-4 h-4 mr-2" />
            Export
          </button>
          <button className="btn-primary" onClick={() => setIsEditing(!isEditing)}>
            {isEditing ? 'Done' : 'Edit'}
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="card p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center">
              <Calendar className="w-5 h-5 text-primary-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Duration</p>
              <p className="font-semibold text-gray-900">{itinerary.days.length} days</p>
            </div>
          </div>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center">
              <DollarSign className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Est. Cost</p>
              <p className="font-semibold text-gray-900">${totalCost}</p>
            </div>
          </div>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
              <MapPin className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Places</p>
              <p className="font-semibold text-gray-900">
                {itinerary.days.reduce((sum, day) => sum + day.items.filter(i => i.type === 'poi_visit').length, 0)}
              </p>
            </div>
          </div>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-orange-100 flex items-center justify-center">
              <Clock className="w-5 h-5 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Pace</p>
              <p className="font-semibold text-gray-900 capitalize">{itinerary.pace}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Day Tabs */}
      <div className="card">
        <div className="border-b border-gray-200 overflow-x-auto">
          <nav className="flex gap-1 p-1" aria-label="Days">
            {itinerary.days.map((day) => (
              <button
                key={day.id}
                onClick={() => setActiveDay(day.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                  activeDay === day.id
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                Day {day.day_number}
                <span className="ml-2 px-2 py-0.5 text-xs bg-gray-200 rounded-full">
                  {day.items.length} items
                </span>
              </button>
            ))}
            <button className="px-4 py-2 rounded-lg text-sm font-medium text-gray-500 hover:bg-gray-100 whitespace-nowrap">
              <Plus className="w-4 h-4" />
            </button>
          </nav>
        </div>

        {/* Day Content */}
        {currentDay && (
          <div className="p-4">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">{currentDay.title || `Day ${currentDay.day_number}`}</h2>
                <p className="text-sm text-gray-500">
                  {new Date(currentDay.date).toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-900">
                  ${currentDay.items.reduce((sum, item) => sum + (item.estimated_cost || 0), 0)}
                </span>
                <button className="btn-outline btn-sm">
                  <Plus className="w-4 h-4 mr-1" />
                  Add Item
                </button>
              </div>
            </div>

            {/* Timeline */}
            <div className="space-y-4">
              {currentDay.items.map((item, index) => (
                <div
                  key={item.id}
                  className="flex gap-4 group"
                  draggable={isEditing}
                >
                  {/* Timeline connector */}
                  <div className="relative flex-shrink-0 w-6">
                    <div className="w-2 h-2 rounded-full border-2 border-primary-500 bg-white relative z-10" />
                    {index < currentDay.items.length - 1 && (
                      <div className="absolute left-1 top-6 bottom-0 w-0.5 bg-gray-200" />
                    )}
                  </div>

                  {/* Time */}
                  <div className="flex-shrink-0 w-20 text-right pt-1">
                    <span className="text-sm font-medium text-gray-900">{item.start_time}</span>
                    <span className="text-xs text-gray-500 block">- {item.end_time}</span>
                  </div>

                  {/* Item Card */}
                  <div className="flex-1 card-hover p-4 relative">
                    <div className="flex items-start gap-3">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${typeColors[item.type]}`}>
                        {typeIcons[item.type]}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <h3 className="font-medium text-gray-900">{item.title}</h3>
                            <p className="text-sm text-gray-500">{item.description || item.address}</p>
                          </div>
                          <div className="flex items-center gap-1">
                            <span className={`px-2 py-0.5 text-xs rounded-full ${typeColors[item.type]}`}>
                              {item.type.replace('_', ' ')}
                            </span>
                            {item.estimated_cost && (
                              <span className="text-sm font-medium text-gray-900">${item.estimated_cost}</span>
                            )}
                          </div>
                        </div>
                        
                        {item.notes && (
                          <p className="text-xs text-gray-500 mt-1">{item.notes}</p>
                        )}
                        
                        {item.transit_details && (
                          <div className="mt-2 p-2 bg-gray-50 rounded-lg text-xs text-gray-600">
                            {item.transit_details.route_name} • {item.transit_details.duration_minutes} min
                          </div>
                        )}
                      </div>

                      {/* Actions */}
                      <div className="opacity-0 group-hover:opacity-100 transition-opacity flex flex-col gap-1">
                        {isEditing && (
                          <button className="p-1 rounded hover:bg-gray-100 text-gray-500">
                            <GripVertical className="w-4 h-4" />
                          </button>
                        )}
                        <button className="p-1 rounded hover:bg-gray-100 text-gray-500">
                          <Edit className="w-4 h-4" />
                        </button>
                        <button className="p-1 rounded hover:bg-gray-100 text-gray-500">
                          <Copy className="w-4 h-4" />
                        </button>
                        <button className="p-1 rounded hover:bg-red-100 text-red-500">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Empty state */}
      {!currentDay && (
        <div className="card p-12 text-center">
          <Calendar className="w-12 h-12 mx-auto text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No day selected</h3>
          <p className="text-gray-500">Select a day from the tabs above</p>
        </div>
      )}
    </div>
  );
}
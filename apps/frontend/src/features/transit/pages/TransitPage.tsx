import { Bus, Train, MapPin, Clock, Search, Navigation, RefreshCw, DollarSign } from 'lucide-react';
import { useState } from 'react';

export function TransitPage() {
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [departureTime, setDepartureTime] = useState('now');
  const [selectedMode, setSelectedMode] = useState<string>('all');
  const [showResults, setShowResults] = useState(false);

  const transportModes = [
    { id: 'all', label: 'All', icon: Navigation },
    { id: 'transit', label: 'Transit', icon: Bus },
    { id: 'walking', label: 'Walking', icon: MapPin },
    { id: 'cycling', label: 'Cycling', icon: Train },
    { id: 'driving', label: 'Driving', icon: Clock },
  ];

  const mockRoutes = [
    {
      id: '1',
      duration: 35,
      departure: '09:00',
      arrival: '09:35',
      modes: ['walking', 'transit'],
      steps: [
        { type: 'walk', duration: 5, instruction: 'Walk to Times Sq-42 St Station' },
        { type: 'transit', duration: 20, instruction: 'Take Red Line to 59th St-Columbus Circle', route: '1', color: 'bg-red-500' },
        { type: 'walk', duration: 10, instruction: 'Walk to Central Park' },
      ],
      fare: 2.90,
      transfers: 0,
    },
    {
      id: '2',
      duration: 28,
      departure: '09:05',
      arrival: '09:33',
      modes: ['transit'],
      steps: [
        { type: 'transit', duration: 3, instruction: 'Walk to 42 St-Bryant Park Station' },
        { type: 'transit', duration: 15, instruction: 'Take B/D/F/M to 59th St-Columbus Circle', route: 'B', color: 'bg-orange-500' },
        { type: 'walk', duration: 10, instruction: 'Walk to Central Park' },
      ],
      fare: 2.90,
      transfers: 0,
    },
    {
      id: '3',
      duration: 45,
      departure: '09:00',
      arrival: '09:45',
      modes: ['walking'],
      steps: [
        { type: 'walk', duration: 45, instruction: 'Walk via Broadway & Central Park W' },
      ],
      fare: 0,
      transfers: 0,
    },
  ];

  const handleSearch = () => {
    if (origin && destination) {
      setShowResults(true);
    }
  };

  const swapLocations = () => {
    const temp = origin;
    setOrigin(destination);
    setDestination(temp);
  };

  return (
    <div className="space-y-6">
      {/* Search Form */}
      <div className="card">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Plan Your Trip</h2>
        </div>
        <div className="p-4 space-y-4">
          <div className="flex items-center gap-3">
            <div className="relative flex-1">
              <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="From (e.g., Times Square)"
                value={origin}
                onChange={(e) => setOrigin(e.target.value)}
                className="input pl-10"
              />
            </div>
            <button
              onClick={swapLocations}
              className="p-2 rounded-lg bg-gray-100 text-gray-500 hover:bg-gray-200 transition-colors flex-shrink-0"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
            <div className="relative flex-1">
              <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-primary-600" />
              <input
                type="text"
                placeholder="To (e.g., Central Park)"
                value={destination}
                onChange={(e) => setDestination(e.target.value)}
                className="input pl-10"
              />
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="relative">
              <Clock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <select
                value={departureTime}
                onChange={(e) => setDepartureTime(e.target.value)}
                className="input pl-10 pr-8 appearance-none"
              >
                <option value="now">Leave now</option>
                <option value="09:00">09:00 AM</option>
                <option value="10:00">10:00 AM</option>
                <option value="12:00">12:00 PM</option>
                <option value="15:00">03:00 PM</option>
                <option value="18:00">06:00 PM</option>
                <option value="custom">Custom time...</option>
              </select>
            </div>
            <button onClick={handleSearch} className="btn-primary flex-1 sm:flex-none">
              <Search className="w-4 h-4 mr-2" />
              Find Routes
            </button>
          </div>

          {/* Transport Mode Filter */}
          <div className="pt-2 border-t border-gray-200">
            <div className="flex flex-wrap gap-2">
              {transportModes.map((mode) => (
                <button
                  key={mode.id}
                  onClick={() => setSelectedMode(mode.id)}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                    selectedMode === mode.id
                      ? 'bg-primary-100 text-primary-700'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  <mode.icon className="w-4 h-4" />
                  {mode.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Results */}
      {showResults && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">
            {mockRoutes.length} routes found
          </h3>
          
          {mockRoutes.map((route) => (
            <div key={route.id} className="card p-4 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-center gap-4">
                  <div className="w-16 h-16 rounded-xl bg-primary-100 flex items-center justify-center flex-shrink-0">
                    <Bus className="w-8 h-8 text-primary-600" />
                  </div>
                  <div>
                    <div className="flex items-center gap-3">
                      <span className="text-2xl font-bold text-gray-900">{route.duration} min</span>
                      <span className="text-gray-500">{route.departure} - {route.arrival}</span>
                      {route.transfers > 0 && (
                        <span className="badge badge-warning">{route.transfers} transfer{route.transfers > 1 ? 's' : ''}</span>
                      )}
                    </div>
                    <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                      <span className="flex items-center gap-1">
                        <DollarSign className="w-4 h-4" />
                        ${route.fare.toFixed(2)}
                      </span>
                      <span className="flex items-center gap-1">
                        {route.modes.map(m => (
                          <span key={m} className="px-2 py-0.5 text-xs bg-gray-100 rounded">{m}</span>
                        ))}
                      </span>
                    </div>
                  </div>
                </div>
                
                <button className="btn-outline btn-sm whitespace-nowrap">
                  Details
                </button>
              </div>

              {/* Steps */}
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="space-y-2">
                  {route.steps.map((step, index) => (
                    <div key={index} className="flex items-center gap-3">
                      <div className="relative flex-shrink-0 w-6">
                        <div className={`w-2 h-2 rounded-full ${step.type === 'transit' ? 'bg-primary-600' : 'bg-gray-400'}`} />
                        {index < route.steps.length - 1 && (
                          <div className="absolute left-1 top-4 bottom-0 w-0.5 bg-gray-200" />
                        )}
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900">{step.instruction}</p>
                        {step.route && (
                          <span className={`inline-block px-2 py-0.5 text-xs rounded ${step.color}`}>
                            {step.route}
                          </span>
                        )}
                      </div>
                      <span className="text-sm text-gray-500 whitespace-nowrap">{step.duration} min</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Real-time Updates */}
      <div className="card">
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Real-time Updates</h2>
          <button className="btn-ghost btn-sm">
            <RefreshCw className="w-4 h-4 mr-1" />
            Refresh
          </button>
        </div>
        <div className="p-4 space-y-3">
          {[
            { route: '1', name: 'Red Line', status: 'delayed', message: '5 min delays due to signal issues', color: 'bg-red-500' },
            { route: 'B', name: 'B Line', status: 'on_time', message: 'Running on schedule', color: 'bg-green-500' },
            { route: '4', name: '4 Line', status: 'delayed', message: '10 min delays - track work', color: 'bg-red-500' },
            { route: 'Q', name: 'Q Line', status: 'on_time', message: 'Running on schedule', color: 'bg-green-500' },
          ].map((alert) => (
            <div key={alert.route} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${alert.color} text-white font-bold text-sm`}>
                {alert.route}
              </div>
              <div className="flex-1">
                <p className="font-medium text-gray-900">{alert.name}</p>
                <p className="text-sm text-gray-500">{alert.message}</p>
              </div>
              <span className={`badge ${alert.status === 'delayed' ? 'badge-warning' : 'badge-success'}`}>
                {alert.status === 'delayed' ? 'Delayed' : 'On Time'}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Nearby Stops */}
      <div className="card">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Nearby Stops</h2>
        </div>
        <div className="p-4 space-y-3">
          {[
            { name: 'Times Sq-42 St', lines: ['1', '2', '3', 'N', 'Q', 'R', 'W', 'S'], distance: '0.1 mi', nextArrival: '2 min' },
            { name: '42 St-Bryant Park', lines: ['B', 'D', 'F', 'M'], distance: '0.2 mi', nextArrival: '5 min' },
            { name: '34 St-Herald Sq', lines: ['B', 'D', 'F', 'M', 'N', 'Q', 'R', 'W'], distance: '0.4 mi', nextArrival: '3 min' },
            { name: 'Grand Central', lines: ['4', '5', '6', '7', 'S'], distance: '0.5 mi', nextArrival: '1 min' },
          ].map((stop) => (
            <div key={stop.name} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center">
                  <Train className="w-5 h-5 text-primary-600" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">{stop.name}</p>
                  <p className="text-sm text-gray-500">{stop.distance} away</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="flex gap-1">
                  {stop.lines.slice(0, 4).map((line) => (
                    <span key={line} className="w-6 h-6 rounded text-xs font-bold text-white flex items-center justify-center bg-gray-600">
                      {line}
                    </span>
                  ))}
                </div>
                <span className="text-sm font-medium text-primary-600">{stop.nextArrival}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
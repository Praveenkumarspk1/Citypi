// TransitPlanner Component
// Multi-modal transit route planner with real-time updates

import { useState, useCallback, useEffect } from 'react';
import {
  MapPin,
  Clock,
  DollarSign,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  Bus,
  Bike,
  Car,
  Footprints,
  MapPin as MapPinIcon,
} from 'lucide-react';
import { useAgencies } from '@shared/hooks/useApi';
import type { TransitRoute, TransitStep, Coordinates, TransportMode } from '@shared/types';

interface TransitPlannerProps {
  origin?: Coordinates;
  destination?: Coordinates;
  originName?: string;
  destinationName?: string;
  departureTime?: Date;
  onRouteSelect?: (route: TransitRoute) => void;
  className?: string;
}

export function TransitPlanner({
  origin,
  destination,
  originName,
  destinationName,
  departureTime: departureTimeProp = new Date(),
  onRouteSelect,
  className = '',
}: TransitPlannerProps) {
  const [originInput, setOriginInput] = useState(originName || '');
  const [destinationInput, setDestinationInput] = useState(destinationName || '');
  const [departureTimeState, setDepartureTimeState] = useState<Date>(departureTimeProp);
  const [selectedMode, setSelectedMode] = useState<TransportMode[]>(['transit', 'walking']);
  const [routes, setRoutes] = useState<TransitRoute[]>([]);
  const [selectedRoute, setSelectedRoute] = useState<TransitRoute | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showModeSelector, setShowModeSelector] = useState(false);
  const [expandedRouteId, setExpandedRouteId] = useState<string | null>(null);
  
  useAgencies();

  const searchRoutes = useCallback(async () => {
    if (!origin || !destination) {
      setError('Please select both origin and destination');
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      // In a real app, this would call the API
      // For now, we'll simulate with mock data
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const mockRoutes: TransitRoute[] = generateMockRoutes(origin, destination, selectedMode);
      setRoutes(mockRoutes);
      if (mockRoutes.length > 0) {
        setSelectedRoute(mockRoutes[0]);
      }
    } catch (err) {
      setError('Failed to find routes. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, [origin, destination, selectedMode]);
  
  useEffect(() => {
    if (origin && destination) {
      searchRoutes();
    }
  }, [searchRoutes]);
  
  const swapLocations = () => {
    const tempInput = originInput;
    setOriginInput(destinationInput);
    setDestinationInput(tempInput);
    // Swap coords in parent
  };
  
  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };
  
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };
  
  const getModeIcon = (mode: TransportMode) => {
    const icons: Record<TransportMode, React.ReactNode> = {
      walking: <Footprints className="w-4 h-4" />,
      cycling: <Bike className="w-4 h-4" />,
      transit: <Bus className="w-4 h-4" />,
      driving: <Car className="w-4 h-4" />,
      rideshare: <Car className="w-4 h-4" />,
      scooter: <Bike className="w-4 h-4" />,
      wheelchair: <Footprints className="w-4 h-4" />,
    };
    return icons[mode] || <Footprints className="w-4 h-4" />;
  };
  
  const getStepIcon = (type: TransitStep['type'], mode?: TransportMode) => {
    if (type === 'walk') return <Footprints className="w-4 h-4" />;
    if (type === 'wait') return <Clock className="w-4 h-4" />;
    return getModeIcon(mode || 'transit');
  };
  
  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Input Section */}
      <div className="card p-4 space-y-4">
        <div className="flex items-center gap-2">
          <h3 className="font-semibold text-gray-900">Plan Your Trip</h3>
          <button
            onClick={swapLocations}
            className="p-1 text-gray-400 hover:text-gray-600"
            title="Swap origin and destination"
          >
            <RefreshCw className="w-5 h-5" />
          </button>
        </div>
        
        <div className="space-y-3">
          {/* Origin */}
          <div className="relative">
            <label className="label">From</label>
            <div className="relative">
              <MapPinIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={originInput}
                onChange={(e) => setOriginInput(e.target.value)}
                placeholder="Enter starting location"
                className="input pl-10"
              />
            </div>
          </div>
          
          {/* Destination */}
          <div className="relative">
            <label className="label">To</label>
            <div className="relative">
              <MapPinIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={destinationInput}
                onChange={(e) => setDestinationInput(e.target.value)}
                placeholder="Enter destination"
                className="input pl-10"
              />
            </div>
          </div>
          
          {/* Transport Modes */}
          <div>
            <label className="label">Transport Modes</label>
            <button
              onClick={() => setShowModeSelector(!showModeSelector)}
              className="input flex items-center justify-between"
              type="button"
            >
              <div className="flex items-center gap-2 flex-wrap">
                {selectedMode.map(mode => (
                  <span key={mode} className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-primary-100 text-primary-700 rounded">
                    {getModeIcon(mode)}
                    {mode}
                  </span>
                ))}
              </div>
              <ChevronDown className="w-4 h-4 text-gray-400" />
            </button>
            
            {showModeSelector && (
              <div className="mt-2 p-3 border border-gray-200 rounded-lg bg-white space-y-2">
                {(['walking', 'cycling', 'transit', 'driving', 'rideshare'] as TransportMode[]).map(mode => (
                  <label key={mode} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedMode.includes(mode)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedMode([...selectedMode, mode]);
                        } else {
                          setSelectedMode(selectedMode.filter(m => m !== mode));
                        }
                      }}
                      className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="flex items-center gap-2">
                      {getModeIcon(mode)}
                      <span className="capitalize">{mode}</span>
                    </span>
                  </label>
                ))}
              </div>
            )}
          </div>
          
          {/* Departure Time */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Departure</label>
              <input
                type="datetime-local"
                value={departureTimeState.toISOString().slice(0, 16)}
                onChange={(e) => setDepartureTimeState(new Date(e.target.value))}
                className="input"
              />
            </div>
            <div>
              <label className="label">&nbsp;</label>
              <button
                onClick={searchRoutes}
                disabled={isLoading || !origin || !destination}
                className="btn-primary w-full h-full"
              >
                {isLoading ? (
                  <span className="flex items-center justify-center gap-2">
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Searching...
                  </span>
                ) : (
                  'Find Routes'
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
      
      {/* Error Message */}
      {error && (
        <div className="card p-3 border-red-200 bg-red-50">
          <div className="flex items-center gap-2 text-red-700">
            <AlertCircle className="w-5 h-5" />
            <span>{error}</span>
          </div>
        </div>
      )}
      
      {/* Routes List */}
      <div className="flex-1 overflow-y-auto space-y-3 p-4">
        {routes.length === 0 && !isLoading && origin && destination ? (
          <div className="card p-8 text-center text-gray-500">
            <MapPin className="w-12 h-12 mx-auto text-gray-300 mb-4" />
            <p className="text-lg font-medium">No routes found</p>
            <p className="text-sm mt-1">Try adjusting your transport modes or locations</p>
          </div>
        ) : (
          routes.map((route, index) => (
            <RouteCard
              key={route.id}
              route={route}
              index={index}
              isSelected={selectedRoute?.id === route.id}
              isExpanded={expandedRouteId === route.id}
              onSelect={() => {
                setSelectedRoute(route);
                onRouteSelect?.(route);
              }}
              onToggleExpand={() => {
                setExpandedRouteId(expandedRouteId === route.id ? null : route.id);
              }}
              formatDuration={formatDuration}
              formatTime={formatTime}
              getStepIcon={getStepIcon}
              getModeIcon={getModeIcon}
            />
          ))
        )}
      </div>
    </div>
  );
}

// RouteCard Component
interface RouteCardProps {
  route: TransitRoute;
  index: number;
  isSelected: boolean;
  isExpanded: boolean;
  onSelect: () => void;
  onToggleExpand: () => void;
  formatDuration: (minutes: number) => string;
  formatTime: (date: Date) => string;
  getStepIcon: (type: TransitStep['type'], mode?: TransportMode) => React.ReactNode;
  getModeIcon: (mode: TransportMode) => React.ReactNode;
}

function RouteCard({
  route,
  index,
  isSelected,
  isExpanded,
  onSelect,
  onToggleExpand,
  formatDuration,
  formatTime,
  getStepIcon,
  getModeIcon,
}: RouteCardProps) {
  const hasTransit = route.steps.some(s => s.type === 'transit');
  
  return (
    <div
      className={`card transition-all duration-200 cursor-pointer ${
        isSelected ? 'ring-2 ring-primary-500 bg-primary-50' : 'hover:shadow-md'
      }`}
      onClick={onSelect}
    >
      <div className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3">
              <span className="text-lg font-bold text-gray-900">{index + 1}</span>
              <div className="flex items-center gap-2">
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                  hasTransit ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700'
                }`}>
                  {hasTransit ? 'Transit' : 'Direct'}
                </span>
                {route.fare && (
                  <span className="flex items-center gap-1 text-sm font-medium text-gray-700">
                    <DollarSign className="w-3 h-3" />
                    {route.fare.toFixed(2)} {route.currency}
                  </span>
                )}
              </div>
            </div>
            
            <div className="mt-2 flex items-center gap-4 text-sm text-gray-600">
              <span className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                {formatDuration(route.duration_minutes)}
              </span>
              <span className="flex items-center gap-1">
                <MapPin className="w-4 h-4" />
                {Math.round(route.distance_meters / 1000)} km
              </span>
              {route.departure_time && (
                <span className="flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  Dep: {formatTime(new Date(route.departure_time))}
                </span>
              )}
              {route.arrival_time && (
                <span className="flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  Arr: {formatTime(new Date(route.arrival_time))}
                </span>
              )}
            </div>
            
            {/* Transport Modes */}
            <div className="mt-2 flex flex-wrap gap-1">
              {route.transport_modes.map(mode => (
                <span key={mode} className="inline-flex items-center gap-1 px-2 py-0.5 text-xs bg-gray-100 text-gray-700 rounded">
                  {getModeIcon(mode)}
                  {mode}
                </span>
              ))}
            </div>
          </div>
          
          <button
            onClick={(e) => {
              e.stopPropagation();
              onToggleExpand();
            }}
            className="p-1 text-gray-400 hover:text-gray-600 flex-shrink-0"
          >
            {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </button>
        </div>
        
        {/* Expanded Steps */}
        {isExpanded && (
          <div className="border-t border-gray-100 pt-4 mt-4">
            <div className="space-y-3">
              {route.steps.map((step, stepIndex) => (
                <TransitStepCard
                  key={step.id}
                  step={step}
                  isLast={stepIndex === route.steps.length - 1}
                  formatDuration={formatDuration}
                  formatTime={formatTime}
                  getStepIcon={getStepIcon}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// TransitStepCard Component
interface TransitStepCardProps {
  step: TransitStep;
  isLast: boolean;
  formatDuration: (minutes: number) => string;
  formatTime: (date: Date) => string;
  getStepIcon: (type: TransitStep['type'], mode?: TransportMode) => React.ReactNode;
}

function TransitStepCard({
  step,
  isLast,
  formatDuration,
  formatTime,
  getStepIcon,
}: TransitStepCardProps) {
  const isTransit = step.type === 'transit';
  const isWalk = step.type === 'walk';
  
  return (
    <div className="flex gap-3">
      {/* Timeline */}
      <div className="flex flex-col items-center flex-shrink-0">
        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
          isTransit ? 'bg-blue-100 text-blue-600' :
          isWalk ? 'bg-green-100 text-green-600' :
          'bg-gray-100 text-gray-600'
        }`}>
          {getStepIcon(step.type, step.transport_mode)}
        </div>
        {!isLast && (
          <div className="w-0.5 h-full bg-gray-200 mt-1" />
        )}
      </div>
      
      {/* Step Details */}
      <div className="flex-1 min-w-0 pt-1">
        <div className="flex items-center gap-2">
          <span className={`font-medium text-sm ${
            isTransit ? 'text-blue-700' :
            isWalk ? 'text-green-700' :
            'text-gray-700'
          }`}>
            {step.instructions}
          </span>
          
          {isTransit && step.route_name && (
            <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded">
              {step.route_name}
            </span>
          )}
          
          {step.fare && (
            <span className="flex items-center gap-1 text-sm text-gray-600">
              <DollarSign className="w-3 h-3" />
              {step.fare.toFixed(2)} {step.currency}
            </span>
          )}
        </div>
        
        <div className="mt-1 flex items-center gap-4 text-sm text-gray-500">
          {step.duration_minutes && (
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {formatDuration(step.duration_minutes)}
            </span>
          )}
          
          {step.departure_stop && (
            <span className="flex items-center gap-1">
              <MapPin className="w-3 h-3" />
              From: {step.departure_stop}
            </span>
          )}
          
          {step.arrival_stop && (
            <span className="flex items-center gap-1">
              <MapPin className="w-3 h-3" />
              To: {step.arrival_stop}
            </span>
          )}
          
          {step.departure_time && (
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {formatTime(new Date(step.departure_time))}
            </span>
          )}
          
          {isTransit && step.transfers !== undefined && step.transfers > 0 && (
            <span className="flex items-center gap-1 text-orange-600">
              <RefreshCw className="w-3 h-3" />
              {step.transfers} transfer{step.transfers > 1 ? 's' : ''}
            </span>
          )}
        </div>
        
        {step.polyline && (
          <div className="mt-2 p-2 bg-gray-50 rounded text-xs text-gray-500">
            Route polyline available (would show on map)
          </div>
        )}
      </div>
    </div>
  );
}

// Mock route generator
function generateMockRoutes(origin: Coordinates, destination: Coordinates, modes: TransportMode[]): TransitRoute[] {
  
  return [
    {
      id: `route-1-${Date.now()}`,
      origin,
      destination,
      origin_name: 'Current Location',
      destination_name: 'Destination',
      departure_time: new Date().toISOString(),
      arrival_time: new Date(Date.now() + 45 * 60 * 1000).toISOString(),
      transport_modes: modes.includes('transit') ? ['transit', 'walking'] : ['walking'],
      duration_minutes: 45,
      distance_meters: 5200,
      fare: 2.75,
      currency: 'USD',
      steps: [
        {
          id: 'step-1',
          type: 'walk',
          duration_minutes: 5,
          distance_meters: 400,
          instructions: 'Walk to Main St & 1st Ave',
          departure_stop: 'Main St & 1st Ave',
        },
        {
          id: 'step-2',
          type: 'transit',
          transport_mode: 'transit',
          route_id: 'route-101',
          route_name: 'Blue Line',
          agency_name: 'City Transit',
          duration_minutes: 25,
          distance_meters: 4000,
          instructions: 'Take Blue Line toward Downtown',
          departure_stop: 'Main St & 1st Ave',
          arrival_stop: 'Central Station',
          departure_time: new Date(Date.now() + 5 * 60 * 1000).toISOString(),
          arrival_time: new Date(Date.now() + 30 * 60 * 1000).toISOString(),
          transfers: 0,
          fare: 2.75,
          currency: 'USD',
        },
        {
          id: 'step-3',
          type: 'walk',
          duration_minutes: 8,
          distance_meters: 600,
          instructions: 'Walk to destination',
          departure_stop: 'Central Station',
          arrival_stop: 'Destination',
        },
      ],
      polyline: 'mock_polyline_1',
      created_at: new Date().toISOString(),
    },
    {
      id: `route-2-${Date.now()}`,
      origin,
      destination,
      origin_name: 'Current Location',
      destination_name: 'Destination',
      departure_time: new Date(Date.now() + 10 * 60 * 1000).toISOString(),
      arrival_time: new Date(Date.now() + 60 * 60 * 1000).toISOString(),
      transport_modes: ['transit', 'walking'],
      duration_minutes: 50,
      distance_meters: 5500,
      fare: 2.75,
      currency: 'USD',
      steps: [
        {
          id: 'step-4',
          type: 'walk',
          duration_minutes: 3,
          distance_meters: 250,
          instructions: 'Walk to Oak St Station',
          departure_stop: 'Oak St Station',
        },
        {
          id: 'step-5',
          type: 'transit',
          transport_mode: 'transit',
          route_id: 'route-202',
          route_name: 'Red Line Express',
          agency_name: 'City Transit',
          duration_minutes: 20,
          distance_meters: 4500,
          instructions: 'Take Red Line Express toward Airport',
          departure_stop: 'Oak St Station',
          arrival_stop: 'Union Square',
          departure_time: new Date(Date.now() + 13 * 60 * 1000).toISOString(),
          arrival_time: new Date(Date.now() + 33 * 60 * 1000).toISOString(),
          transfers: 0,
          fare: 2.75,
          currency: 'USD',
        },
        {
          id: 'step-6',
          type: 'walk',
          duration_minutes: 12,
          distance_meters: 900,
          instructions: 'Walk to destination',
          departure_stop: 'Union Square',
          arrival_stop: 'Destination',
        },
      ],
      polyline: 'mock_polyline_2',
      created_at: new Date().toISOString(),
    },
  ];
}
// ItineraryBuilder Component
// Drag-and-drop itinerary builder with day planning

import { useState, useCallback } from 'react';
import { 
  Plus, 
  Trash2, 
  GripVertical, 
  Calendar, 
  MapPin, 
  Clock, 
  DollarSign,
  ChevronDown,
  ChevronUp,
  Save,
  Share2,
  Settings,
  Moon,
  Star,
  X, 
  Bus, 
  Utensils, 
  Car, 
  Home 
} from 'lucide-react';
import { useCreateItinerary, useUpdateItinerary } from '@shared/hooks/useApi';
import type { Itinerary, ItineraryDay, ItineraryItem, ItineraryItemType, TransportMode } from '@shared/types';

type NewItineraryItemInput = Omit<ItineraryItem, 'id' | 'day_id' | 'created_at' | 'updated_at' | 'order_index'> & {
  currency?: string;
  is_flexible?: boolean;
  is_required?: boolean;
};

interface ItineraryBuilderProps {
  initialItinerary?: Itinerary;
  onSave?: (itinerary: Itinerary) => void;
  onShare?: (itinerary: Itinerary) => void;
  readOnly?: boolean;
}

export function ItineraryBuilder({ 
  initialItinerary, 
  onSave, 
  onShare,
  readOnly = false 
}: ItineraryBuilderProps) {
  const [itinerary, setItinerary] = useState<Itinerary>(initialItinerary || createEmptyItinerary());
  const [activeDayIndex, setActiveDayIndex] = useState(0);
  const [draggedItem, setDraggedItem] = useState<{ dayIndex: number; itemIndex: number } | null>(null);
  
  const createItineraryMutation = useCreateItinerary();
  const updateItineraryMutation = useUpdateItinerary();
  
  // Update day when items change
  const addItem = useCallback((dayIndex: number, item: Omit<ItineraryItem, 'id' | 'day_id' | 'created_at' | 'updated_at' | 'order_index'>) => {
    const newItem: ItineraryItem = {
      ...item,
      id: `item-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      day_id: itinerary.days[dayIndex].id,
      order_index: itinerary.days[dayIndex].items.length,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    
    setItinerary(prev => ({
      ...prev,
      days: prev.days.map((day, i) => 
        i === dayIndex 
          ? { ...day, items: [...day.items, newItem].sort((a, b) => a.order_index - b.order_index) }
          : day
      ),
    }));
  }, [itinerary]);
  
  // Remove item from day
  const removeItem = useCallback((dayIndex: number, itemId: string) => {
    setItinerary(prev => ({
      ...prev,
      days: prev.days.map((day, i) => 
        i === dayIndex 
          ? { ...day, items: day.items.filter(item => item.id !== itemId) }
          : day
      ),
    }));
  }, []);
  
  // Move item within or between days
  const moveItem = useCallback((
    fromDayIndex: number, 
    fromItemIndex: number, 
    toDayIndex: number, 
    toItemIndex: number
  ) => {
    setItinerary(prev => {
      const newDays = [...prev.days];
      const item = newDays[fromDayIndex].items[fromItemIndex];
      
      // Remove from source
      newDays[fromDayIndex] = {
        ...newDays[fromDayIndex],
        items: newDays[fromDayIndex].items.filter((_, i) => i !== fromItemIndex),
      };
      
      // Insert at destination
      const newItem = { ...item, day_id: newDays[toDayIndex].id, order_index: toItemIndex };
      newDays[toDayIndex] = {
        ...newDays[toDayIndex],
        items: [
          ...newDays[toDayIndex].items.slice(0, toItemIndex),
          newItem,
          ...newDays[toDayIndex].items.slice(toItemIndex),
        ].map((item, i) => ({ ...item, order_index: i })),
      };
      
      // Re-index source day
      newDays[fromDayIndex].items = newDays[fromDayIndex].items.map((item, i) => ({ 
        ...item, 
        order_index: i 
      }));
      
      return { ...prev, days: newDays };
    });
  }, []);
  
  // Handle drag start
  const handleDragStart = (dayIndex: number, itemIndex: number) => {
    setDraggedItem({ dayIndex, itemIndex });
  };
  
  // Handle drag over
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };
  
  // Handle drop
  const handleDrop = (e: React.DragEvent, toDayIndex: number, toItemIndex?: number) => {
    e.preventDefault();
    if (draggedItem) {
      const targetIndex = toItemIndex ?? itinerary.days[toDayIndex].items.length;
      moveItem(draggedItem.dayIndex, draggedItem.itemIndex, toDayIndex, targetIndex);
      setDraggedItem(null);
    }
  };
  
  // Handle drag end
  const handleDragEnd = () => {
    setDraggedItem(null);
  };
  
  // Add new day
  const addDay = useCallback(() => {
    const newDay: ItineraryDay = {
      id: `day-${Date.now()}`,
      itinerary_id: itinerary.id,
      day_number: itinerary.days.length + 1,
      date: new Date(Date.now() + itinerary.days.length * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      items: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    
    setItinerary(prev => ({
      ...prev,
      days: [...prev.days, newDay],
    }));
    
    setActiveDayIndex(itinerary.days.length);
  }, [itinerary]);
  
  // Remove day
  const removeDay = useCallback((dayIndex: number) => {
    if (itinerary.days.length <= 1) return;
    
    setItinerary(prev => ({
      ...prev,
      days: prev.days.filter((_, i) => i !== dayIndex).map((day, i) => ({
        ...day,
        day_number: i + 1,
      })),
    }));
    
    setActiveDayIndex(Math.min(activeDayIndex, itinerary.days.length - 2));
  }, [itinerary, activeDayIndex]);
  
  // Save itinerary
  const handleSave = async () => {
    try {
      if (initialItinerary?.id) {
        const updated = await updateItineraryMutation.mutateAsync({
          id: initialItinerary.id,
          data: itinerary,
        });
        onSave?.(updated);
      } else {
        const created = await createItineraryMutation.mutateAsync(itinerary);
        onSave?.(created);
      }
    } catch (error) {
      console.error('Failed to save itinerary:', error);
    }
  };
  
  // Calculate totals
  const totalCost = itinerary.days.reduce((sum, day) => 
    sum + day.items.reduce((s, item) => s + (item.estimated_cost || 0), 0), 0
  );
  
  const totalDuration = itinerary.days.reduce((sum, day) => 
    sum + day.items.reduce((s, item) => s + item.duration_minutes, 0), 0
  );
  
  const activeDay = itinerary.days[activeDayIndex];
  
  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-white sticky top-0 z-10">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-semibold text-gray-900">{itinerary.title || 'Untitled Itinerary'}</h2>
            <span className="px-2 py-1 text-xs font-medium rounded-full bg-primary-100 text-primary-700">
              {itinerary.status}
            </span>
          </div>
          
          <div className="flex items-center gap-2">
            {!readOnly && (
              <>
                <button 
                  onClick={handleSave}
                  className="btn-primary flex items-center gap-2"
                >
                  <Save className="w-4 h-4" />
                  Save
                </button>
                <button 
                  onClick={() => onShare?.(itinerary)}
                  className="btn-outline flex items-center gap-2"
                >
                  <Share2 className="w-4 h-4" />
                  Share
                </button>
              </>
            )}
          </div>
        </div>
        
        {/* Summary Stats */}
        <div className="mt-4 flex flex-wrap gap-4 text-sm text-gray-600">
          <div className="flex items-center gap-1">
            <Calendar className="w-4 h-4" />
            <span>{itinerary.days.length} days</span>
          </div>
          <div className="flex items-center gap-1">
            <Clock className="w-4 h-4" />
            <span>{Math.floor(totalDuration / 60)}h {totalDuration % 60}m</span>
          </div>
          <div className="flex items-center gap-1">
            <DollarSign className="w-4 h-4" />
            <span>${totalCost.toFixed(2)}</span>
          </div>
        </div>
      </div>
      
      {/* Day Tabs */}
      <div className="border-b border-gray-200 bg-white sticky top-[60px] z-10">
        <div className="flex overflow-x-auto px-4 py-2 gap-2">
          {itinerary.days.map((day, index) => (
            <button
              key={day.id}
              onClick={() => setActiveDayIndex(index)}
              className={`flex-shrink-0 px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
                index === activeDayIndex
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              Day {day.day_number}
              {day.title && <span className="ml-2">: {day.title}</span>}
            </button>
          ))}
          {!readOnly && (
            <button
              onClick={addDay}
              className="flex-shrink-0 px-4 py-2 rounded-lg text-sm font-medium text-gray-500 hover:bg-gray-100 whitespace-nowrap"
            >
              <Plus className="w-4 h-4 inline mr-1" /> Add Day
            </button>
          )}
        </div>
      </div>
      
      {/* Day Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {activeDay ? (
          <DayView
            day={activeDay}
            dayIndex={activeDayIndex}
            readOnly={readOnly}
            onAddItem={(item) => addItem(activeDayIndex, item)}
            onRemoveItem={(itemId) => removeItem(activeDayIndex, itemId)}
            onDragStart={handleDragStart}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            onDragEnd={handleDragEnd}
            draggedItem={draggedItem}
            allDays={itinerary.days}
            moveItem={moveItem}
            removeDay={() => removeDay(activeDayIndex)}
          />
        ) : (
          <div className="flex items-center justify-center h-64 text-gray-500">
            <p>No days in itinerary. Add a day to get started.</p>
          </div>
        )}
      </div>
    </div>
  );
}

// DayView Component
interface DayViewProps {
  day: ItineraryDay;
  dayIndex: number;
  readOnly: boolean;
  onAddItem: (item: NewItineraryItemInput) => void;
  onRemoveItem: (itemId: string) => void;
  onDragStart: (dayIndex: number, itemIndex: number) => void;
  onDragOver: (e: React.DragEvent) => void;
  onDrop: (e: React.DragEvent, dayIndex: number, itemIndex?: number) => void;
  onDragEnd: () => void;
  draggedItem: { dayIndex: number; itemIndex: number } | null;
  allDays: ItineraryDay[];
  removeDay: () => void;
  moveItem: (fromDay: number, fromItem: number, toDay: number, toItem: number) => void;
}

function DayView({
  day,
  dayIndex,
  readOnly,
  onAddItem,
  onRemoveItem,
  onDragStart,
  onDragOver,
  onDrop,
  onDragEnd,
  draggedItem,
  allDays,
  removeDay,
}: DayViewProps) {
  const [showAddItem, setShowAddItem] = useState(false);
  
  const dayTotalCost = day.items.reduce((sum, item) => sum + (item.estimated_cost || 0), 0);
  const dayTotalDuration = day.items.reduce((sum, item) => sum + item.duration_minutes, 0);
  
  return (
    <div className="space-y-4">
      {/* Day Header */}
      <div className="card p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary-100 flex items-center justify-center">
              <span className="text-xl font-bold text-primary-600">{day.day_number}</span>
            </div>
            <div>
              <input
                type="text"
                value={day.title || ''}
                readOnly={readOnly}
                onChange={(e) => void e}
                placeholder="Day title (optional)"
                className="text-lg font-semibold text-gray-900 bg-transparent border-none focus:outline-none"
              />
              <div className="flex items-center gap-2 text-sm text-gray-500 mt-1">
                <span>{day.date}</span>
                <span>•</span>
                <span>{Math.floor(dayTotalDuration / 60)}h {dayTotalDuration % 60}m</span>
                <span>•</span>
                <span>${dayTotalCost.toFixed(2)}</span>
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {!readOnly && (
              <>
                <button
                  onClick={() => setShowAddItem(!showAddItem)}
                  className="btn-outline flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  Add Item
                </button>
                {allDays.length > 1 && (
                  <button
                    onClick={removeDay}
                    className="btn-outline text-red-600 hover:bg-red-50"
                    title="Remove day"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </>
            )}
          </div>
        </div>
      </div>
      
      {/* Add Item Form */}
      {showAddItem && !readOnly && (
        <AddItemForm
          onClose={() => setShowAddItem(false)}
          onAdd={(item) => {
            onAddItem(item);
            setShowAddItem(false);
          }}
        />
      )}
      
      {/* Items List */}
      <div className="space-y-2">
        {day.items.length === 0 ? (
          <div className="card p-8 text-center text-gray-500">
            <p className="mb-4">No activities planned for this day</p>
            {!readOnly && (
              <button
                onClick={() => setShowAddItem(true)}
                className="btn-primary"
              >
                <Plus className="w-4 h-4 inline mr-1" />
                Add your first activity
              </button>
            )}
          </div>
        ) : (
          day.items.map((item, itemIndex) => (
            <ItineraryItemCard
              key={item.id}
              item={item}
              readOnly={readOnly}
              isDragging={draggedItem?.dayIndex === dayIndex && draggedItem?.itemIndex === itemIndex}
              onDragStart={() => onDragStart(dayIndex, itemIndex)}
              onDragOver={onDragOver}
              onDrop={(e) => onDrop(e, dayIndex, itemIndex)}
              onDragEnd={onDragEnd}
              onRemove={() => onRemoveItem(item.id)}
            />
          ))
        )}
      </div>
    </div>
  );
}

// ItineraryItemCard Component
interface ItineraryItemCardProps {
  item: ItineraryItem;
  readOnly: boolean;
  isDragging: boolean;
  onDragStart: () => void;
  onDragOver: (e: React.DragEvent) => void;
  onDrop: (e: React.DragEvent) => void;
  onDragEnd: () => void;
  onRemove: () => void;
}

function ItineraryItemCard({
  item,
  readOnly,
  isDragging,
  onDragStart,
  onDragOver,
  onDrop,
  onDragEnd,
  onRemove,
}: ItineraryItemCardProps) {
  const [expanded, setExpanded] = useState(false);
  
  const getTypeIcon = (type: ItineraryItemType) => {
    const icons: Record<ItineraryItemType, React.ReactNode> = {
      poi_visit: <MapPin className="w-4 h-4" />,
      transit: <Bus className="w-4 h-4" />,
      meal: <Utensils className="w-4 h-4" />,
      activity: <Star className="w-4 h-4" />,
      rest: <Moon className="w-4 h-4" />,
      custom: <Settings className="w-4 h-4" />,
      accommodation: <Home className="w-4 h-4" />,
    };
    return icons[type] || <MapPin className="w-4 h-4" />;
  };
  
  const getTypeColor = (type: ItineraryItemType) => {
    const colors: Record<ItineraryItemType, string> = {
      poi_visit: 'bg-blue-100 text-blue-700',
      transit: 'bg-green-100 text-green-700',
      meal: 'bg-orange-100 text-orange-700',
      activity: 'bg-purple-100 text-purple-700',
      rest: 'bg-gray-100 text-gray-700',
      custom: 'bg-pink-100 text-pink-700',
      accommodation: 'bg-indigo-100 text-indigo-700',
    };
    return colors[type] || 'bg-gray-100 text-gray-700';
  };
  
  return (
    <div
      className={`card transition-all duration-200 ${isDragging ? 'opacity-50 ring-2 ring-primary-500' : ''}`}
      draggable={!readOnly}
      onDragStart={onDragStart}
      onDragOver={onDragOver}
      onDrop={onDrop}
      onDragEnd={onDragEnd}
    >
      <div className="p-4">
        <div className="flex items-start gap-3">
          {/* Drag Handle */}
          {!readOnly && (
            <button
              onMouseDown={(e) => e.preventDefault()}
              className="text-gray-300 hover:text-gray-500 p-1"
            >
              <GripVertical className="w-5 h-5" />
            </button>
          )}
          
          {/* Time & Type */}
          <div className="flex-shrink-0 w-24 text-right text-sm text-gray-500">
            <div className="font-medium text-gray-900">
              {item.start_time} - {item.end_time}
            </div>
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${getTypeColor(item.type)}`}>
              {item.type.replace('_', ' ')}
            </span>
          </div>
          
          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${getTypeColor(item.type).replace('bg-', 'bg-').replace('text-', 'bg-')}`}>
                {getTypeIcon(item.type)}
              </div>
              <div className="flex-1 min-w-0">
                <h4 className="font-medium text-gray-900 truncate">{item.title}</h4>
                {item.address && (
                  <p className="text-sm text-gray-500 truncate flex items-center gap-1">
                    <MapPin className="w-3 h-3" />
                    {item.address}
                  </p>
                )}
              </div>
            </div>
            
            {/* Expanded Details */}
            {expanded && (
              <div className="mt-3 pt-3 border-t border-gray-100 space-y-2">
                {item.description && (
                  <p className="text-sm text-gray-600">{item.description}</p>
                )}
                <div className="flex flex-wrap gap-4 text-sm text-gray-500">
                  {item.duration_minutes && (
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {item.duration_minutes} min
                    </span>
                  )}
                  {item.transport_mode && (
                    <span className="flex items-center gap-1">
                      <Car className="w-3 h-3" />
                      {item.transport_mode}
                    </span>
                  )}
                  {item.estimated_cost && (
                    <span className="flex items-center gap-1">
                      <DollarSign className="w-3 h-3" />
                      ${item.estimated_cost.toFixed(2)}
                    </span>
                  )}
                </div>
                
                {item.transit_details && (
                  <div className="p-3 bg-gray-50 rounded-lg text-sm">
                    <p className="font-medium text-gray-900 mb-1">Transit Details</p>
                    <p className="text-gray-600">
                      {item.transit_details.route_name} • {item.transit_details.duration_minutes} min • {item.transit_details.transfers} transfers
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
          
          {/* Actions */}
          <div className="flex items-center gap-1">
            <button
              onClick={() => setExpanded(!expanded)}
              className="p-1 text-gray-400 hover:text-gray-600"
            >
              {expanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
            </button>
            {!readOnly && (
              <button
                onClick={onRemove}
                className="p-1 text-gray-400 hover:text-red-500"
              >
                <Trash2 className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// AddItemForm Component
interface AddItemFormProps {
  onClose: () => void;
  onAdd: (item: NewItineraryItemInput) => void;
}

function AddItemForm({ onClose, onAdd }: AddItemFormProps) {
  const [formData, setFormData] = useState<NewItineraryItemInput>({
    type: 'poi_visit',
    title: '',
    description: '',
    start_time: '09:00',
    end_time: '10:00',
    duration_minutes: 60,
    address: '',
    estimated_cost: 0,
    transport_mode: 'walking',
    currency: 'USD',
    is_flexible: false,
    is_required: false,
  });
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onAdd(formData);
  };
  
  return (
    <div className="card p-4 border-primary-200 bg-primary-50">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="flex items-center justify-between">
          <h4 className="font-medium text-gray-900">Add Activity</h4>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Type</label>
            <select
              value={formData.type}
              onChange={(e) => setFormData({ ...formData, type: e.target.value as ItineraryItemType })}
              className="input"
            >
              <option value="poi_visit">Place Visit</option>
              <option value="meal">Meal</option>
              <option value="activity">Activity</option>
              <option value="transit">Transit</option>
              <option value="rest">Rest/Break</option>
              <option value="accommodation">Accommodation</option>
              <option value="custom">Custom</option>
            </select>
          </div>
          
          <div>
            <label className="label">Transport</label>
            <select
              value={formData.transport_mode}
              onChange={(e) => setFormData({ ...formData, transport_mode: e.target.value as TransportMode })}
              className="input"
            >
              <option value="walking">Walking</option>
              <option value="transit">Transit</option>
              <option value="driving">Driving</option>
              <option value="cycling">Cycling</option>
              <option value="rideshare">Rideshare</option>
            </select>
          </div>
        </div>
        
        <div>
          <label className="label">Title</label>
          <input
            type="text"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            placeholder="Activity title"
            className="input"
            required
          />
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Start Time</label>
            <input
              type="time"
              value={formData.start_time}
              onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
              className="input"
            />
          </div>
          <div>
            <label className="label">End Time</label>
            <input
              type="time"
              value={formData.end_time}
              onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
              className="input"
            />
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Duration (min)</label>
            <input
              type="number"
              value={formData.duration_minutes}
              onChange={(e) => setFormData({ ...formData, duration_minutes: parseInt(e.target.value) })}
              className="input"
              min="1"
            />
          </div>
          <div>
            <label className="label">Est. Cost ($)</label>
            <input
              type="number"
              value={formData.estimated_cost}
              onChange={(e) => setFormData({ ...formData, estimated_cost: parseFloat(e.target.value) })}
              className="input"
              min="0"
              step="0.01"
            />
          </div>
        </div>
        
        <div>
          <label className="label">Address</label>
          <input
            type="text"
            value={formData.address}
            onChange={(e) => setFormData({ ...formData, address: e.target.value })}
            placeholder="Address or location"
            className="input"
          />
        </div>
        
        <div>
          <label className="label">Description</label>
          <textarea
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            placeholder="Notes or details"
            className="input"
            rows={2}
          />
        </div>
        
        <div className="flex gap-2">
          <button type="button" onClick={onClose} className="btn-outline flex-1">Cancel</button>
          <button type="submit" className="btn-primary flex-1">Add Activity</button>
        </div>
      </form>
    </div>
  );
}

  // Helper function
function createEmptyItinerary(): Itinerary {
  return {
    id: `itinerary-${Date.now()}`,
    user_id: '',
    title: '',
    status: 'draft',
    start_date: new Date().toISOString().split('T')[0],
    end_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    budget_level: 'mid_range',
    pace: 'moderate',
    interests: [],
    accessibility_needs: [],
    dietary_restrictions: [],
    transport_preferences: ['walking', 'transit'],
    tags: [],
    is_public: false,
    collaborators: [],
    currency: 'USD',
    days: [{
      id: `day-1`,
      itinerary_id: '',
      day_number: 1,
      date: new Date().toISOString().split('T')[0],
      items: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
}

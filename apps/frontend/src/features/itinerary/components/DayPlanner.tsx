interface DayPlannerProps {
  day: {
    day_number: number;
    title: string;
    items: Array<{
      time: string;
      name: string;
      duration: number;
    }>;
  };
  onAddItem?: () => void;
  onRemoveItem?: (index: number) => void;
}

export function DayPlanner({ day, onAddItem, onRemoveItem }: DayPlannerProps) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex justify-between items-center mb-3">
        <h4 className="font-medium">Day {day.day_number}: {day.title}</h4>
        {onAddItem && (
          <button onClick={onAddItem} className="text-sm text-primary-600 hover:text-primary-700">+ Add</button>
        )}
      </div>
      <div className="space-y-2">
        {day.items.map((item, i) => (
          <div key={i} className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50">
            <span className="text-xs text-gray-500 w-12">{item.time}</span>
            <span className="text-sm flex-1">{item.name}</span>
            <span className="text-xs text-gray-400">{item.duration}m</span>
            {onRemoveItem && (
              <button onClick={() => onRemoveItem(i)} className="text-gray-400 hover:text-red-500">×</button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

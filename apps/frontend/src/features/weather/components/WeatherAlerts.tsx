interface WeatherAlertsProps {
  alerts: Array<{
    title: string;
    description: string;
    severity: 'minor' | 'moderate' | 'severe' | 'extreme';
    start: string;
    end: string;
  }>;
}

export function WeatherAlerts({ alerts }: WeatherAlertsProps) {
  if (alerts.length === 0) return null;

  const severityColors = {
    minor: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    moderate: 'bg-orange-50 border-orange-200 text-orange-800',
    severe: 'bg-red-50 border-red-200 text-red-800',
    extreme: 'bg-purple-50 border-purple-200 text-purple-800',
  };

  return (
    <div className="space-y-2">
      {alerts.map((alert, i) => (
        <div key={i} className={`p-3 rounded-lg border ${severityColors[alert.severity]}`}>
          <div className="flex items-center gap-2">
            <span className="font-medium text-sm">{alert.title}</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-white/50">{alert.severity}</span>
          </div>
          <p className="text-sm mt-1 opacity-80">{alert.description}</p>
        </div>
      ))}
    </div>
  );
}

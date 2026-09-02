interface RealTimeDeparturesProps {
  departures: Array<{
    line: string;
    destination: string;
    time: string;
    delay?: number;
  }>;
  stopName?: string;
}

export function RealTimeDepartures({ departures, stopName }: RealTimeDeparturesProps) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      {stopName && <h4 className="font-medium text-sm mb-3">{stopName}</h4>}
      <div className="space-y-2">
        {departures.map((dep, i) => (
          <div key={i} className="flex justify-between items-center py-1 border-b border-gray-100 last:border-0">
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 bg-primary-100 text-primary-700 rounded text-xs font-medium">{dep.line}</span>
              <span className="text-sm">{dep.destination}</span>
            </div>
            <div className="flex items-center gap-2">
              {dep.delay && dep.delay > 0 && (
                <span className="text-xs text-red-500">+{dep.delay}m</span>
              )}
              <span className="text-sm font-medium">{dep.time}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

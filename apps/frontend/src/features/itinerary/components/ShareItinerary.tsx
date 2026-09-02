interface ShareItineraryProps {
  shareToken?: string;
  onGenerateLink: () => void;
  onCopyLink: () => void;
}

export function ShareItinerary({ shareToken, onGenerateLink, onCopyLink }: ShareItineraryProps) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <h4 className="font-medium text-sm mb-3">Share Itinerary</h4>
      {shareToken ? (
        <div className="flex gap-2">
          <input
            type="text"
            readOnly
            value={`${window.location.origin}/itineraries/shared/${shareToken}`}
            className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm bg-gray-50"
          />
          <button onClick={onCopyLink} className="px-3 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700">
            Copy
          </button>
        </div>
      ) : (
        <button onClick={onGenerateLink} className="w-full px-4 py-2 border border-dashed border-gray-300 rounded-lg text-sm text-gray-600 hover:border-primary-500 hover:text-primary-600">
          Generate Share Link
        </button>
      )}
    </div>
  );
}

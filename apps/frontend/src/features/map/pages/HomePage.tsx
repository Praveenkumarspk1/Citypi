import { MapPin, Search, Filter, Layers, Navigation, Heart, Star } from 'lucide-react';
import { useState } from 'react';

export function HomePage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'list' | 'map'>('list');

  const categories = [
    { id: 'all', label: 'All', icon: Layers },
    { id: 'restaurant', label: 'Restaurants', icon: MapPin },
    { id: 'cafe', label: 'Cafes', icon: Heart },
    { id: 'attraction', label: 'Attractions', icon: Star },
    { id: 'museum', label: 'Museums', icon: Navigation },
    { id: 'park', label: 'Parks', icon: Filter },
    { id: 'shopping', label: 'Shopping', icon: Search },
    { id: 'hotel', label: 'Hotels', icon: Layers },
  ];

  const mockPOIs = [
    {
      id: '1',
      name: 'Central Park',
      category: 'park',
      rating: 4.8,
      reviewCount: 1250,
      distance: '0.5 km',
      image: 'https://images.unsplash.com/photo-1496307653780-42ee777d2d48?w=400',
      address: 'New York, NY',
    },
    {
      id: '2',
      name: 'The Metropolitan Museum of Art',
      category: 'museum',
      rating: 4.9,
      reviewCount: 890,
      distance: '1.2 km',
      image: 'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=400',
      address: '1000 5th Ave, New York, NY',
    },
    {
      id: '3',
      name: 'Joe\'s Pizza',
      category: 'restaurant',
      rating: 4.6,
      reviewCount: 2100,
      distance: '0.3 km',
      image: 'https://images.unsplash.com/photo-1565299585323-38d6b0865b47?w=400',
      address: '1435 Broadway, New York, NY',
    },
    {
      id: '4',
      name: 'Blue Bottle Coffee',
      category: 'cafe',
      rating: 4.5,
      reviewCount: 567,
      distance: '0.8 km',
      image: 'https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=400',
      address: '75 Rockefeller Plaza, New York, NY',
    },
    {
      id: '5',
      name: 'Times Square',
      category: 'attraction',
      rating: 4.4,
      reviewCount: 5400,
      distance: '1.5 km',
      image: 'https://images.unsplash.com/photo-1504196606672-aef5c9cefc92?w=400',
      address: 'Manhattan, NY',
    },
    {
      id: '6',
      name: 'MoMA',
      category: 'museum',
      rating: 4.7,
      reviewCount: 1200,
      distance: '1.0 km',
      image: 'https://images.unsplash.com/photo-1533900298318-6b8da08a523e?w=400',
      address: '11 W 53rd St, New York, NY',
    },
  ];

  const filteredPOIs = mockPOIs.filter(poi => 
    selectedCategory === 'all' || poi.category === selectedCategory
  );

  const categoryColors: Record<string, string> = {
    restaurant: 'bg-red-100 text-red-700',
    cafe: 'bg-brown-100 text-brown-700',
    attraction: 'bg-yellow-100 text-yellow-700',
    museum: 'bg-purple-100 text-purple-700',
    park: 'bg-green-100 text-green-700',
    shopping: 'bg-pink-100 text-pink-700',
    hotel: 'bg-blue-100 text-blue-700',
  };

  return (
    <div className="space-y-6">
      {/* Hero Section */}
      <div className="relative rounded-2xl bg-gradient-to-br from-primary-600 to-primary-800 p-8 text-white overflow-hidden">
        <div className="relative z-10 max-w-2xl">
          <h1 className="text-3xl sm:text-4xl font-bold mb-4">
            Discover Your City
          </h1>
          <p className="text-primary-100 text-lg mb-6">
            Find the best places, plan your perfect day, and explore like a local with AI-powered recommendations.
          </p>
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search for places, restaurants, attractions..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder:text-primary-200 focus:outline-none focus:ring-2 focus:ring-white/50 focus:border-transparent"
              />
            </div>
            <button className="btn-primary btn-lg whitespace-nowrap">
              <Navigation className="w-5 h-5 mr-2" />
              Plan a Trip
            </button>
          </div>
        </div>
        <div className="absolute inset-0 opacity-10">
          <MapPin className="w-full h-full" style={{ transform: 'rotate(45deg)' }} />
        </div>
      </div>

      {/* Category Filter */}
      <div className="card">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Categories</h2>
        </div>
        <div className="p-4">
          <div className="flex flex-wrap gap-2">
            {categories.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all ${
                  selectedCategory === cat.id
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <cat.icon className="w-4 h-4" />
                {cat.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* View Toggle & Results */}
      <div className="card">
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">
            {filteredPOIs.length} places found
          </h2>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded-lg transition-colors ${
                viewMode === 'list' ? 'bg-primary-100 text-primary-700' : 'text-gray-500 hover:bg-gray-100'
              }`}
            >
              <Layers className="w-5 h-5" />
            </button>
            <button
              onClick={() => setViewMode('map')}
              className={`p-2 rounded-lg transition-colors ${
                viewMode === 'map' ? 'bg-primary-100 text-primary-700' : 'text-gray-500 hover:bg-gray-100'
              }`}
            >
              <MapPin className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="p-4">
          {viewMode === 'list' ? (
            <div className="space-y-4">
              {filteredPOIs.map((poi) => (
                <div
                  key={poi.id}
                  className="flex gap-4 p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors cursor-pointer"
                >
                  <div className="relative w-24 h-24 flex-shrink-0 rounded-lg overflow-hidden">
                    <img
                      src={poi.image}
                      alt={poi.name}
                      className="w-full h-full object-cover"
                    />
                    <span className={`absolute top-2 right-2 px-2 py-1 rounded-full text-xs font-medium ${categoryColors[poi.category]}`}>
                      {poi.category}
                    </span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="font-semibold text-gray-900 truncate">{poi.name}</h3>
                      <div className="flex items-center gap-1 text-yellow-500">
                        <Star className="w-4 h-4 fill-current" />
                        <span className="text-sm font-medium">{poi.rating}</span>
                        <span className="text-gray-500 text-sm">({poi.reviewCount})</span>
                      </div>
                    </div>
                    <p className="text-gray-500 text-sm mt-1 truncate">{poi.address}</p>
                    <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                      <span className="flex items-center gap-1">
                        <MapPin className="w-3.5 h-3.5" />
                        {poi.distance}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="aspect-video bg-gray-100 rounded-xl flex items-center justify-center">
              <div className="text-center text-gray-500">
                <MapPin className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>Map view coming soon</p>
                <p className="text-sm">Interactive map with POI markers</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { title: 'Plan with AI', desc: 'Get personalized itineraries', icon: Navigation, color: 'primary' },
          { title: 'Real-time Transit', desc: 'Live bus & train updates', icon: MapPin, color: 'blue' },
          { title: 'Weather Alerts', desc: 'Stay prepared for any weather', icon: Star, color: 'yellow' },
          { title: 'Share & Collaborate', desc: 'Plan trips with friends', icon: Heart, color: 'pink' },
        ].map((action, i) => (
          <div key={i} className="card-hover p-6 text-center">
            <div className={`w-12 h-12 rounded-xl bg-${action.color}-100 flex items-center justify-center mx-auto mb-4`}>
              <action.icon className={`w-6 h-6 text-${action.color}-600`} />
            </div>
            <h3 className="font-semibold text-gray-900 mb-1">{action.title}</h3>
            <p className="text-gray-500 text-sm">{action.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
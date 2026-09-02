import { Link, useLocation } from 'react-router-dom';

const navItems = [
  { path: '/', label: 'Map', icon: 'map' },
  { path: '/chat', label: 'Chat', icon: 'chat' },
  { path: '/itinerary', label: 'Itinerary', icon: 'calendar' },
  { path: '/transit', label: 'Transit', icon: 'transit' },
  { path: '/weather', label: 'Weather', icon: 'weather' },
  { path: '/profile', label: 'Profile', icon: 'user' },
];

export function Sidebar() {
  const location = useLocation();

  return (
    <aside className="w-16 md:w-56 bg-white border-r border-gray-200 flex-shrink-0">
      <nav className="p-2 space-y-1">
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
              location.pathname === item.path
                ? 'bg-primary-50 text-primary-700 font-medium'
                : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            <span className="w-5 h-5 flex items-center justify-center text-center">{item.icon[0].toUpperCase()}</span>
            <span className="hidden md:inline">{item.label}</span>
          </Link>
        ))}
      </nav>
    </aside>
  );
}

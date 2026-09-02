import { Link } from 'react-router-dom';

export function Header() {
  return (
    <header className="bg-white border-b border-gray-200 px-4 py-3">
      <div className="flex items-center justify-between">
        <Link to="/" className="text-xl font-bold text-primary-600">
          Smart City Concierge
        </Link>
        <nav className="flex items-center gap-4">
          <Link to="/chat" className="text-sm text-gray-600 hover:text-primary-600">Chat</Link>
          <Link to="/transit" className="text-sm text-gray-600 hover:text-primary-600">Transit</Link>
          <Link to="/weather" className="text-sm text-gray-600 hover:text-primary-600">Weather</Link>
          <Link to="/profile" className="text-sm text-gray-600 hover:text-primary-600">Profile</Link>
        </nav>
      </div>
    </header>
  );
}

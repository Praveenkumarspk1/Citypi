import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from '@shared/stores/authStore';
import { Layout } from '@shared/components/Layout';
import { LoginPage } from '@features/user/pages/LoginPage';
import { RegisterPage } from '@features/user/pages/RegisterPage';
import { ForgotPasswordPage } from '@features/user/pages/ForgotPasswordPage';
import { ResetPasswordPage } from '@features/user/pages/ResetPasswordPage';
import { VerifyEmailPage } from '@features/user/pages/VerifyEmailPage';
import { HomePage } from '@features/map/pages/HomePage';
import { ChatPage } from '@features/chat/pages/ChatPage';
import { ItineraryPage } from '@features/itinerary/pages/ItineraryPage';
import { TransitPage } from '@features/transit/pages/TransitPage';
import { WeatherPage } from '@features/weather/pages/WeatherPage';
import { ProfilePage } from '@features/user/pages/ProfilePage';
import { SettingsPage } from '@features/user/pages/SettingsPage';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuthStore();
  
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent"></div>
      </div>
    );
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuthStore();
  
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent"></div>
      </div>
    );
  }
  
  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }
  
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={
        <PublicRoute>
          <LoginPage />
        </PublicRoute>
      } />
      <Route path="/register" element={
        <PublicRoute>
          <RegisterPage />
        </PublicRoute>
      } />
      <Route path="/forgot-password" element={
        <PublicRoute>
          <ForgotPasswordPage />
        </PublicRoute>
      } />
      <Route path="/reset-password" element={
        <PublicRoute>
          <ResetPasswordPage />
        </PublicRoute>
      } />
      <Route path="/verify-email" element={
        <PublicRoute>
          <VerifyEmailPage />
        </PublicRoute>
      } />
      <Route element={
        <ProtectedRoute>
          <Layout />
        </ProtectedRoute>
      }>
        <Route path="/" element={<HomePage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/itinerary" element={<ItineraryPage />} />
        <Route path="/itinerary/:id" element={<ItineraryPage />} />
        <Route path="/transit" element={<TransitPage />} />
        <Route path="/weather" element={<WeatherPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

import { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

const LoginPage = lazy(() => import('./features/user/pages/LoginPage'));
const RegisterPage = lazy(() => import('./features/user/pages/RegisterPage'));
const ForgotPasswordPage = lazy(() => import('./features/user/pages/ForgotPasswordPage'));
const ResetPasswordPage = lazy(() => import('./features/user/pages/ResetPasswordPage'));
const VerifyEmailPage = lazy(() => import('./features/user/pages/VerifyEmailPage'));
const HomePage = lazy(() => import('./features/map/pages/HomePage'));
const ChatPage = lazy(() => import('./features/chat/pages/ChatPage'));
const ItineraryPage = lazy(() => import('./features/itinerary/pages/ItineraryPage'));
const TransitPage = lazy(() => import('./features/transit/pages/TransitPage'));
const WeatherPage = lazy(() => import('./features/weather/pages/WeatherPage'));
const ProfilePage = lazy(() => import('./features/user/pages/ProfilePage'));
const SettingsPage = lazy(() => import('./features/user/pages/SettingsPage'));

function PageLoader() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent" />
    </div>
  );
}

export function AppRoutes() {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/verify-email" element={<VerifyEmailPage />} />

        {/* Protected routes */}
        <Route path="/" element={<HomePage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/chat/:conversationId" element={<ChatPage />} />
        <Route path="/itinerary" element={<ItineraryPage />} />
        <Route path="/itinerary/:itineraryId" element={<ItineraryPage />} />
        <Route path="/transit" element={<TransitPage />} />
        <Route path="/weather" element={<WeatherPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/settings" element={<SettingsPage />} />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}

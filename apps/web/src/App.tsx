import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom"
import { ThemeProvider } from "next-themes"
import { Toaster } from "sonner"
import LoginPage from "./pages/login"
import RegisterPage from "./pages/register"
import ChatPage from "./pages/chat"
import ProfilePage from "./pages/profile"
import SettingsPage from "./pages/settings"
import AuthCallbackPage from "./pages/auth-callback"
import GoogleSetupPage from "./pages/google-setup"
import AuthErrorPage from "./pages/auth-error"
import ProtectedRoute from "./components/protected-route"

function App() {
  return (
    <ThemeProvider
      attribute="class"
      defaultTheme="dark"
      enableSystem
      storageKey="uit-ai-theme"
      disableTransitionOnChange
    >
      <Toaster richColors position="top-right" />
      <Router>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/auth/callback" element={<AuthCallbackPage />} />
          <Route path="/auth/google-setup" element={<GoogleSetupPage />} />
          <Route path="/auth/error" element={<AuthErrorPage />} />
          <Route
            path="/chat"
            element={
              <ProtectedRoute>
                <ChatPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <SettingsPage />
              </ProtectedRoute>
            }
          />
          <Route path="/" element={<Navigate to="/chat" replace />} />
        </Routes>
      </Router>
    </ThemeProvider>
  )
}

export default App

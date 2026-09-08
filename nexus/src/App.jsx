import {
  Navigate,
  Outlet,
  Route,
  Routes,
} from 'react-router-dom'

import Login from './pages/Login'
import DashboardLive from './pages/DashboardLive'
import InvestigationsLive from './pages/InvestigationsLive'
import NetworkLive from './pages/NetworkLive'
import DataExplorer from './pages/DataExplorer'

import {
  AlertsPage,
  EvidencePage,
  ReportsPage,
} from './pages/DemoPages'

import {
  ActiveCaseProvider,
} from './context/ActiveCaseContext'

import {
  useAuth,
} from './context/AuthContext'

function ProtectedRoute() {
  const {
    isAuthenticated,
    loading,
  } = useAuth()

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-base-950">
        <div className="text-center">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />

          <p className="mt-4 text-sm text-ink-500">
            Initializing secure workspace...
          </p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <Navigate
        to="/login"
        replace
      />
    )
  }

  return (
    <ActiveCaseProvider>
      <Outlet />
    </ActiveCaseProvider>
  )
}

function RootRedirect() {
  const {
    isAuthenticated,
    loading,
  } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen bg-base-950" />
    )
  }

  return (
    <Navigate
      to={isAuthenticated ? '/dashboard' : '/login'}
      replace
    />
  )
}

function App() {
  return (
    <Routes>
      {/* Public route */}
      <Route
        path="/login"
        element={<Login />}
      />

      {/* Protected routes */}
      <Route element={<ProtectedRoute />}>
        <Route
          path="/dashboard"
          element={<DashboardLive />}
        />

        <Route
          path="/investigations"
          element={<InvestigationsLive />}
        />

        <Route
          path="/cases"
          element={<InvestigationsLive />}
        />

        {/*
          The old Investigation page was crashing.
          Redirect investigation links to the working live network page.
        */}
        <Route
          path="/investigation/:caseId"
          element={
            <Navigate
              to="/network"
              replace
            />
          }
        />

        <Route
          path="/network"
          element={<NetworkLive />}
        />

        <Route
          path="/network/:caseId"
          element={<NetworkLive />}
        />

        <Route
          path="/evidence"
          element={<EvidencePage />}
        />

        <Route
          path="/alerts"
          element={<AlertsPage />}
        />

        <Route
          path="/reports"
          element={<ReportsPage />}
        />

        <Route
          path="/reports/:caseId"
          element={<ReportsPage />}
        />

        <Route
          path="/data-explorer"
          element={<DataExplorer />}
        />
      </Route>

      {/* Starting route */}
      <Route
        path="/"
        element={<RootRedirect />}
      />

      {/* Invalid URL fallback */}
      <Route
        path="*"
        element={<RootRedirect />}
      />
    </Routes>
  )
}

export default App
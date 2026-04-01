import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import AppLayout from './components/ui/Layout'
import LoginPage     from './pages/Login'
import DashboardPage from './pages/Dashboard'
import OperationsPage from './pages/Operations'
import ReportsPage   from './pages/Reports'
import BalancesPage  from './pages/Balances'
import CategoriesPage from './pages/Categories'
import UsersPage     from './pages/Users'
import NotFoundPage from './pages/NotFound'

function RequireAuth({ children }) {
  const { token } = useAuthStore()
  if (!token) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <RequireAuth>
              <AppLayout />
            </RequireAuth>
          }
        >
          <Route index element={<Navigate to="/operations" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="operations"  element={<OperationsPage />} />
          <Route path="reports"     element={<ReportsPage />} />
          <Route path="balances"    element={<BalancesPage />} />
          <Route path="categories"  element={<CategoriesPage />} />
          <Route path="users"       element={<UsersPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  )
}

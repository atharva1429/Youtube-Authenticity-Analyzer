import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'

import { AuthProvider } from './context/AuthContext'

import ProtectedRoute from './components/ProtectedRoute'

import Login from './pages/Login'

import Register from './pages/Register'

import Dashboard from './pages/Dashboard'

import ReportPage from './pages/ReportPage'



export default function App() {

  return (

    <AuthProvider>

      <BrowserRouter>

        <Routes>

          <Route path="/" element={<Navigate to="/dashboard" replace />} />

          <Route path="/login" element={<Login />} />

          <Route path="/register" element={<Register />} />

          <Route

            path="/dashboard"

            element={

              <ProtectedRoute>

                <Dashboard />

              </ProtectedRoute>

            }

          />

          <Route

            path="/report/:id"

            element={

              <ProtectedRoute>

                <ReportPage />

              </ProtectedRoute>

            }

          />

          <Route path="*" element={<Navigate to="/dashboard" replace />} />

        </Routes>

      </BrowserRouter>

    </AuthProvider>

  )

}



import React, { Suspense, lazy } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ProtectedRoute } from './components/ProtectedRoute'
import { UpdateBanner } from './components/common/UpdateBanner'

// Code-splitting con lazy loading para aligerar la carga y memoria en celulares de meseros y cocina
const Login = lazy(() => import('./pages/Login').then(m => ({ default: m.Login })))
const Mesero = lazy(() => import('./pages/Mesero').then(m => ({ default: m.Mesero })))
const Cocina = lazy(() => import('./pages/Cocina').then(m => ({ default: m.Cocina })))
const Caja = lazy(() => import('./pages/Caja').then(m => ({ default: m.Caja })))
const Admin = lazy(() => import('./pages/Admin').then(m => ({ default: m.Admin })))

const LoadingFallback: React.FC = () => (
  <div className="flex min-h-screen items-center justify-center bg-gray-950 text-amber-500">
    <div className="flex flex-col items-center gap-3">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-amber-500 border-t-transparent" />
      <span className="text-sm font-medium tracking-wide text-gray-300">Cargando Mr. Burger...</span>
    </div>
  </div>
)

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <UpdateBanner />
        <Suspense fallback={<LoadingFallback />}>
          <Routes>
            {/* Ruta pública de Autenticación */}
            <Route path="/login" element={<Login />} />

            {/* Rutas Protegidas por Rol */}
            <Route
              path="/mesero"
              element={
                <ProtectedRoute allowedRoles={['mesero', 'admin']}>
                  <Mesero />
                </ProtectedRoute>
              }
            />
            <Route
              path="/cocina"
              element={
                <ProtectedRoute allowedRoles={['cocina', 'admin']}>
                  <Cocina />
                </ProtectedRoute>
              }
            />
            <Route
              path="/caja"
              element={
                <ProtectedRoute allowedRoles={['cajero', 'admin']}>
                  <Caja />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <Admin />
                </ProtectedRoute>
              }
            />

            {/* Redirección por defecto */}
            <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>
        </Suspense>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App

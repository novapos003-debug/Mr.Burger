import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ProtectedRoute } from './components/ProtectedRoute'
import { Login } from './pages/Login'
import { Mesero } from './pages/Mesero'
import { Cocina } from './pages/Cocina'
import { Caja } from './pages/Caja'
import { Admin } from './pages/Admin'
import { UpdateBanner } from './components/common/UpdateBanner'

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <UpdateBanner />
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
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App

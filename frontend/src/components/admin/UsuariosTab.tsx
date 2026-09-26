import React, { useState, useEffect } from 'react'
import {
  Users,
  UserPlus,
  KeyRound,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Lock,
  Search,
  UserCheck,
  UserX,
  X,
  RefreshCw,
} from 'lucide-react'
import {
  getUsuariosApi,
  crearUsuarioApi,
  resetPasswordUsuarioApi,
  cambiarEstadoUsuarioApi,
} from '../../api/admin'
import { cambiarMiPasswordApi } from '../../api/auth'
import type { UsuarioAdminItem, UsuarioCreateInput } from '../../types/admin'

export const UsuariosTab: React.FC = () => {
  const [usuarios, setUsuarios] = useState<UsuarioAdminItem[]>([])
  const [loading, setLoading] = useState(true)
  const [filtroTexto, setFiltroTexto] = useState('')
  const [filtroRol, setFiltroRol] = useState<string>('TODOS')

  // Estado formulario de cambio de mi propia contraseña
  const [miPassActual, setMiPassActual] = useState('')
  const [miPassNueva, setMiPassNueva] = useState('')
  const [miPassConfirmar, setMiPassConfirmar] = useState('')
  const [guardandoMiPass, setGuardandoMiPass] = useState(false)
  const [miPassMensaje, setMiPassMensaje] = useState<{ tipo: 'ok' | 'error'; texto: string } | null>(null)

  // Modales
  const [modalCrearAbierto, setModalCrearAbierto] = useState(false)
  const [modalResetAbierto, setModalResetAbierto] = useState(false)
  const [usuarioSeleccionado, setUsuarioSeleccionado] = useState<UsuarioAdminItem | null>(null)
  const [resetNuevaPass, setResetNuevaPass] = useState('')
  const [guardandoReset, setGuardandoReset] = useState(false)

  // Formulario nuevo usuario
  const [nuevoForm, setNuevoForm] = useState<UsuarioCreateInput>({
    nombre: '',
    usuario: '',
    password: '',
    rol: 'mesero',
  })
  const [guardandoNuevo, setGuardandoNuevo] = useState(false)
  const [errorNuevo, setErrorNuevo] = useState('')

  const cargarUsuarios = async () => {
    try {
      setLoading(true)
      const data = await getUsuariosApi()
      setUsuarios(data)
    } catch (err: any) {
      console.error('Error cargando usuarios:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    cargarUsuarios()
  }, [])

  // Cambiar mi propia contraseña
  const handleCambiarMiPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setMiPassMensaje(null)

    if (miPassNueva.length < 4) {
      setMiPassMensaje({ tipo: 'error', texto: 'La nueva contraseña debe tener al menos 4 caracteres.' })
      return
    }

    if (miPassNueva !== miPassConfirmar) {
      setMiPassMensaje({ tipo: 'error', texto: 'La nueva contraseña y su confirmación no coinciden.' })
      return
    }

    try {
      setGuardandoMiPass(true)
      const res = await cambiarMiPasswordApi(miPassActual, miPassNueva)
      setMiPassMensaje({ tipo: 'ok', texto: res.mensaje || '¡Tu contraseña ha sido actualizada con éxito!' })
      setMiPassActual('')
      setMiPassNueva('')
      setMiPassConfirmar('')
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Error al cambiar contraseña. Verifica tu clave actual.'
      setMiPassMensaje({ tipo: 'error', texto: msg })
    } finally {
      setGuardandoMiPass(false)
    }
  }

  // Crear nuevo usuario
  const handleCrearUsuario = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorNuevo('')

    if (!nuevoForm.nombre.trim() || !nuevoForm.usuario.trim() || !nuevoForm.password.trim()) {
      setErrorNuevo('Todos los campos son obligatorios.')
      return
    }

    if (nuevoForm.password.length < 4) {
      setErrorNuevo('La contraseña debe tener mínimo 4 caracteres.')
      return
    }

    try {
      setGuardandoNuevo(true)
      await crearUsuarioApi(nuevoForm)
      setModalCrearAbierto(false)
      setNuevoForm({ nombre: '', usuario: '', password: '', rol: 'mesero' })
      cargarUsuarios()
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Error al crear el usuario.'
      setErrorNuevo(msg)
    } finally {
      setGuardandoNuevo(false)
    }
  }

  // Resetear contraseña de un empleado
  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!usuarioSeleccionado) return

    if (resetNuevaPass.length < 4) {
      alert('La nueva contraseña debe tener mínimo 4 caracteres.')
      return
    }

    try {
      setGuardandoReset(true)
      await resetPasswordUsuarioApi(usuarioSeleccionado.id, resetNuevaPass)
      setModalResetAbierto(false)
      setResetNuevaPass('')
      setUsuarioSeleccionado(null)
      alert(`Contraseña actualizada exitosamente para ${usuarioSeleccionado.nombre}`)
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error al restablecer la contraseña.')
    } finally {
      setGuardandoReset(false)
    }
  }

  // Cambiar estado activo/inactivo
  const handleToggleEstado = async (u: UsuarioAdminItem) => {
    const nuevoEstado = !u.activo
    const accion = nuevoEstado ? 'activar' : 'desactivar'
    if (!window.confirm(`¿Estás seguro de que deseas ${accion} el acceso de ${u.nombre}?`)) {
      return
    }

    try {
      await cambiarEstadoUsuarioApi(u.id, nuevoEstado)
      cargarUsuarios()
    } catch (err: any) {
      alert(err.response?.data?.detail || `Error al ${accion} el usuario.`)
    }
  }

  const usuariosFiltrados = usuarios.filter((u) => {
    const matchTexto =
      u.nombre.toLowerCase().includes(filtroTexto.toLowerCase()) ||
      u.usuario.toLowerCase().includes(filtroTexto.toLowerCase())
    const matchRol = filtroRol === 'TODOS' || u.rol.toLowerCase() === filtroRol.toLowerCase()
    return matchTexto && matchRol
  })

  const getRolBadge = (rol: string) => {
    switch (rol.toLowerCase()) {
      case 'admin':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-900/50 text-purple-300 border border-purple-700/50">
            Administrador
          </span>
        )
      case 'cajero':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-900/50 text-amber-300 border border-amber-700/50">
            Cajero
          </span>
        )
      case 'mesero':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-900/50 text-blue-300 border border-blue-700/50">
            Mesero
          </span>
        )
      case 'cocina':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-900/50 text-emerald-300 border border-emerald-700/50">
            Cocina (KDS)
          </span>
        )
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-300 border border-slate-700">
            {rol}
          </span>
        )
    }
  }

  return (
    <div className="space-y-6">
      {/* Encabezado y Acción Principal */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-slate-900/80 p-5 rounded-xl border border-slate-800 shadow-lg">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Users className="w-6 h-6 text-amber-500" />
            Equipo y Seguridad de Acceso
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Administra los roles del personal (Caja, Meseros, Cocina) y las contraseñas de acceso.
          </p>
        </div>
        <button
          onClick={() => setModalCrearAbierto(true)}
          className="inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-lg transition-colors shadow-md shadow-amber-500/20"
        >
          <UserPlus className="w-5 h-5" />
          Nuevo Empleado
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Tarjeta 1: Mi Seguridad (Cambio de contraseña personal) */}
        <div className="lg:col-span-1 bg-slate-900/90 rounded-xl border border-slate-800 p-5 shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-3 pb-4 border-b border-slate-800 mb-4">
              <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Mi Contraseña</h3>
                <p className="text-xs text-slate-400">Seguridad de tu cuenta Administradora</p>
              </div>
            </div>

            {miPassMensaje && (
              <div
                className={`p-3 rounded-lg mb-4 text-xs flex items-start gap-2 ${
                  miPassMensaje.tipo === 'ok'
                    ? 'bg-emerald-950/60 border border-emerald-800 text-emerald-300'
                    : 'bg-rose-950/60 border border-rose-800 text-rose-300'
                }`}
              >
                {miPassMensaje.tipo === 'ok' ? (
                  <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
                ) : (
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                )}
                <span>{miPassMensaje.texto}</span>
              </div>
            )}

            <form onSubmit={handleCambiarMiPassword} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Contraseña Actual
                </label>
                <div className="relative">
                  <input
                    type="password"
                    required
                    value={miPassActual}
                    onChange={(e) => setMiPassActual(e.target.value)}
                    placeholder="••••••••"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-amber-500"
                  />
                  <Lock className="w-4 h-4 text-slate-600 absolute right-3 top-2.5" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Nueva Contraseña
                </label>
                <div className="relative">
                  <input
                    type="password"
                    required
                    value={miPassNueva}
                    onChange={(e) => setMiPassNueva(e.target.value)}
                    placeholder="Mínimo 4 caracteres"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-amber-500"
                  />
                  <KeyRound className="w-4 h-4 text-slate-600 absolute right-3 top-2.5" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Confirmar Nueva Contraseña
                </label>
                <div className="relative">
                  <input
                    type="password"
                    required
                    value={miPassConfirmar}
                    onChange={(e) => setMiPassConfirmar(e.target.value)}
                    placeholder="Repite la contraseña"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-amber-500"
                  />
                  <KeyRound className="w-4 h-4 text-slate-600 absolute right-3 top-2.5" />
                </div>
              </div>

              <button
                type="submit"
                disabled={guardandoMiPass}
                className="w-full mt-2 py-2 px-4 bg-slate-800 hover:bg-slate-700 text-amber-400 font-semibold rounded-lg text-xs transition-colors flex items-center justify-center gap-2 border border-slate-700"
              >
                {guardandoMiPass ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Lock className="w-4 h-4" />}
                Guardar Mi Contraseña
              </button>
            </form>
          </div>
        </div>

        {/* Tarjeta 2: Listado de Empleados y Cuentas */}
        <div className="lg:col-span-2 bg-slate-900/90 rounded-xl border border-slate-800 p-5 shadow-lg flex flex-col">
          {/* Filtros */}
          <div className="flex flex-col sm:flex-row gap-3 mb-4 justify-between items-start sm:items-center">
            <div className="relative w-full sm:w-64">
              <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Buscar por nombre o usuario..."
                value={filtroTexto}
                onChange={(e) => setFiltroTexto(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-amber-500"
              />
            </div>

            <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0">
              {['TODOS', 'mesero', 'cajero', 'cocina', 'admin'].map((rol) => (
                <button
                  key={rol}
                  onClick={() => setFiltroRol(rol)}
                  className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors capitalize ${
                    filtroRol === rol
                      ? 'bg-amber-500 text-slate-950 font-bold'
                      : 'bg-slate-800 text-slate-400 hover:text-white'
                  }`}
                >
                  {rol === 'TODOS' ? 'Todos' : rol}
                </button>
              ))}
            </div>
          </div>

          {/* Tabla de Usuarios */}
          <div className="overflow-x-auto rounded-lg border border-slate-800 flex-1">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-slate-400 font-semibold border-b border-slate-800 uppercase tracking-wider">
                <tr>
                  <th className="py-2.5 px-3">Empleado</th>
                  <th className="py-2.5 px-3">Rol</th>
                  <th className="py-2.5 px-3 text-center">Estado</th>
                  <th className="py-2.5 px-3 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {loading ? (
                  <tr>
                    <td colSpan={4} className="py-8 text-center text-slate-500">
                      <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-amber-500" />
                      Cargando empleados...
                    </td>
                  </tr>
                ) : usuariosFiltrados.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="py-8 text-center text-slate-500">
                      No se encontraron empleados con ese criterio.
                    </td>
                  </tr>
                ) : (
                  usuariosFiltrados.map((u) => (
                    <tr key={u.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3 px-3">
                        <div className="font-semibold text-white">{u.nombre}</div>
                        <div className="text-[11px] text-slate-400 font-mono">@{u.usuario}</div>
                      </td>
                      <td className="py-3 px-3">{getRolBadge(u.rol)}</td>
                      <td className="py-3 px-3 text-center">
                        {u.activo ? (
                          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-400">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                            Activo
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-rose-400">
                            <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                            Inactivo
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-3 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => {
                              setUsuarioSeleccionado(u)
                              setResetNuevaPass('')
                              setModalResetAbierto(true)
                            }}
                            title="Cambiar contraseña de este empleado"
                            className="p-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-amber-400 transition-colors border border-slate-700/60"
                          >
                            <KeyRound className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => handleToggleEstado(u)}
                            title={u.activo ? 'Desactivar acceso' : 'Activar acceso'}
                            className={`p-1.5 rounded-md border transition-colors ${
                              u.activo
                                ? 'bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 border-rose-800/50'
                                : 'bg-emerald-950/40 hover:bg-emerald-900/60 text-emerald-300 border-emerald-800/50'
                            }`}
                          >
                            {u.activo ? <UserX className="w-3.5 h-3.5" /> : <UserCheck className="w-3.5 h-3.5" />}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Modal: Crear Nuevo Empleado */}
      {modalCrearAbierto && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-4">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <UserPlus className="w-5 h-5 text-amber-500" />
                Registrar Nuevo Empleado
              </h3>
              <button
                onClick={() => setModalCrearAbierto(false)}
                className="text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {errorNuevo && (
              <div className="p-3 mb-4 rounded-lg bg-rose-950/60 border border-rose-800 text-rose-300 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{errorNuevo}</span>
              </div>
            )}

            <form onSubmit={handleCrearUsuario} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Nombre Completo</label>
                <input
                  type="text"
                  required
                  placeholder="Ej: Carlos Gómez"
                  value={nuevoForm.nombre}
                  onChange={(e) => setNuevoForm({ ...nuevoForm, nombre: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Usuario de Login</label>
                <input
                  type="text"
                  required
                  placeholder="Ej: carlos_mesero"
                  value={nuevoForm.usuario}
                  onChange={(e) => setNuevoForm({ ...nuevoForm, usuario: e.target.value.toLowerCase() })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-amber-500 font-mono"
                />
                <p className="text-[11px] text-slate-500 mt-1">Este usuario se usará para iniciar sesión en la app.</p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Rol en el Restaurante</label>
                <select
                  value={nuevoForm.rol}
                  onChange={(e) => setNuevoForm({ ...nuevoForm, rol: e.target.value as any })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500"
                >
                  <option value="mesero">Mesero (Tomar pedidos en mesas)</option>
                  <option value="cajero">Cajero (Cobros, arqueos, vales)</option>
                  <option value="cocina">Cocina / KDS (Comandas de cocina)</option>
                  <option value="admin">Administrador (Control total)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Contraseña Inicial</label>
                <input
                  type="password"
                  required
                  placeholder="Mínimo 4 caracteres"
                  value={nuevoForm.password}
                  onChange={(e) => setNuevoForm({ ...nuevoForm, password: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setModalCrearAbierto(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={guardandoNuevo}
                  className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold rounded-lg transition-colors flex items-center gap-2"
                >
                  {guardandoNuevo && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                  Crear Empleado
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Resetear Contraseña de Empleado */}
      {modalResetAbierto && usuarioSeleccionado && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-sm w-full p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <KeyRound className="w-5 h-5 text-amber-500" />
                Nueva Clave para Empleado
              </h3>
              <button
                onClick={() => setModalResetAbierto(false)}
                className="text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-400 mb-4">
              Asignando nueva contraseña a <strong className="text-white">{usuarioSeleccionado.nombre}</strong> (@
              {usuarioSeleccionado.usuario}):
            </p>

            <form onSubmit={handleResetPassword} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Nueva Contraseña</label>
                <input
                  type="password"
                  required
                  placeholder="Mínimo 4 caracteres"
                  value={resetNuevaPass}
                  onChange={(e) => setResetNuevaPass(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setModalResetAbierto(false)}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={guardandoReset}
                  className="px-3 py-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold rounded-lg transition-colors flex items-center gap-2"
                >
                  {guardandoReset && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                  Guardar Clave
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

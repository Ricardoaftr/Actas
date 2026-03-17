import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, NavLink, Navigate } from 'react-router-dom'
import Actas from './pages/Actas'
import Login from './pages/Login'
import Superadmin from './pages/Superadmin'
import Dashboard from './pages/Dashboard'
import Tareas from './pages/Tareas'

function App() {
  const [usuario, setUsuario] = useState(null)

  useEffect(() => {
    const usrGuardado = localStorage.getItem('usuarioSaaS')
    if (usrGuardado) {
      setUsuario(JSON.parse(usrGuardado))
    }
  }, [])

  const handleLogin = (datosUsuario) => {
    localStorage.setItem('usuarioSaaS', JSON.stringify(datosUsuario))
    setUsuario(datosUsuario)
  }

  const handleLogout = () => {
    localStorage.removeItem('usuarioSaaS')
    setUsuario(null)
  }

  if (!usuario) {
    return <Login onLogin={handleLogin} />
  }

  const rol = usuario.rol ? usuario.rol.toLowerCase() : ''

  // Esta función decide qué clases de Tailwind CSS aplicar dependiendo de si la ruta está activa o no
  const linkClasses = ({ isActive }) =>
    `block p-3 rounded-lg transition font-medium border-l-4 ${
      isActive 
        ? 'bg-gray-800 border-blue-500 text-white' // Activo: Fondo oscuro, borde azul, texto blanco
        : 'border-transparent text-gray-300 hover:bg-gray-800 hover:text-white' // Inactivo: Sin borde, gris claro
    }`

  // Clase especial para el botón del Superadmin (mantiene el tono morado)
  const superadminLinkClasses = ({ isActive }) =>
    `block p-3 rounded-lg transition font-medium border-l-4 ${
      isActive 
        ? 'bg-purple-800 border-purple-400 text-white shadow-inner' 
        : 'bg-purple-900 border-transparent text-gray-200 hover:bg-purple-800 hover:text-white'
    }`

  return (
    <BrowserRouter>
      <div className="flex h-screen bg-gray-50 font-sans">
        
        <aside className="w-64 bg-gray-900 text-white flex flex-col shadow-xl z-10">
          <div className="p-5 text-xl font-bold border-b border-gray-800 tracking-wide">
            Panel Global SaaS
          </div>
          
          <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
            {/* MENÚ EXCLUSIVO SUPERADMIN */}
            {rol === 'superadmin' && (
              <NavLink to="/superadmin" className={superadminLinkClasses}>
                Panel Global (SaaS)
              </NavLink>
            )}

            {/* MENÚ EXCLUSIVO ADMIN */}
            {rol === 'admin' && (
              <>
                <NavLink to="/dashboard" className={linkClasses}>
                  Dashboard
                </NavLink>
                <NavLink to="/tareas" className={linkClasses}>
                  Asignar Tareas
                </NavLink>
              </>
            )}

            {/* MENÚ EXCLUSIVO TÉCNICO */}
            {rol === 'tecnico' && (
              <>
                <NavLink to="/actas" className={linkClasses}>
                  Generar Acta
                </NavLink>
                <NavLink to="/tareas" className={linkClasses}>
                  Mis Tareas
                </NavLink>
                <NavLink to="/asistente" className={linkClasses}>
                  Asistente IA
                </NavLink>
                <NavLink to="/calculadora" className={linkClasses}>
                  Calculadora LED
                </NavLink>
              </>
            )}
          </nav>
          
          <div className="p-5 border-t border-gray-800">
            <div className="text-sm text-gray-400 mb-3">
              Usuario: <span className="text-white font-bold">{usuario.nombre}</span><br/>
              Rol: <span className="text-blue-400 uppercase text-xs">{rol}</span>
            </div>
            <button onClick={handleLogout} className="w-full bg-red-600 hover:bg-red-700 text-white py-2 rounded text-sm font-bold transition shadow-sm">
              Cerrar Sesión
            </button>
          </div>
        </aside>

        <main className="flex-1 p-8 overflow-y-auto">
          <Routes>
            <Route path="/" element={
              rol === 'superadmin' ? <Navigate to="/superadmin" /> :
              rol === 'admin' ? <Navigate to="/dashboard" /> :
              rol === 'tecnico' ? <Navigate to="/actas" /> : // Redirección directa al técnico también
              (
                <div>
                  <h1 className="text-3xl font-bold text-gray-800">Bienvenido, {usuario.nombre}</h1>
                  <p className="mt-2 text-gray-600">Selecciona una herramienta en el panel izquierdo.</p>
                </div>
              )
            } />
            
            {/* RUTAS SUPERADMIN */}
            {rol === 'superadmin' && (
              <Route path="/superadmin" element={<Superadmin />} />
            )}
            
            {/* RUTAS ADMIN */}
            {rol === 'admin' && (
              <>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/tareas" element={<Tareas />} />
              </>
            )}

            {/* RUTAS TÉCNICO */}
            {rol === 'tecnico' && (
              <>
                <Route path="/actas" element={<Actas />} />
                <Route path="/tareas" element={<Tareas />} />
                <Route path="/asistente" element={<h1 className="text-2xl font-bold">Asistente IA (En construcción)</h1>} />
                <Route path="/calculadora" element={<h1 className="text-2xl font-bold">Calculadora LED (En construcción)</h1>} />
              </>
            )}
            
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </main>

      </div>
    </BrowserRouter>
  )
}

export default App
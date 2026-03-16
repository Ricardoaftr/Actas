import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Link, Navigate } from 'react-router-dom'
import Actas from './pages/Actas'
import Login from './pages/Login'
import Superadmin from './pages/Superadmin'

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

  return (
    <BrowserRouter>
      <div className="flex h-screen bg-gray-50 font-sans">
        
        <aside className="w-64 bg-gray-900 text-white flex flex-col shadow-xl z-10">
          <div className="p-5 text-xl font-bold border-b border-gray-800 tracking-wide">
            Panel Global SaaS
          </div>
          
          <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
            {rol === 'superadmin' && (
              <Link to="/superadmin" className="block p-3 rounded-lg bg-purple-900 hover:bg-purple-800 transition font-medium">Panel Global (SaaS)</Link>
            )}

            {rol !== 'superadmin' && (
              <>
                <Link to="/actas" className="block p-3 rounded-lg hover:bg-gray-800 transition font-medium">Generar Acta</Link>
                
                {rol === 'admin' && (
                  <Link to="/dashboard" className="block p-3 rounded-lg hover:bg-gray-800 transition font-medium">Dashboard</Link>
                )}

                <Link to="/tareas" className="block p-3 rounded-lg hover:bg-gray-800 transition font-medium">
                  {rol === 'admin' ? 'Asignar Tareas' : 'Mis Tareas'}
                </Link>

                {rol === 'tecnico' && (
                  <Link to="/asistente" className="block p-3 rounded-lg hover:bg-gray-800 transition font-medium">Asistente IA</Link>
                )}

                <Link to="/calculadora" className="block p-3 rounded-lg hover:bg-gray-800 transition font-medium">Calculadora LED</Link>
              </>
            )}
          </nav>
          
          <div className="p-5 border-t border-gray-800">
            <div className="text-sm text-gray-400 mb-3">
              Usuario: <span className="text-white font-bold">{usuario.nombre}</span><br/>
              Rol: <span className="text-blue-400 uppercase text-xs">{rol}</span>
            </div>
            <button onClick={handleLogout} className="w-full bg-red-600 hover:bg-red-700 text-white py-2 rounded text-sm font-bold transition">
              Cerrar Sesión
            </button>
          </div>
        </aside>

        <main className="flex-1 p-8 overflow-y-auto">
          <Routes>
            <Route path="/" element={
              rol === 'superadmin' ? <Navigate to="/superadmin" /> : (
                <div>
                  <h1 className="text-3xl font-bold text-gray-800">Bienvenido, {usuario.nombre}</h1>
                  <p className="mt-2 text-gray-600">Selecciona una herramienta en el panel izquierdo.</p>
                </div>
              )
            } />
            
            {rol === 'superadmin' && (
              <Route path="/superadmin" element={<Superadmin />} />
            )}
            
            {rol !== 'superadmin' && (
              <>
                <Route path="/actas" element={<Actas />} />
                <Route path="/tareas" element={<h1 className="text-2xl font-bold">Módulo de Tareas (En construcción)</h1>} />
                <Route path="/calculadora" element={<h1 className="text-2xl font-bold">Calculadora LED (En construcción)</h1>} />
                
                {rol === 'admin' && (
                  <Route path="/dashboard" element={<h1 className="text-2xl font-bold">Dashboard Admin (En construcción)</h1>} />
                )}
                
                {rol === 'tecnico' && (
                  <Route path="/asistente" element={<h1 className="text-2xl font-bold">Asistente IA (En construcción)</h1>} />
                )}
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
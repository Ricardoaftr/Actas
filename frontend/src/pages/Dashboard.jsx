import { useState, useEffect } from 'react'

export default function Dashboard() {
  const [vistaActiva, setVistaActiva] = useState('kpi')
  const [empresaId, setEmpresaId] = useState(null)
  
  const [kpi, setKpi] = useState({})
  const [usuarios, setUsuarios] = useState([])
  const [proyectos, setProyectos] = useState([])
  
  const [formUsuario, setFormUsuario] = useState({ username: '', password: '', rol: 'tecnico' })
  const [formProyecto, setFormProyecto] = useState({ nombre: '', notas: '' })

  useEffect(() => {
    const usuario = JSON.parse(localStorage.getItem('usuarioSaaS'))
    if (usuario && usuario.empresaId) {
      setEmpresaId(usuario.empresaId)
      cargarKpi(usuario.empresaId)
    }
  }, [])

  useEffect(() => {
    if (!empresaId) return
    if (vistaActiva === 'kpi') cargarKpi(empresaId)
    if (vistaActiva === 'usuarios') cargarUsuarios(empresaId)
    if (vistaActiva === 'proyectos') cargarProyectos(empresaId)
  }, [vistaActiva, empresaId])

  const cargarKpi = async (id) => {
    const res = await fetch(`http://localhost:8000/api/admin/kpi/${id}`)
    const data = await res.json()
    if (data.success) setKpi(data.metricas)
  }

  const cargarUsuarios = async (id) => {
    const res = await fetch(`http://localhost:8000/api/admin/usuarios/${id}`)
    const data = await res.json()
    if (data.success) setUsuarios(data.usuarios)
  }

  const cargarProyectos = async (id) => {
    const res = await fetch(`http://localhost:8000/api/admin/proyectos/${id}`)
    const data = await res.json()
    if (data.success) setProyectos(data.proyectos)
  }

  const crearUsuario = async (e) => {
    e.preventDefault()
    await fetch('http://localhost:8000/api/admin/usuarios', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...formUsuario, empresa_id: empresaId })
    })
    setFormUsuario({ username: '', password: '', rol: 'tecnico' })
    cargarUsuarios(empresaId)
  }

  const crearProyecto = async (e) => {
    e.preventDefault()
    await fetch('http://localhost:8000/api/admin/proyectos', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...formProyecto, empresa_id: empresaId })
    })
    setFormProyecto({ nombre: '', notas: '' })
    cargarProyectos(empresaId)
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold text-gray-800">Consola de Administración</h1>
      
      <div className="flex border-b overflow-x-auto">
        <button onClick={() => setVistaActiva('kpi')} className={`px-4 py-2 font-bold ${vistaActiva === 'kpi' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}>Métricas KPI</button>
        <button onClick={() => setVistaActiva('proyectos')} className={`px-4 py-2 font-bold ${vistaActiva === 'proyectos' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}>Explorador de Archivos</button>
        <button onClick={() => setVistaActiva('clasificacion')} className={`px-4 py-2 font-bold ${vistaActiva === 'clasificacion' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}>Clasificación y Exportación</button>
        <button onClick={() => setVistaActiva('usuarios')} className={`px-4 py-2 font-bold ${vistaActiva === 'usuarios' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}>Gestión de Usuario</button>
        <button onClick={() => setVistaActiva('drive')} className={`px-4 py-2 font-bold ${vistaActiva === 'drive' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}>Google Drive</button>
        <button onClick={() => setVistaActiva('seguridad')} className={`px-4 py-2 font-bold ${vistaActiva === 'seguridad' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}>Seguridad</button>
      </div>

      {vistaActiva === 'kpi' && (
        <div className="grid grid-cols-4 gap-6 mt-4">
          <div className="bg-white p-6 border rounded shadow-sm">
            <h3 className="text-gray-500 font-bold mb-2">Total Actas</h3>
            <p className="text-3xl font-bold text-blue-600">{kpi.total_actas || 0}</p>
          </div>
          <div className="bg-white p-6 border rounded shadow-sm">
            <h3 className="text-gray-500 font-bold mb-2">Tareas Pendientes</h3>
            <p className="text-3xl font-bold text-orange-500">{kpi.tareas_pendientes || 0}</p>
          </div>
          <div className="bg-white p-6 border rounded shadow-sm">
            <h3 className="text-gray-500 font-bold mb-2">Tareas Completadas</h3>
            <p className="text-3xl font-bold text-green-600">{kpi.tareas_completadas || 0}</p>
          </div>
          <div className="bg-white p-6 border rounded shadow-sm">
            <h3 className="text-gray-500 font-bold mb-2">Uso Almacenamiento</h3>
            <p className="text-3xl font-bold text-purple-600">{kpi.uso_almacenamiento || '0 MB'}</p>
          </div>
        </div>
      )}

      {vistaActiva === 'usuarios' && (
        <div className="grid grid-cols-2 gap-6 mt-4">
          <div className="bg-white p-6 border rounded shadow-sm">
            <h2 className="text-xl font-bold mb-4">Crear Nuevo Usuario</h2>
            <form onSubmit={crearUsuario} className="space-y-4">
              <input type="text" placeholder="Username" required value={formUsuario.username} onChange={e => setFormUsuario({...formUsuario, username: e.target.value})} className="w-full border p-2 rounded" />
              <input type="password" placeholder="Contraseña" required value={formUsuario.password} onChange={e => setFormUsuario({...formUsuario, password: e.target.value})} className="w-full border p-2 rounded" />
              <select value={formUsuario.rol} onChange={e => setFormUsuario({...formUsuario, rol: e.target.value})} className="w-full border p-2 rounded">
                <option value="tecnico">Técnico</option>
                <option value="admin">Administrador</option>
              </select>
              <button type="submit" className="w-full bg-blue-600 text-white font-bold py-2 rounded">Crear Usuario</button>
            </form>
          </div>
          <div className="bg-white p-6 border rounded shadow-sm">
            <h2 className="text-xl font-bold mb-4">Usuarios Activos</h2>
            <ul className="space-y-2">
              {usuarios.map((u, i) => (
                <li key={i} className="p-3 border rounded flex justify-between">
                  <span className="font-bold">{u[0]}</span>
                  <span className="bg-gray-200 px-2 rounded text-sm uppercase">{u[1]}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {vistaActiva === 'proyectos' && (
        <div className="grid grid-cols-2 gap-6 mt-4">
          <div className="bg-white p-6 border rounded shadow-sm">
            <h2 className="text-xl font-bold mb-4">Crear Carpeta de Proyecto</h2>
            <form onSubmit={crearProyecto} className="space-y-4">
              <input type="text" placeholder="Nombre del Proyecto" required value={formProyecto.nombre} onChange={e => setFormProyecto({...formProyecto, nombre: e.target.value})} className="w-full border p-2 rounded" />
              <textarea placeholder="Notas u observaciones" value={formProyecto.notas} onChange={e => setFormProyecto({...formProyecto, notas: e.target.value})} className="w-full border p-2 rounded"></textarea>
              <button type="submit" className="w-full bg-blue-600 text-white font-bold py-2 rounded">Crear Carpeta</button>
            </form>
          </div>
          <div className="bg-white p-6 border rounded shadow-sm">
            <h2 className="text-xl font-bold mb-4">Carpetas Existentes</h2>
            <ul className="space-y-2">
              {proyectos.map((p, i) => (
                <li key={i} className="p-3 border rounded">
                  <p className="font-bold">{p[1]}</p>
                  <p className="text-sm text-gray-500">{p[3]}</p>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {vistaActiva === 'clasificacion' && (
        <div className="bg-white p-6 border rounded shadow-sm mt-4">
          <h2 className="text-xl font-bold mb-4">Clasificación y Exportación Masiva</h2>
          <div className="p-4 bg-gray-50 border rounded text-gray-600">
            Interfaz de selección de actas para clasificación y generación de ZIP. Requiere conexión al módulo PDF y Drive.
          </div>
        </div>
      )}

      {vistaActiva === 'drive' && (
        <div className="bg-white p-6 border rounded shadow-sm mt-4">
          <h2 className="text-xl font-bold mb-4">Configuración de Google Drive</h2>
          <button className="bg-green-600 text-white px-4 py-2 rounded font-bold">Autenticar Drive API</button>
        </div>
      )}

      {vistaActiva === 'seguridad' && (
        <div className="bg-white p-6 border rounded shadow-sm mt-4">
          <h2 className="text-xl font-bold mb-4">Auditoría y Seguridad</h2>
          <button className="bg-red-600 text-white px-4 py-2 rounded font-bold">Restablecer 2FA Global</button>
        </div>
      )}
    </div>
  )
}
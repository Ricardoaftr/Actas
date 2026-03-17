import { useState, useEffect } from 'react'

export default function Tareas() {
  const [tareas, setTareas] = useState([])
  const [tecnicos, setTecnicos] = useState([])
  const [cargando, setCargando] = useState(true)
  
  const [usuario, setUsuario] = useState(null)
  const [formTarea, setFormTarea] = useState({ titulo: '', descripcion: '', asignado_a: '' })
  
  // Para la reasignación rápida en la tabla
  const [tecnicoReasignar, setTecnicoReasignar] = useState({})

  useEffect(() => {
    const usr = JSON.parse(localStorage.getItem('usuarioSaaS'))
    if (usr) {
      setUsuario(usr)
      cargarDatos(usr.empresaId)
    }
  }, [])

  const cargarDatos = async (empresaId) => {
    try {
      const [resTareas, resTecnicos] = await Promise.all([
        fetch(`http://localhost:8000/api/admin/tareas/${empresaId}`),
        fetch(`http://localhost:8000/api/admin/tecnicos/${empresaId}`)
      ])
      const dataTareas = await resTareas.json()
      const dataTecnicos = await resTecnicos.json()

      if (dataTareas.success) setTareas(dataTareas.tareas || [])
      if (dataTecnicos.success) {
        setTecnicos(dataTecnicos.tecnicos || [])
        if (dataTecnicos.tecnicos.length > 0) {
          setFormTarea(prev => ({ ...prev, asignado_a: dataTecnicos.tecnicos[0] }))
        }
      }
    } catch (error) {
      console.error("Error cargando tareas:", error)
    } finally {
      setCargando(false)
    }
  }

  const handleCrearTarea = async (e) => {
    e.preventDefault()
    if (!formTarea.titulo || !formTarea.asignado_a) return alert("Faltan datos")

    const req = await fetch('http://localhost:8000/api/admin/tareas', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        titulo: formTarea.titulo,
        descripcion: formTarea.descripcion,
        asignado_a: formTarea.asignado_a,
        empresa_id: usuario.empresaId,
        creado_por: usuario.nombre
      })
    })

    if (req.ok) {
      setFormTarea({ ...formTarea, titulo: '', descripcion: '' })
      cargarDatos(usuario.empresaId)
      alert("¡Tarea asignada con éxito!")
    }
  }

  const actualizarEstado = async (id, nuevoEstado) => {
    await fetch(`http://localhost:8000/api/admin/tareas/${id}/estado`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ estado: nuevoEstado })
    })
    cargarDatos(usuario.empresaId)
  }

  const reasignarTarea = async (id) => {
    const nuevoTecnico = tecnicoReasignar[id]
    if (!nuevoTecnico) return alert("Selecciona un técnico primero")

    await fetch(`http://localhost:8000/api/admin/tareas/${id}/reasignar`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nuevo_tecnico: nuevoTecnico })
    })
    alert("Tarea reasignada")
    cargarDatos(usuario.empresaId)
  }

  const eliminarTarea = async (id) => {
    if (!window.confirm("¿Seguro que deseas eliminar esta tarea?")) return
    await fetch(`http://localhost:8000/api/admin/tareas/${id}`, { method: 'DELETE' })
    cargarDatos(usuario.empresaId)
  }

  if (cargando) return <div className="p-8 font-bold text-gray-600">Cargando Panel de Tareas...</div>

  // Vista exclusiva del Técnico la haremos luego, por ahora bloqueamos
  if (usuario?.rol === 'tecnico') return <h1 className="text-2xl p-8">Panel de técnico en construcción...</h1>

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      <h1 className="text-3xl font-bold text-gray-800 border-b pb-4">Gestión y Asignación de Tareas</h1>

      {/* FORMULARIO CREAR TAREA */}
      <section className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
        <h2 className="text-xl font-bold text-gray-700 mb-4">Asignar Nueva Tarea</h2>
        <form onSubmit={handleCrearTarea} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-bold text-gray-600 mb-1">Título de la Tarea</label>
              <input type="text" required value={formTarea.titulo} onChange={e => setFormTarea({...formTarea, titulo: e.target.value})} className="w-full border p-2 rounded outline-none focus:ring-2 focus:ring-blue-500" placeholder="Ej: Mantenimiento Pantalla Sede Norte" />
            </div>
            <div>
              <label className="block text-sm font-bold text-gray-600 mb-1">Asignar a Técnico</label>
              <select value={formTarea.asignado_a} onChange={e => setFormTarea({...formTarea, asignado_a: e.target.value})} className="w-full border p-2 rounded outline-none focus:ring-2 focus:ring-blue-500">
                {tecnicos.length === 0 && <option value="">No hay técnicos en la empresa</option>}
                {tecnicos.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="block text-sm font-bold text-gray-600 mb-1">Descripción / Instrucciones</label>
            <textarea rows="3" value={formTarea.descripcion} onChange={e => setFormTarea({...formTarea, descripcion: e.target.value})} className="w-full border p-2 rounded outline-none focus:ring-2 focus:ring-blue-500" placeholder="Detalles de lo que el técnico debe realizar..."></textarea>
          </div>
          <button type="submit" disabled={tecnicos.length === 0} className="bg-blue-900 text-white font-bold py-2 px-6 rounded hover:bg-blue-800 transition disabled:bg-gray-400">
            Crear y Asignar Tarea
          </button>
        </form>
      </section>

      {/* TABLA DE TAREAS ACTIVAS */}
      <section className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
        <h2 className="text-xl font-bold text-gray-700 mb-4">Tareas de la Empresa</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="bg-gray-100 text-gray-700">
                <th className="p-3 font-bold border-b">ID</th>
                <th className="p-3 font-bold border-b">Título</th>
                <th className="p-3 font-bold border-b">Técnico Actual</th>
                <th className="p-3 font-bold border-b text-center">Estado</th>
                <th className="p-3 font-bold border-b">Acciones Administrativas</th>
              </tr>
            </thead>
            <tbody>
              {tareas.length === 0 ? (
                <tr><td colSpan="5" className="p-6 text-center text-gray-500">No hay tareas registradas.</td></tr>
              ) : (
                tareas.map((t, idx) => (
                  <tr key={idx} className="border-b hover:bg-gray-50">
                    <td className="p-3 font-mono text-gray-500">{t[0]}</td>
                    <td className="p-3 font-bold text-gray-800">{t[1]}<br/><span className="text-xs font-normal text-gray-500">{t[2]}</span></td>
                    <td className="p-3 text-blue-700 font-semibold uppercase">{t[3]}</td>
                    <td className="p-3 text-center">
                      <select value={t[4]} onChange={e => actualizarEstado(t[0], e.target.value)} className={`font-bold p-1 rounded ${t[4] === 'Pendiente' ? 'bg-orange-100 text-orange-700' : t[4] === 'Completado' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'}`}>
                        <option value="Pendiente">Pendiente</option>
                        <option value="En Proceso">En Proceso</option>
                        <option value="Completado">Completado</option>
                      </select>
                    </td>
                    <td className="p-3">
                      <div className="flex items-center space-x-2">
                        <select onChange={e => setTecnicoReasignar({...tecnicoReasignar, [t[0]]: e.target.value})} className="border p-1 text-xs rounded">
                          <option value="">Reasignar a...</option>
                          {tecnicos.filter(tec => tec !== t[3]).map(tec => <option key={tec} value={tec}>{tec}</option>)}
                        </select>
                        <button onClick={() => reasignarTarea(t[0])} className="text-blue-600 font-bold hover:underline text-xs">Aplicar</button>
                        <span className="text-gray-300">|</span>
                        <button onClick={() => eliminarTarea(t[0])} className="text-red-600 font-bold hover:underline text-xs">Eliminar</button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
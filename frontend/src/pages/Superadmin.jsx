import { useState, useEffect } from 'react'

export default function Superadmin() {
  const [empresas, setEmpresas] = useState([])
  const [metricas, setMetricas] = useState(null)
  const [auditoria, setAuditoria] = useState([])
  const [cargando, setCargando] = useState(true)
  const [vistaActiva, setVistaActiva] = useState('empresas')

  const [formEmpresa, setFormEmpresa] = useState({ nombre: '', plan: 'Basico', carpeta: '', admin_user: '', admin_pass: '', admin_pass_confirm: '' })
  const [formPeligro, setFormPeligro] = useState({ empresaBorrar: '', userBorrar: '', userReset: '', nuevaPass: '' })

  useEffect(() => {
    cargarDatos()
  }, [])

  const cargarDatos = async () => {
    try {
      const [resEmpresas, resMetricas, resAuditoria] = await Promise.all([
        fetch('http://localhost:8000/api/superadmin/empresas'),
        fetch('http://localhost:8000/api/superadmin/metricas'),
        fetch('http://localhost:8000/api/superadmin/auditoria')
      ])
      
      const dataEmpresas = await resEmpresas.json()
      const dataMetricas = await resMetricas.json()
      const dataAuditoria = await resAuditoria.json()

      if (dataEmpresas.success) setEmpresas(Array.isArray(dataEmpresas.empresas) ? dataEmpresas.empresas : [])
      if (dataMetricas.success) setMetricas(dataMetricas.metricas)
      if (dataAuditoria.success) setAuditoria(Array.isArray(dataAuditoria.logs) ? dataAuditoria.logs : [])
      
    } catch (error) {
      console.error("Error cargando panel", error)
    } finally {
      setCargando(false)
    }
  }

  const crearEmpresa = async (e) => {
    e.preventDefault()
    if (formEmpresa.admin_pass !== formEmpresa.admin_pass_confirm) return alert("Contraseñas no coinciden")
    
    const req = await fetch('http://localhost:8000/api/superadmin/empresas', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        nombre: formEmpresa.nombre,
        plan: formEmpresa.plan,
        carpeta: formEmpresa.carpeta,
        admin_user: formEmpresa.admin_user.trim().toLowerCase().replace(/ /g, "_"),
        admin_pass: formEmpresa.admin_pass
      })
    })
    if (req.ok) {
      alert("Empresa creada exitosamente")
      setFormEmpresa({ nombre: '', plan: 'Basico', carpeta: '', admin_user: '', admin_pass: '', admin_pass_confirm: '' })
      cargarDatos()
    } else {
      const error = await req.json()
      alert(error.detail || "Error al crear")
    }
  }

  const actualizarPlan = async (id, nuevoPlan) => {
    await fetch(`http://localhost:8000/api/superadmin/empresas/${id}/plan`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ plan: nuevoPlan })
    })
    cargarDatos()
  }

  const eliminarEmpresa = async () => {
    if (!formPeligro.empresaBorrar) return
    const confirmacion = window.confirm(`¿Seguro de destruir la empresa ID: ${formPeligro.empresaBorrar}?`)
    if (!confirmacion) return

    await fetch(`http://localhost:8000/api/superadmin/empresas/${formPeligro.empresaBorrar}`, { method: 'DELETE' })
    alert("Empresa eliminada")
    cargarDatos()
  }

  const eliminarUsuario = async () => {
    if (!formPeligro.userBorrar) return
    await fetch(`http://localhost:8000/api/superadmin/usuarios/${formPeligro.userBorrar}`, { method: 'DELETE' })
    alert("Usuario eliminado")
    cargarDatos()
  }

  const resetearPass = async () => {
    if (!formPeligro.userReset || !formPeligro.nuevaPass) return
    await fetch('http://localhost:8000/api/superadmin/usuarios/reset', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: formPeligro.userReset, nueva_pass: formPeligro.nuevaPass })
    })
    alert("Contraseña actualizada")
  }

  if (cargando) return <div className="p-8 font-bold text-gray-600">Cargando Panel...</div>

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold text-gray-800">Panel de Control Global - SaaS</h1>
      
      <div className="flex space-x-4 border-b pb-2">
        <button onClick={() => setVistaActiva('empresas')} className={`font-bold pb-2 ${vistaActiva === 'empresas' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}>Gestión de Empresas</button>
        <button onClick={() => setVistaActiva('metricas')} className={`font-bold pb-2 ${vistaActiva === 'metricas' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}>Métricas del Servidor</button>
        <button onClick={() => setVistaActiva('peligro')} className={`font-bold pb-2 ${vistaActiva === 'peligro' ? 'text-red-600 border-b-2 border-red-600' : 'text-gray-500'}`}>Super Admin</button>
      </div>

      {vistaActiva === 'empresas' && (
        <div className="space-y-8">
          <section className="bg-white p-6 rounded-xl border border-gray-200">
            <h2 className="text-xl font-bold mb-4">Registrar Nueva Empresa</h2>
            <form onSubmit={crearEmpresa} className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <input type="text" placeholder="Nombre Empresa" required value={formEmpresa.nombre} onChange={e => setFormEmpresa({...formEmpresa, nombre: e.target.value})} className="border p-2 rounded" />
                <select value={formEmpresa.plan} onChange={e => setFormEmpresa({...formEmpresa, plan: e.target.value})} className="border p-2 rounded">
                  <option>Basico</option><option>Plus</option><option>Enterprise</option>
                </select>
                <input type="text" placeholder="ID Carpeta Drive Raíz" required value={formEmpresa.carpeta} onChange={e => setFormEmpresa({...formEmpresa, carpeta: e.target.value})} className="border p-2 rounded" />
              </div>
              <h3 className="font-bold pt-4 border-t">Usuario Administrador Principal</h3>
              <div className="grid grid-cols-3 gap-4">
                <input type="text" placeholder="Usuario Admin" required value={formEmpresa.admin_user} onChange={e => setFormEmpresa({...formEmpresa, admin_user: e.target.value})} className="border p-2 rounded" />
                <input type="password" placeholder="Contraseña" required value={formEmpresa.admin_pass} onChange={e => setFormEmpresa({...formEmpresa, admin_pass: e.target.value})} className="border p-2 rounded" />
                <input type="password" placeholder="Confirmar" required value={formEmpresa.admin_pass_confirm} onChange={e => setFormEmpresa({...formEmpresa, admin_pass_confirm: e.target.value})} className="border p-2 rounded" />
              </div>
              <button type="submit" className="bg-blue-600 text-white font-bold py-2 px-4 rounded hover:bg-blue-700">Crear Empresa y Admin</button>
            </form>
          </section>

          <section>
            <h2 className="text-xl font-bold mb-4">Empresas Activas</h2>
            <div className="grid gap-4">
              {empresas.map((emp, idx) => (
                <div key={idx} className="bg-white p-4 border rounded-lg flex justify-between items-center">
                  <div>
                    <p className="font-bold">{emp[1]} <span className="text-gray-400 text-sm">(ID: {emp[0]})</span></p>
                    <p className="text-sm text-gray-500">Carpeta Drive: {emp[3]}</p>
                  </div>
                  <div className="flex space-x-2">
                    <select value={emp[2]} onChange={(e) => actualizarPlan(emp[0], e.target.value)} className="border p-2 rounded text-sm">
                      <option>Basico</option><option>Plus</option><option>Enterprise</option>
                    </select>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      )}

      {vistaActiva === 'metricas' && (
        <div className="grid grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-xl border flex flex-col items-center">
            <span className="text-gray-500 font-semibold">Uso CPU</span>
            <span className="text-3xl font-bold text-blue-600">{metricas?.cpu || '0%'}</span>
          </div>
          <div className="bg-white p-6 rounded-xl border flex flex-col items-center">
            <span className="text-gray-500 font-semibold">Memoria RAM</span>
            <span className="text-3xl font-bold text-purple-600">{metricas?.ram_usada || '0%'}</span>
            <span className="text-xs text-gray-400 mt-1">Total: {metricas?.ram_total}</span>
          </div>
          <div className="bg-white p-6 rounded-xl border flex flex-col items-center">
            <span className="text-gray-500 font-semibold">Disco Duro</span>
            <span className="text-3xl font-bold text-green-600">{metricas?.disco_usado || '0%'}</span>
            <span className="text-xs text-gray-400 mt-1">Total: {metricas?.disco_total}</span>
          </div>
        </div>
      )}

      {vistaActiva === 'peligro' && (
        <div className="space-y-8">
          <div className="grid grid-cols-3 gap-6">
            <div className="bg-red-50 p-6 rounded-xl border border-red-200">
              <h3 className="font-bold text-red-800 mb-2">Eliminar Empresa Completa</h3>
              <select value={formPeligro.empresaBorrar} onChange={e => setFormPeligro({...formPeligro, empresaBorrar: e.target.value})} className="w-full border p-2 rounded mb-4">
                <option value="">Seleccionar Empresa...</option>
                {empresas.map(e => <option key={e[0]} value={e[0]}>{e[1]}</option>)}
              </select>
              <button onClick={eliminarEmpresa} className="w-full bg-red-600 text-white font-bold py-2 rounded">Aniquilar Empresa</button>
            </div>

            <div className="bg-orange-50 p-6 rounded-xl border border-orange-200">
              <h3 className="font-bold text-orange-800 mb-2">Eliminar Admins/Usuarios</h3>
              <input type="text" placeholder="Username exacto" value={formPeligro.userBorrar} onChange={e => setFormPeligro({...formPeligro, userBorrar: e.target.value})} className="w-full border p-2 rounded mb-4" />
              <button onClick={eliminarUsuario} className="w-full bg-orange-600 text-white font-bold py-2 rounded">Eliminar Usuario</button>
            </div>

            <div className="bg-yellow-50 p-6 rounded-xl border border-yellow-200">
              <h3 className="font-bold text-yellow-800 mb-2">Resetear Contraseña</h3>
              <input type="text" placeholder="Username" value={formPeligro.userReset} onChange={e => setFormPeligro({...formPeligro, userReset: e.target.value})} className="w-full border p-2 rounded mb-2" />
              <input type="password" placeholder="Nueva Contraseña" value={formPeligro.nuevaPass} onChange={e => setFormPeligro({...formPeligro, nuevaPass: e.target.value})} className="w-full border p-2 rounded mb-4" />
              <button onClick={resetearPass} className="w-full bg-yellow-600 text-white font-bold py-2 rounded">Forzar Cambio</button>
            </div>
          </div>

          <section className="bg-white p-6 rounded-xl border">
            <h2 className="text-xl font-bold mb-4">Auditoría Global</h2>
            <div className="overflow-auto max-h-96">
              <table className="w-full text-sm text-left">
                <thead className="bg-gray-100 font-bold text-gray-700">
                  <tr><th className="p-2">Empresa</th><th className="p-2">Usuario</th><th className="p-2">Acción</th><th className="p-2">Detalle</th></tr>
                </thead>
                <tbody>
                  {auditoria.map((log, i) => (
                    <tr key={i} className="border-b"><td className="p-2">{log[1]}</td><td className="p-2">{log[2]}</td><td className="p-2">{log[3]}</td><td className="p-2">{log[4]}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      )}
    </div>
  )
}
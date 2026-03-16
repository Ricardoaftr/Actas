import { useState } from 'react'

export default function Actas() {
  const [formulario, setFormulario] = useState({
    ciudad: 'Cali',
    proyecto: '',
    direccion: '',
    empresaContratante: '',
    personaRecibe: ''
  })

  const handleChange = (e) => {
    setFormulario({
      ...formulario,
      [e.target.name]: e.target.value
    })
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    console.log("Datos capturados listos para enviar a FastAPI:", formulario)
    alert("Formulario procesado instantáneamente. Revisa la consola (F12).")
  }

  return (
    <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-200 max-w-4xl">
      <h2 className="text-2xl font-bold mb-6 text-gray-800">1. Datos Generales</h2>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        
        <div className="grid grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Ciudad</label>
            <input 
              type="text" 
              name="ciudad" 
              value={formulario.ciudad} 
              onChange={handleChange} 
              className="w-full rounded-md border border-gray-300 p-2.5 focus:ring-2 focus:ring-blue-500 outline-none" 
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Nombre del Proyecto</label>
            <input 
              type="text" 
              name="proyecto" 
              value={formulario.proyecto} 
              onChange={handleChange} 
              required
              className="w-full rounded-md border border-gray-300 p-2.5 focus:ring-2 focus:ring-blue-500 outline-none" 
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">Dirección de Entrega</label>
          <input 
            type="text" 
            name="direccion" 
            value={formulario.direccion} 
            onChange={handleChange} 
            required
            className="w-full rounded-md border border-gray-300 p-2.5 focus:ring-2 focus:ring-blue-500 outline-none" 
          />
        </div>

        <h2 className="text-2xl font-bold mt-8 mb-6 text-gray-800 border-t pt-6">Datos del Contratante</h2>

        <div className="grid grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Empresa quien recibe</label>
            <input 
              type="text" 
              name="empresaContratante" 
              value={formulario.empresaContratante} 
              onChange={handleChange} 
              required
              className="w-full rounded-md border border-gray-300 p-2.5 focus:ring-2 focus:ring-blue-500 outline-none" 
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Persona encargada</label>
            <input 
              type="text" 
              name="personaRecibe" 
              value={formulario.personaRecibe} 
              onChange={handleChange} 
              required
              className="w-full rounded-md border border-gray-300 p-2.5 focus:ring-2 focus:ring-blue-500 outline-none" 
            />
          </div>
        </div>

        <div className="pt-6">
          <button 
            type="submit" 
            className="w-full bg-blue-600 text-white font-bold py-3 px-4 rounded-md hover:bg-blue-700 transition"
          >
            ENVIAR ACTA
          </button>
        </div>

      </form>
    </div>
  )
}
import { useState, useRef } from 'react'
import SignatureCanvas from 'react-signature-canvas'

export default function Actas() {
  const sigCanvas = useRef({})
  
  const [formData, setFormData] = useState({
    idActa: 'ACT-001', 
    fecha: new Date().toISOString().split('T')[0],
    ciudad: 'Cali',
    proyecto: '',
    direccion: '',
    cant1: 1,
    desc1: '',
    cant2: 0,
    desc2: '',
    observaciones: '',
    empresa: '',
    persona: '',
    tipoDoc: 'CC',
    numDoc: '',
    colaborador: 'Técnico Actual'
  })

  const [archivos, setArchivos] = useState({
    sello: null,
    evidencias: []
  })

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  const handleFileChange = (e) => {
    if (e.target.name === 'evidencias') {
      setArchivos({ ...archivos, evidencias: Array.from(e.target.files) })
    } else {
      setArchivos({ ...archivos, sello: e.target.files[0] })
    }
  }

  const limpiarFirma = (e) => {
    e.preventDefault()
    sigCanvas.current.clear()
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    
    if (sigCanvas.current.isEmpty()) {
      alert("La firma es obligatoria.")
      return
    }

    const firmaBase64 = sigCanvas.current.getTrimmedCanvas().toDataURL('image/jpeg')
    
    const payloadCompleto = {
      ...formData,
      sello: archivos.sello ? archivos.sello.name : 'No adjunto',
      cantidadEvidencias: archivos.evidencias.length,
      firma: firmaBase64
    }

    console.log("Datos listos para FastAPI:", payloadCompleto)
    alert("Formulario validado. Revisa la consola F12.")
  }

  return (
    <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-200 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-8 text-gray-800 border-b pb-4">Generar Acta con Firma</h1>
      
      <form onSubmit={handleSubmit} className="space-y-8">
        
        <section>
          <h2 className="text-xl font-bold mb-4 text-gray-800">1. Datos Generales</h2>
          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">ID Acta</label>
              <input type="text" name="idActa" value={formData.idActa} disabled className="w-full rounded-md border border-gray-300 p-2.5 bg-gray-100 cursor-not-allowed" />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Fecha</label>
              <input type="date" name="fecha" value={formData.fecha} onChange={handleChange} className="w-full rounded-md border border-gray-300 p-2.5 outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Ciudad</label>
              <input type="text" name="ciudad" value={formData.ciudad} onChange={handleChange} className="w-full rounded-md border border-gray-300 p-2.5 outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Nombre del Proyecto</label>
              <input type="text" name="proyecto" value={formData.proyecto} onChange={handleChange} required className="w-full rounded-md border border-gray-300 p-2.5 outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
        </section>

        <section>
          <h2 className="text-xl font-bold mb-4 text-gray-800">2. Detalles de lo Entregado</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Dirección de Entrega</label>
              <input type="text" name="direccion" value={formData.direccion} onChange={handleChange} required className="w-full rounded-md border border-gray-300 p-2.5 outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div className="grid grid-cols-4 gap-4">
              <div className="col-span-1">
                <label className="block text-sm font-semibold text-gray-700 mb-1">Cant.</label>
                <input type="number" min="1" name="cant1" value={formData.cant1} onChange={handleChange} className="w-full rounded-md border border-gray-300 p-2.5 outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div className="col-span-3">
                <label className="block text-sm font-semibold text-gray-700 mb-1">Descripción Item 1</label>
                <input type="text" name="desc1" value={formData.desc1} onChange={handleChange} required className="w-full rounded-md border border-gray-300 p-2.5 outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
            </div>
            <div className="grid grid-cols-4 gap-4">
              <div className="col-span-1">
                <label className="block text-sm font-semibold text-gray-700 mb-1">Cant.</label>
                <input type="number" min="0" name="cant2" value={formData.cant2} onChange={handleChange} className="w-full rounded-md border border-gray-300 p-2.5 outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div className="col-span-3">
                <label className="block text-sm font-semibold text-gray-700 mb-1">Descripción Item 2 (Opcional)</label>
                <input type="text" name="desc2" value={formData.desc2} onChange={handleChange} className="w-full rounded-md border border-gray-300 p-2.5 outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Observaciones Adicionales</label>
              <textarea name="observaciones" value={formData.observaciones} onChange={handleChange} rows="3" className="w-full rounded-md border border-gray-300 p-2.5 outline-none focus:ring-2 focus:ring-blue-500"></textarea>
            </div>
          </div>
        </section>

        <section>
          <h2 className="text-xl font-bold mb-4 text-gray-800 border-t pt-6">3. Datos de Participantes</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Empresa quien recibe</label>
              <input type="text" name="empresa" value={formData.empresa} onChange={handleChange} required className="w-full rounded-md border border-gray-300 p-2.5 outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div className="grid grid-cols-4 gap-4">
              <div className="col-span-2">
                <label className="block text-sm font-semibold text-gray-700 mb-1">Persona encargada</label>
                <input type="text" name="persona" value={formData.persona} onChange={handleChange} required className="w-full rounded-md border border-gray-300 p-2.5 outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div className="col-span-1">
                <label className="block text-sm font-semibold text-gray-700 mb-1">Tipo</label>
                <select name="tipoDoc" value={formData.tipoDoc} onChange={handleChange} className="w-full rounded-md border border-gray-300 p-2.5 outline-none focus:ring-2 focus:ring-blue-500">
                  <option value="CC">CC</option>
                  <option value="NIT">NIT</option>
                </select>
              </div>
              <div className="col-span-1">
                <label className="block text-sm font-semibold text-gray-700 mb-1">Número</label>
                <input type="text" name="numDoc" value={formData.numDoc} onChange={handleChange} required className="w-full rounded-md border border-gray-300 p-2.5 outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Nombre del Colaborador</label>
              <input type="text" name="colaborador" value={formData.colaborador} disabled className="w-full rounded-md border border-gray-300 p-2.5 bg-gray-100 cursor-not-allowed" />
            </div>
          </div>
        </section>

        <section>
          <h2 className="text-xl font-bold mb-4 text-gray-800 border-t pt-6">4. Firma de Recibido</h2>
          <p className="text-sm text-gray-500 mb-2">Firma en el recuadro blanco usando tu dedo o el mouse:</p>
          <div className="border-2 border-dashed border-gray-300 rounded-lg bg-gray-50 overflow-hidden mb-2">
            <SignatureCanvas 
              ref={sigCanvas}
              penColor='black'
              canvasProps={{
                width: 700, 
                height: 150, 
                className: 'sigCanvas',
                style: { cursor: 'crosshair', width: '100%' }
              }} 
            />
          </div>
          <button onClick={limpiarFirma} className="text-sm bg-red-100 text-red-600 px-4 py-2 rounded font-semibold hover:bg-red-200 transition">
            Borrar Firma
          </button>
        </section>

        <section>
          <h2 className="text-xl font-bold mb-4 text-gray-800 border-t pt-6">5. Archivos Adjuntos</h2>
          <div className="space-y-4">
            <div className="p-4 border border-blue-100 bg-blue-50 rounded-lg">
              <label className="block text-sm font-semibold text-blue-900 mb-1">Sello Físico</label>
              <input type="file" name="sello" accept="image/png, image/jpeg, image/jpg" onChange={handleFileChange} required className="text-sm w-full" />
            </div>
            <div className="p-4 border border-blue-100 bg-blue-50 rounded-lg">
              <label className="block text-sm font-semibold text-blue-900 mb-1">Evidencias Fotográficas</label>
              <input type="file" name="evidencias" accept="image/png, image/jpeg, image/jpg" multiple onChange={handleFileChange} required className="text-sm w-full" />
            </div>
          </div>
        </section>

        <div className="pt-8">
          <button type="submit" className="w-full bg-blue-600 text-white font-bold py-4 px-4 rounded-lg hover:bg-blue-700 transition shadow-lg text-lg">
            ENVIAR ACTA
          </button>
        </div>

      </form>
    </div>
  )
}
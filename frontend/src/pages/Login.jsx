import { useState } from 'react'

export default function Login({ onLogin }) {
  const [credenciales, setCredenciales] = useState({ usuario: '', password: '' })
  const [codigo2FA, setCodigo2FA] = useState('')
  const [fase, setFase] = useState('login') // 'login' o '2fa'
  const [usuarioTemp, setUsuarioTemp] = useState(null)
  
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(false)

  const handleChange = (e) => setCredenciales({ ...credenciales, [e.target.name]: e.target.value })

  const handleLoginSubmit = async (e) => {
    e.preventDefault()
    setError(''); setCargando(true)

    try {
      const respuesta = await fetch('http://localhost:8000/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credenciales)
      })
      const data = await respuesta.json()

      if (respuesta.ok && data.success) {
        if (data.requiere_2fa) {
          setUsuarioTemp(data.usuario_temp)
          setFase('2fa') // Pasamos a la pantalla de 6 dígitos
        } else {
          onLogin(data.usuario_temp) // Si no tiene 2FA, entra directo
        }
      } else {
        setError(data.detail || 'Error al iniciar sesión.')
      }
    } catch (err) {
      setError('Error conectando con el servidor backend.')
    } finally {
      setCargando(false)
    }
  }

  const handle2FASubmit = async (e) => {
    e.preventDefault()
    setError(''); setCargando(true)

    try {
      const respuesta = await fetch('http://localhost:8000/api/verify-2fa', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ usuario: usuarioTemp.nombre, codigo_2fa: codigo2FA })
      })
      const data = await respuesta.json()

      if (respuesta.ok && data.success) {
        onLogin(usuarioTemp) // ¡Código correcto, le damos acceso total!
      } else {
        setError(data.detail || 'Código incorrecto.')
      }
    } catch (err) {
      setError('Error conectando con el servidor.')
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="max-w-md w-full bg-white p-8 border border-gray-200 rounded-xl shadow-lg">
        
        {fase === 'login' ? (
          <>
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-gray-900">Panel Global SaaS</h2>
              <p className="text-gray-500 mt-2">Inicia sesión con tu cuenta real</p>
            </div>
            {error && <div className="bg-red-50 text-red-600 p-3 rounded-md mb-4 text-sm font-medium">{error}</div>}
            <form onSubmit={handleLoginSubmit} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Usuario</label>
                <input type="text" name="usuario" value={credenciales.usuario} onChange={handleChange} className="w-full p-3 border border-gray-300 rounded-md outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Contraseña</label>
                <input type="password" name="password" value={credenciales.password} onChange={handleChange} className="w-full p-3 border border-gray-300 rounded-md outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <button type="submit" disabled={cargando} className="w-full text-white font-bold py-3 rounded-md bg-blue-900 hover:bg-blue-800 transition">
                {cargando ? 'Verificando...' : 'INGRESAR'}
              </button>
            </form>
          </>
        ) : (
          <>
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-900">Autenticación en Dos Pasos</h2>
              <p className="text-gray-500 mt-2">Abre tu Google Authenticator</p>
            </div>
            {error && <div className="bg-red-50 text-red-600 p-3 rounded-md mb-4 text-sm font-medium">{error}</div>}
            <form onSubmit={handle2FASubmit} className="space-y-6">
              <div>
                <input type="text" maxLength="6" placeholder="000000" value={codigo2FA} onChange={(e) => setCodigo2FA(e.target.value)} className="w-full text-center text-3xl tracking-widest p-4 border border-gray-300 rounded-md outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <button type="submit" disabled={cargando} className="w-full text-white font-bold py-3 rounded-md bg-green-600 hover:bg-green-700 transition">
                {cargando ? 'Validando...' : 'VERIFICAR CÓDIGO'}
              </button>
              <button type="button" onClick={() => setFase('login')} className="w-full text-gray-500 text-sm font-medium hover:text-gray-800">
                Volver atrás
              </button>
            </form>
          </>
        )}

      </div>
    </div>
  )
}
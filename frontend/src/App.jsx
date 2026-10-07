import { useState, useEffect } from 'react'
import './App.css'
import ProcessingDemo from './components/ProcessingDemo'

const App = () => {
  const [status, setStatus] = useState('disconnected')

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const response = await fetch('http://localhost:8000/health')
        const data = await response.json()
        setStatus(data.status)
      } catch (error) {
        setStatus('error')
        console.error('Backend connection failed:', error)
      }
    }
    checkBackend()
    const interval = setInterval(checkBackend, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="app-container">
      {status === 'error' && (
        <div style={{
          backgroundColor: '#ef4444',
          color: 'white',
          padding: '8px 16px',
          textAlign: 'center',
          fontSize: '13px',
          fontWeight: '500'
        }}>
          ⚠️ Backend connection failed. Ensure the server is running on port 8000.
        </div>
      )}
      <ProcessingDemo backendStatus={status} />
    </div>
  )
}

export default App

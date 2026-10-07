import { useState } from 'react'
import './App.css'
import ProcessingDemo from './components/ProcessingDemo'

const App = () => {
  const [status, setStatus] = useState('disconnected')

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

  return (
    <div className="app">
      <header className="app-header">
        <h1>Flagship 107</h1>
        <p>Video Intelligence & Behavioral Anomaly Detection</p>
        <div style={{ marginTop: '10px' }}>
          <span>Backend: </span>
          <span className={`status-${status}`} style={{ 
            padding: '2px 8px', 
            borderRadius: '4px',
            backgroundColor: status === 'healthy' ? '#c8e6c9' : '#ffcdd2'
          }}>
            {status}
          </span>
          <button onClick={checkBackend} style={{ marginLeft: '10px' }}>Check Connection</button>
        </div>
      </header>
      
      <main className="app-main">
        <ProcessingDemo />
      </main>
      
      <footer className="app-footer">
        <p>HackNEX 2026 - Problem Statement HNX26PSI07</p>
      </footer>
    </div>
  )
}

export default App

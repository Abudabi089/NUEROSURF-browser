import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import ErrorBoundary from './components/ErrorBoundary'
import './index.css'

console.log('🚀 RENDERER STARTING...');
console.log('Platform:', window.electronAPI?.getPlatform ? 'API Exists' : 'API Missing');
console.log('Versions:', window.versions ? JSON.stringify(window.versions) : 'Versions Missing');

ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <ErrorBoundary>
            <App />
        </ErrorBoundary>
    </React.StrictMode>
)

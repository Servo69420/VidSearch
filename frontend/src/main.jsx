import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.jsx'
import { ThemeProvider } from './contexts/ThemeContext'
import { HistoryProvider } from './contexts/HistoryContext'
import { UserVideosProvider } from './contexts/UserVideosContext'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ThemeProvider>
      <HistoryProvider>
        <UserVideosProvider>
          <App />
        </UserVideosProvider>
      </HistoryProvider>
    </ThemeProvider>
  </StrictMode>,
)

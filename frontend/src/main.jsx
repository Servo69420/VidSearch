import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.jsx'
import { AuthProvider } from './contexts/AuthContext'
import { ThemeProvider } from './contexts/ThemeContext'
import { WatchLaterProvider } from './contexts/WatchLaterContext'
import { HistoryProvider } from './contexts/HistoryContext'
import { UserVideosProvider } from './contexts/UserVideosContext'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ThemeProvider>
      <AuthProvider>
        <WatchLaterProvider>
          <HistoryProvider>
            <UserVideosProvider>
              <App />
            </UserVideosProvider>
          </HistoryProvider>
        </WatchLaterProvider>
      </AuthProvider>
    </ThemeProvider>
  </StrictMode>,
)

import { useHashRouter, navigate } from './router'
import { useAuth } from './contexts/AuthContext'
import Navbar from './components/layout/Navbar'
import Footer from './components/layout/Footer'

// Public pages
import HomePage from './pages/public/HomePage'
import BrowseVideosPage from './pages/public/BrowseVideosPage'
import VideoDetailsPage from './pages/public/VideoDetailsPage'
import PricingPage from './pages/public/PricingPage'
import HowItWorksPage from './pages/public/HowItWorksPage'
import FAQPage from './pages/public/FAQPage'
import AboutPage from './pages/public/AboutPage'
import ContactPage from './pages/public/ContactPage'
import LoginPage from './pages/public/LoginPage'
import SignUpPage from './pages/public/SignUpPage'

// Dashboard pages
import DashboardPage from './pages/dashboard/DashboardPage'
import WatchPage from './pages/dashboard/WatchPage'
import HistoryPage from './pages/dashboard/HistoryPage'
import WatchedPage from './pages/dashboard/WatchedPage'
import SavedPage from './pages/dashboard/SavedPage'
import SubscriptionPage from './pages/dashboard/SubscriptionPage'
import ProfilePage from './pages/dashboard/ProfilePage'
import SettingsPage from './pages/dashboard/SettingsPage'
import NotificationsPage from './pages/dashboard/NotificationsPage'

// Legal pages
import PrivacyPage from './pages/legal/PrivacyPage'
import TermsPage from './pages/legal/TermsPage'
import CookiePage from './pages/legal/CookiePage'

import './styles/variables.css'
import './styles/global.css'

const PROTECTED = ['/dashboard', '/watch', '/history', '/watched', '/saved', '/subscription', '/profile', '/settings', '/notifications']

const ROUTES = [
  { path: '/', component: HomePage },
  { path: '/browse', component: BrowseVideosPage },
  { path: '/video/:id', component: VideoDetailsPage },
  { path: '/pricing', component: PricingPage },
  { path: '/how-it-works', component: HowItWorksPage },
  { path: '/faq', component: FAQPage },
  { path: '/about', component: AboutPage },
  { path: '/contact', component: ContactPage },
  { path: '/login', component: LoginPage },
  { path: '/signup', component: SignUpPage },
  { path: '/dashboard', component: DashboardPage },
  { path: '/watch', component: WatchPage },
  { path: '/watch/:id', component: WatchPage },
  { path: '/history', component: HistoryPage },
  { path: '/watched', component: WatchedPage },
  { path: '/saved', component: SavedPage },
  { path: '/subscription', component: SubscriptionPage },
  { path: '/profile', component: ProfilePage },
  { path: '/settings', component: SettingsPage },
  { path: '/notifications', component: NotificationsPage },
  { path: '/privacy', component: PrivacyPage },
  { path: '/terms', component: TermsPage },
  { path: '/cookies', component: CookiePage },
]

export default function App() {
  const { current, params } = useHashRouter(ROUTES)
  const { user, loading } = useAuth()
  const Page = current.component

  if (loading) return null

  const isProtected = PROTECTED.some(p => current.path === p || current.path.startsWith(p + '/'))
  if (isProtected && !user) {
    navigate('/login')
    return null
  }

  return (
    <div className="app">
      <Navbar />
      <main className="main-content">
        <Page params={params} />
      </main>
      <Footer />
    </div>
  )
}

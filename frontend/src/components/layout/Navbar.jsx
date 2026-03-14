import { useState, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import Avatar from '../ui/Avatar'
import Dropdown from '../ui/Dropdown'
import './Navbar.css'

export default function Navbar() {
  const { user, logout } = useAuth()
  const [hash, setHash] = useState(window.location.hash || '#/')
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    function onHash() { setHash(window.location.hash || '#/') }
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

  const path = hash.replace(/^#/, '') || '/'
  const isActive = (p) => path === p || path.startsWith(p + '/') ? 'active' : ''

  const publicLinks = [
    { label: 'Home', href: '#/' },
    { label: 'Browse Videos', href: '#/browse' },
    { label: 'Pricing', href: '#/pricing' },
    { label: 'How It Works', href: '#/how-it-works' },
  ]

  const loggedInLinks = [
    { label: 'Home', href: '#/' },
    { label: 'Browse Videos', href: '#/browse' },
    { label: 'Dashboard', href: '#/dashboard' },
    { label: 'History', href: '#/history' },
  ]

  const links = user ? loggedInLinks : publicLinks

  const accountItems = [
    { label: 'Profile', icon: '\u2630', onClick: () => window.location.hash = '#/profile' },
    { label: 'Subscription', icon: '\u2606', onClick: () => window.location.hash = '#/subscription' },
    { label: 'Settings', icon: '\u2699', onClick: () => window.location.hash = '#/settings' },
    { divider: true },
    { label: 'Sign Out', icon: '\u2192', danger: true, onClick: () => { logout(); window.location.hash = '#/' } },
  ]

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <a href="#/" className="navbar-logo">
          <div className="navbar-logo-icon">&#9654;</div>
          <span>VideoSearch</span>
        </a>

        <div className={`navbar-links ${menuOpen ? 'open' : ''}`}>
          {links.map(l => {
            const p = l.href.replace('#', '')
            return (
              <a key={l.href} href={l.href} className={`navbar-link ${isActive(p)}`} onClick={() => setMenuOpen(false)}>
                {l.label}
              </a>
            )
          })}
        </div>

        <div className="navbar-actions">
          {user ? (
            <>
              <a href="#/notifications" className={`navbar-notif ${isActive('/notifications')}`} title="Notifications">
                &#128276;
              </a>
              <Dropdown
                trigger={<Avatar name={`${user.name} ${user.surname}`} size="sm" />}
                items={accountItems}
                align="right"
              />
            </>
          ) : (
            <>
              <a href="#/login" className="navbar-login">Log In</a>
              <a href="#/signup" className="navbar-signup">Sign Up</a>
            </>
          )}
          <button className="navbar-hamburger" onClick={() => setMenuOpen(!menuOpen)}>
            {menuOpen ? '\u2715' : '\u2630'}
          </button>
        </div>
      </div>
    </nav>
  )
}

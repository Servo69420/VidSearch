import { useState } from 'react'
import { useAuth } from './AuthContext'
import { TOPICS, HOBBY_COLORS } from './data'
import './AuthModal.css'

export default function AuthModal({ onClose }) {
  const { user, login, register, logout } = useAuth()
  const [tab, setTab] = useState('login')

  // Login state
  const [loginName, setLoginName] = useState('')
  const [loginError, setLoginError] = useState('')

  // Register state
  const [regName, setRegName] = useState('')
  const [regSurname, setRegSurname] = useState('')
  const [regHobbies, setRegHobbies] = useState([])
  const [regError, setRegError] = useState('')

  function handleLogin(e) {
    e.preventDefault()
    const ok = login(loginName.trim())
    if (ok) {
      onClose()
    } else {
      setLoginError('No account found with that name. Please create an account.')
    }
  }

  function handleRegister(e) {
    e.preventDefault()
    if (!regName.trim() || !regSurname.trim()) {
      setRegError('Please enter your first and last name.')
      return
    }
    if (regHobbies.length === 0) {
      setRegError('Please select at least one interest.')
      return
    }
    register({ name: regName.trim(), surname: regSurname.trim(), hobbies: regHobbies })
    onClose()
  }

  function toggleHobby(label) {
    setRegHobbies(prev =>
      prev.includes(label) ? prev.filter(h => h !== label) : [...prev, label]
    )
  }

  // Profile view when already logged in
  if (user) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal" onClick={e => e.stopPropagation()}>
          <div className="modal-header">
            <span className="modal-title">My Account</span>
            <button className="modal-close" onClick={onClose}>✕</button>
          </div>
          <div className="modal-body">
            <div className="profile-row">
              <div className="avatar-lg">{user.name[0]}{user.surname[0]}</div>
              <div>
                <div className="profile-name">{user.name} {user.surname}</div>
                <div className="profile-sub">{user.hobbies.length} interest{user.hobbies.length !== 1 ? 's' : ''}</div>
              </div>
            </div>
            <div className="form-group">
              <label>Your Interests</label>
              <div className="hobby-chips">
                {user.hobbies.map(h => (
                  <span key={h} className={`topic-chip ${HOBBY_COLORS[h]?.chip ?? 'chip-indigo'} chip-selected`}>
                    {h} <span className="chip-check">✓</span>
                  </span>
                ))}
              </div>
            </div>
            <button
              className="btn btn-ghost btn-full"
              onClick={() => { logout(); onClose() }}
            >
              Log Out
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-tabs">
            <button
              className={`modal-tab ${tab === 'login' ? 'active' : ''}`}
              onClick={() => setTab('login')}
            >Log In</button>
            <button
              className={`modal-tab ${tab === 'register' ? 'active' : ''}`}
              onClick={() => setTab('register')}
            >Create Account</button>
          </div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        {tab === 'login' && (
          <form className="modal-body" onSubmit={handleLogin}>
            <p className="modal-subtitle">Enter your name to log in to your account.</p>
            <div className="form-group">
              <label>First Name</label>
              <input
                value={loginName}
                onChange={e => { setLoginName(e.target.value); setLoginError('') }}
                placeholder="Your first name"
                autoFocus
              />
            </div>
            {loginError && <p className="form-error">{loginError}</p>}
            <button type="submit" className="btn btn-primary btn-full">Log In</button>
            <p className="modal-switch">
              No account yet?{' '}
              <button type="button" className="link-btn" onClick={() => setTab('register')}>
                Create one
              </button>
            </p>
          </form>
        )}

        {tab === 'register' && (
          <form className="modal-body" onSubmit={handleRegister}>
            <div className="form-row">
              <div className="form-group">
                <label>First Name</label>
                <input
                  value={regName}
                  onChange={e => { setRegName(e.target.value); setRegError('') }}
                  placeholder="First name"
                  autoFocus
                />
              </div>
              <div className="form-group">
                <label>Last Name</label>
                <input
                  value={regSurname}
                  onChange={e => { setRegSurname(e.target.value); setRegError('') }}
                  placeholder="Last name"
                />
              </div>
            </div>
            <div className="form-group">
              <label>Your Interests</label>
              <p className="form-hint">Select topics to personalise your video feed</p>
              <div className="hobby-chips">
                {TOPICS.map(t => {
                  const selected = regHobbies.includes(t.label)
                  return (
                    <button
                      key={t.label}
                      type="button"
                      className={`topic-chip ${t.color} ${selected ? 'chip-selected' : ''}`}
                      onClick={() => toggleHobby(t.label)}
                    >
                      {t.label}
                      {selected && <span className="chip-check">✓</span>}
                    </button>
                  )
                })}
              </div>
            </div>
            {regError && <p className="form-error">{regError}</p>}
            <button type="submit" className="btn btn-primary btn-full">Create Account</button>
            <p className="modal-switch">
              Already have an account?{' '}
              <button type="button" className="link-btn" onClick={() => setTab('login')}>
                Log in
              </button>
            </p>
          </form>
        )}
      </div>
    </div>
  )
}

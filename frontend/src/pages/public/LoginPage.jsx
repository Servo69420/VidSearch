import { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { navigate } from '../../router'
import './LoginPage.css'

export default function LoginPage() {
  const { login } = useAuth()
  const [name, setName] = useState('')
  const [error, setError] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    if (!name.trim()) {
      setError('Please enter your first name.')
      return
    }
    const ok = login(name.trim())
    if (ok) {
      navigate('/dashboard')
    } else {
      setError('No account found with that name. Try signing up instead.')
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-header">
          <a href="#/" className="auth-logo">
            <div className="auth-logo-icon">&#9654;</div>
            VideoSearch
          </a>
          <h3>Welcome back</h3>
          <p>Sign in to your account to continue learning.</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="auth-field">
            <label>First Name</label>
            <input
              type="text"
              placeholder="Enter your first name"
              value={name}
              onChange={e => { setName(e.target.value); setError('') }}
              autoFocus
            />
          </div>

          {error && <div className="auth-error">{error}</div>}

          <button type="submit" className="auth-submit">Sign In</button>
        </form>

        <div className="auth-footer">
          Don&apos;t have an account? <a href="#/signup">Sign up</a>
        </div>
      </div>
    </div>
  )
}

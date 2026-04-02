import { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { navigate } from '../../router'
import './LoginPage.css'

export default function LoginPage() {
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!username.trim()) { setError('Please enter your username.'); return }
    if (!password.trim()) { setError('Please enter your password.'); return }
    setSubmitting(true)
    try {
      await login(username.trim(), password.trim())
      navigate('/dashboard')
    } catch (err) {
      setError(err.message || 'Invalid username or password. Try again or sign up.')
    } finally {
      setSubmitting(false)
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
            <label>Username</label>
            <input
              type="text"
              placeholder="Enter your username"
              value={username}
              onChange={e => { setUsername(e.target.value); setError('') }}
              autoFocus
            />
          </div>

          <div className="auth-field">
            <label>Password</label>
            <input
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={e => { setPassword(e.target.value); setError('') }}
            />
          </div>

          {error && <div className="auth-error">{error}</div>}

          <button type="submit" className="auth-submit" disabled={submitting}>
            {submitting ? 'Signing in…' : 'Sign In'}
          </button>
        </form>

        <div className="auth-footer">
          Don&apos;t have an account? <a href="#/signup">Sign up</a>
        </div>
      </div>
    </div>
  )
}

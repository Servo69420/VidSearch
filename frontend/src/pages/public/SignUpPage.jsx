import { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { navigate } from '../../router'
import { TOPICS } from '../../data/data'
import './LoginPage.css'

export default function SignUpPage() {
  const { register } = useAuth()
  const [form, setForm] = useState({ username: '', password: '', name: '', surname: '', email: '' })
  const [hobbies, setHobbies] = useState([])
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

  function toggleHobby(label) {
    setHobbies(prev =>
      prev.includes(label) ? prev.filter(h => h !== label) : [...prev, label]
    )
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!form.username.trim()) { setError('Please enter a username.'); return }
    if (!form.password.trim()) { setError('Please enter a password.'); return }
    setSubmitting(true)
    try {
      await register({
        username: form.username.trim(),
        password: form.password.trim(),
        name: form.name.trim(),
        surname: form.surname.trim(),
        email: form.email.trim(),
        hobbies,
      })
      navigate('/dashboard')
    } catch (err) {
      setError(err.message || 'Registration failed. Please try again.')
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
          <h3>Create your account</h3>
          <p>Start learning from videos with AI-powered explanations.</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="auth-field">
            <label>Username</label>
            <input
              type="text"
              placeholder="Choose a username"
              value={form.username}
              onChange={e => { setForm(p => ({ ...p, username: e.target.value })); setError('') }}
              autoFocus
            />
          </div>

          <div className="auth-field">
            <label>Password</label>
            <div className="auth-password-wrapper">
              <input
                type={showPassword ? 'text' : 'password'}
                placeholder="Create a password"
                value={form.password}
                onChange={e => { setForm(p => ({ ...p, password: e.target.value })); setError('') }}
              />
              <button
                type="button"
                className="auth-password-toggle"
                onClick={() => setShowPassword(p => !p)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? '🙈' : '👁️'}
              </button>
            </div>
          </div>

          <div className="auth-row">
            <div className="auth-field">
              <label>First Name <span className="auth-optional">(optional)</span></label>
              <input
                type="text"
                placeholder="John"
                value={form.name}
                onChange={e => { setForm(p => ({ ...p, name: e.target.value })); setError('') }}
              />
            </div>
            <div className="auth-field">
              <label>Last Name <span className="auth-optional">(optional)</span></label>
              <input
                type="text"
                placeholder="Doe"
                value={form.surname}
                onChange={e => { setForm(p => ({ ...p, surname: e.target.value })); setError('') }}
              />
            </div>
          </div>

          <div className="auth-field">
            <label>Email <span className="auth-optional">(optional)</span></label>
            <input
              type="email"
              placeholder="john@example.com"
              value={form.email}
              onChange={e => { setForm(p => ({ ...p, email: e.target.value })); setError('') }}
            />
          </div>

          <div>
            <div className="auth-interests-label">Select your interests (optional)</div>
            <div className="auth-interests-grid">
              {TOPICS.map(t => (
                <button
                  key={t.label}
                  type="button"
                  className={`auth-interest-chip ${hobbies.includes(t.label) ? 'selected' : ''}`}
                  onClick={() => toggleHobby(t.label)}
                >
                  {hobbies.includes(t.label) && '\u2713 '}{t.label}
                </button>
              ))}
            </div>
          </div>

          {error && <div className="auth-error">{error}</div>}

          <button type="submit" className="auth-submit" disabled={submitting}>
            {submitting ? 'Creating account…' : 'Create Account'}
          </button>
        </form>

        <div className="auth-footer">
          Already have an account? <a href="#/login">Sign in</a>
        </div>
      </div>
    </div>
  )
}

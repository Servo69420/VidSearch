import { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { navigate } from '../../router'
import { TOPICS } from '../../data/data'
import './LoginPage.css'

export default function SignUpPage() {
  const { register } = useAuth()
  const [form, setForm] = useState({ name: '', surname: '', email: '' })
  const [hobbies, setHobbies] = useState([])
  const [error, setError] = useState('')

  function toggleHobby(label) {
    setHobbies(prev =>
      prev.includes(label) ? prev.filter(h => h !== label) : [...prev, label]
    )
  }

  function handleSubmit(e) {
    e.preventDefault()
    if (!form.name.trim() || !form.surname.trim()) {
      setError('Please enter your name.')
      return
    }
    if (!form.email.trim()) {
      setError('Please enter your email.')
      return
    }

    register({
      name: form.name.trim(),
      surname: form.surname.trim(),
      email: form.email.trim(),
      hobbies,
    })
    navigate('/dashboard')
  }

  return (
    <div className="auth-page">
      <div className="auth-card" style={{ maxWidth: 480 }}>
        <div className="auth-header">
          <a href="#/" className="auth-logo">
            <div className="auth-logo-icon">&#9654;</div>
            VidSearch
          </a>
          <h3>Create your account</h3>
          <p>Start learning from videos with AI-powered explanations.</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="auth-row">
            <div className="auth-field">
              <label>First Name</label>
              <input
                type="text"
                placeholder="John"
                value={form.name}
                onChange={e => { setForm(p => ({ ...p, name: e.target.value })); setError('') }}
                autoFocus
              />
            </div>
            <div className="auth-field">
              <label>Last Name</label>
              <input
                type="text"
                placeholder="Doe"
                value={form.surname}
                onChange={e => { setForm(p => ({ ...p, surname: e.target.value })); setError('') }}
              />
            </div>
          </div>

          <div className="auth-field">
            <label>Email</label>
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

          <button type="submit" className="auth-submit">Create Account</button>
        </form>

        <div className="auth-footer">
          Already have an account? <a href="#/login">Sign in</a>
        </div>
      </div>
    </div>
  )
}

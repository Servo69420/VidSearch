import { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { TOPICS } from '../../data/data'
import './ProfilePage.css'

export default function ProfilePage() {
  const { user, updateProfile } = useAuth()
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({
    name: user?.name || '',
    surname: user?.surname || '',
    email: user?.email || '',
  })
  const [hobbies, setHobbies] = useState(user?.hobbies || [])
  const [saved, setSaved] = useState(false)

  function toggleHobby(label) {
    setHobbies(prev => prev.includes(label) ? prev.filter(h => h !== label) : [...prev, label])
  }

  function handleSave() {
    updateProfile({ ...form, hobbies })
    setEditing(false)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const initials = user ? `${user.name[0]}${user.surname[0]}`.toUpperCase() : '?'

  return (
    <div className="profile-page">
      <div className="profile-header">
        <h3>Profile</h3>
        <p>Manage your account information and interests.</p>
      </div>

      <div className="profile-card">
        <div className="profile-avatar-section">
          <div className="profile-avatar">{initials}</div>
          <div>
            <div className="profile-name">{user?.name} {user?.surname}</div>
            <div className="profile-email">{user?.email || 'No email set'}</div>
            <div className="profile-joined">Member since {user?.joinedAt ? new Date(user.joinedAt).toLocaleDateString() : 'today'}</div>
          </div>
        </div>

        {!editing ? (
          <button className="profile-edit-btn" onClick={() => setEditing(true)}>Edit Profile</button>
        ) : null}
      </div>

      {editing ? (
        <div className="profile-form-card">
          <div className="profile-form-row">
            <div className="profile-form-field">
              <label>First Name</label>
              <input value={form.name} onChange={e => setForm(p => ({ ...p, name: e.target.value }))} />
            </div>
            <div className="profile-form-field">
              <label>Last Name</label>
              <input value={form.surname} onChange={e => setForm(p => ({ ...p, surname: e.target.value }))} />
            </div>
          </div>
          <div className="profile-form-field">
            <label>Email</label>
            <input type="email" value={form.email} onChange={e => setForm(p => ({ ...p, email: e.target.value }))} />
          </div>

          <div className="profile-form-field">
            <label>Interests</label>
            <div className="profile-interests">
              {TOPICS.map(t => (
                <button
                  key={t.label}
                  type="button"
                  className={`profile-interest-chip ${hobbies.includes(t.label) ? 'selected' : ''}`}
                  onClick={() => toggleHobby(t.label)}
                >
                  {hobbies.includes(t.label) && '\u2713 '}{t.label}
                </button>
              ))}
            </div>
          </div>

          <div className="profile-form-actions">
            <button className="profile-save-btn" onClick={handleSave}>Save Changes</button>
            <button className="profile-cancel-btn" onClick={() => setEditing(false)}>Cancel</button>
          </div>
        </div>
      ) : (
        <div className="profile-details-card">
          <div className="profile-detail-row">
            <span className="profile-detail-label">Email</span>
            <span className="profile-detail-value">{user?.email || '\u2014'}</span>
          </div>
          <div className="profile-detail-row">
            <span className="profile-detail-label">Subscription</span>
            <span className="profile-detail-value profile-plan-badge">{(user?.subscription || 'free').charAt(0).toUpperCase() + (user?.subscription || 'free').slice(1)}</span>
          </div>
          <div className="profile-detail-row">
            <span className="profile-detail-label">Interests</span>
            <span className="profile-detail-value">
              {user?.hobbies?.length ? user.hobbies.join(', ') : 'None selected'}
            </span>
          </div>
        </div>
      )}

      {saved && <div className="profile-saved-toast">Profile updated successfully!</div>}
    </div>
  )
}

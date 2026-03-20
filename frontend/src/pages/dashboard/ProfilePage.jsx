import { useState, useRef } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import './ProfilePage.css'

export default function ProfilePage() {
  const { user, updateProfile, uploadAvatar, API_BASE } = useAuth()
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({
    name: user?.name || '',
    surname: user?.surname || '',
    email: user?.email || '',
  })
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')
  const [uploading, setUploading] = useState(false)
  const [saving, setSaving] = useState(false)
  const fileRef = useRef(null)

  const initials = user
    ? (user.name && user.surname
        ? `${user.name[0]}${user.surname[0]}`
        : user.username?.slice(0, 2) || '?'
      ).toUpperCase()
    : '?'

  const avatarSrc = user?.avatar_url ? `${API_BASE}${user.avatar_url}` : null

  async function handleAvatarChange(e) {
    const file = e.target.files?.[0]
    if (!file) return
    setError('')
    setUploading(true)
    try {
      await uploadAvatar(file)
    } catch (err) {
      setError(err.message)
    } finally {
      setUploading(false)
    }
  }

  async function handleSave() {
    setError('')
    setSaving(true)
    try {
      await updateProfile(form)
      setEditing(false)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const displayName = [user?.name, user?.surname].filter(Boolean).join(' ') || user?.username || ''

  return (
    <div className="profile-page">
      <div className="profile-header">
        <h3>Profile</h3>
        <p>Manage your account information.</p>
      </div>

      {error && <div className="profile-error">{error}</div>}

      <div className="profile-card">
        <div className="profile-avatar-section">
          <div className="profile-avatar-wrapper" onClick={() => fileRef.current?.click()}>
            {avatarSrc ? (
              <img src={avatarSrc} alt="Avatar" className="profile-avatar-img" />
            ) : (
              <div className="profile-avatar">{initials}</div>
            )}
            <div className="profile-avatar-overlay">
              {uploading ? '...' : '\u270E'}
            </div>
            <input
              ref={fileRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={handleAvatarChange}
              hidden
            />
          </div>
          <div>
            <div className="profile-name">{displayName}</div>
            <div className="profile-username">@{user?.username}</div>
            <div className="profile-email">{user?.email || 'No email set'}</div>
            <div className="profile-joined">
              Member since {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'today'}
            </div>
          </div>
        </div>

        {!editing && (
          <button className="profile-edit-btn" onClick={() => {
            setForm({ name: user?.name || '', surname: user?.surname || '', email: user?.email || '' })
            setEditing(true)
          }}>
            Edit Profile
          </button>
        )}
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

          <div className="profile-form-actions">
            <button className="profile-save-btn" onClick={handleSave} disabled={saving}>
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
            <button className="profile-cancel-btn" onClick={() => setEditing(false)}>Cancel</button>
          </div>
        </div>
      ) : (
        <div className="profile-details-card">
          <div className="profile-detail-row">
            <span className="profile-detail-label">Username</span>
            <span className="profile-detail-value">{user?.username}</span>
          </div>
          <div className="profile-detail-row">
            <span className="profile-detail-label">First Name</span>
            <span className="profile-detail-value">{user?.name || '\u2014'}</span>
          </div>
          <div className="profile-detail-row">
            <span className="profile-detail-label">Last Name</span>
            <span className="profile-detail-value">{user?.surname || '\u2014'}</span>
          </div>
          <div className="profile-detail-row">
            <span className="profile-detail-label">Email</span>
            <span className="profile-detail-value">{user?.email || '\u2014'}</span>
          </div>
          <div className="profile-detail-row">
            <span className="profile-detail-label">Subscription</span>
            <span className="profile-detail-value profile-plan-badge">
              {(user?.subscription || 'free').charAt(0).toUpperCase() + (user?.subscription || 'free').slice(1)}
            </span>
          </div>
        </div>
      )}

      {saved && <div className="profile-saved-toast">Profile updated successfully!</div>}
    </div>
  )
}

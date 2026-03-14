import { useState } from 'react'
import './SettingsPage.css'

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    emailNotifs: true,
    weeklyDigest: true,
    newFeatures: false,
    autoplay: true,
    darkMode: false,
  })

  function toggle(key) {
    setSettings(prev => ({ ...prev, [key]: !prev[key] }))
  }

  return (
    <div className="settings-page">
      <div className="settings-header">
        <h3>Settings</h3>
        <p>Manage your preferences and account settings.</p>
      </div>

      <div className="settings-section">
        <h5>Notifications</h5>
        <div className="settings-card">
          <div className="settings-row">
            <div className="settings-row-info">
              <div className="settings-row-label">Email Notifications</div>
              <div className="settings-row-desc">Receive email alerts about your activity.</div>
            </div>
            <button className={`settings-toggle ${settings.emailNotifs ? 'on' : ''}`} onClick={() => toggle('emailNotifs')}>
              <span className="settings-toggle-knob" />
            </button>
          </div>
          <div className="settings-row">
            <div className="settings-row-info">
              <div className="settings-row-label">Weekly Digest</div>
              <div className="settings-row-desc">Get a weekly summary of your learning progress.</div>
            </div>
            <button className={`settings-toggle ${settings.weeklyDigest ? 'on' : ''}`} onClick={() => toggle('weeklyDigest')}>
              <span className="settings-toggle-knob" />
            </button>
          </div>
          <div className="settings-row">
            <div className="settings-row-info">
              <div className="settings-row-label">New Features</div>
              <div className="settings-row-desc">Be notified about new features and updates.</div>
            </div>
            <button className={`settings-toggle ${settings.newFeatures ? 'on' : ''}`} onClick={() => toggle('newFeatures')}>
              <span className="settings-toggle-knob" />
            </button>
          </div>
        </div>
      </div>

      <div className="settings-section">
        <h5>Preferences</h5>
        <div className="settings-card">
          <div className="settings-row">
            <div className="settings-row-info">
              <div className="settings-row-label">Autoplay Videos</div>
              <div className="settings-row-desc">Automatically play videos when opening the workspace.</div>
            </div>
            <button className={`settings-toggle ${settings.autoplay ? 'on' : ''}`} onClick={() => toggle('autoplay')}>
              <span className="settings-toggle-knob" />
            </button>
          </div>
        </div>
      </div>

      <div className="settings-section">
        <h5>Account</h5>
        <div className="settings-card">
          <div className="settings-row">
            <div className="settings-row-info">
              <div className="settings-row-label">Change Password</div>
              <div className="settings-row-desc">Update your account password.</div>
            </div>
            <button className="settings-action-btn">Change</button>
          </div>
          <div className="settings-row">
            <div className="settings-row-info">
              <div className="settings-row-label settings-danger">Delete Account</div>
              <div className="settings-row-desc">Permanently delete your account and all data.</div>
            </div>
            <button className="settings-danger-btn">Delete</button>
          </div>
        </div>
      </div>
    </div>
  )
}

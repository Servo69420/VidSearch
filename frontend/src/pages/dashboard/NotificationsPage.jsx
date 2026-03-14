import { useState } from 'react'
import { SAMPLE_NOTIFICATIONS } from '../../data/data'
import './NotificationsPage.css'

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState(SAMPLE_NOTIFICATIONS)

  function markAllRead() {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })))
  }

  const unreadCount = notifications.filter(n => !n.read).length

  const typeIcons = { info: '\u2139\uFE0F', success: '\u2705', warning: '\u26A0\uFE0F' }

  return (
    <div className="notif-page">
      <div className="notif-header">
        <div>
          <h3>Notifications</h3>
          <p>{unreadCount > 0 ? `You have ${unreadCount} unread notification${unreadCount !== 1 ? 's' : ''}.` : 'All caught up!'}</p>
        </div>
        {unreadCount > 0 && (
          <button className="notif-mark-btn" onClick={markAllRead}>Mark all as read</button>
        )}
      </div>

      <div className="notif-list">
        {notifications.map(n => (
          <div key={n.id} className={`notif-item ${n.read ? '' : 'unread'}`}>
            <div className="notif-icon">{typeIcons[n.type] || '\u2139\uFE0F'}</div>
            <div className="notif-content">
              <div className="notif-title">{n.title}</div>
              <div className="notif-message">{n.message}</div>
              <div className="notif-time">{n.time}</div>
            </div>
            {!n.read && <div className="notif-unread-dot" />}
          </div>
        ))}
      </div>
    </div>
  )
}

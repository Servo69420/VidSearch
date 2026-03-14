import './StatCard.css'

export default function StatCard({ label, value, change, changeType = 'neutral', icon }) {
  return (
    <div className="scard">
      <div className="scard-top">
        <div className="scard-label">{label}</div>
        {icon && <div className="scard-icon">{icon}</div>}
      </div>
      <div className="scard-value">{value}</div>
      {change && <div className={`scard-change scard-${changeType}`}>{change}</div>}
    </div>
  )
}

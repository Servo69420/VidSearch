import './Avatar.css'

export default function Avatar({ name = '', size = 'md', className = '' }) {
  const initials = name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2) || '?'
  return <div className={`avatar avatar-${size} ${className}`}>{initials}</div>
}

import { useState, useRef, useEffect } from 'react'
import './Dropdown.css'

export default function Dropdown({ trigger, items, align = 'right' }) {
  const [open, setOpen] = useState(false)
  const ref = useRef()

  useEffect(() => {
    function handleClick(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  return (
    <div className="dropdown" ref={ref}>
      <div className="dropdown-trigger" onClick={() => setOpen(!open)}>{trigger}</div>
      {open && (
        <div className={`dropdown-menu dropdown-${align}`}>
          {items.map((item, i) =>
            item.divider ? (
              <div key={i} className="dropdown-divider" />
            ) : (
              <button
                key={i}
                className={`dropdown-item ${item.danger ? 'dropdown-danger' : ''}`}
                onClick={() => { item.onClick?.(); setOpen(false) }}
              >
                {item.icon && <span className="dropdown-icon">{item.icon}</span>}
                {item.label}
              </button>
            )
          )}
        </div>
      )}
    </div>
  )
}

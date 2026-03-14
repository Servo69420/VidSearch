import './Input.css'

export default function Input({ label, error, hint, multiline, className = '', ...rest }) {
  const Tag = multiline ? 'textarea' : 'input'
  return (
    <div className={`input-group ${error ? 'has-error' : ''} ${className}`}>
      {label && <label className="input-label">{label}</label>}
      <Tag className="input-field" {...rest} />
      {error && <div className="input-error">{error}</div>}
      {hint && !error && <div className="input-hint">{hint}</div>}
    </div>
  )
}

import './Button.css'

export default function Button({ variant = 'primary', size = 'md', children, className = '', ...rest }) {
  return (
    <button className={`btn btn-${variant} btn-${size} ${className}`} {...rest}>
      {children}
    </button>
  )
}

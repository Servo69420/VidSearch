import './SearchBar.css'

export default function SearchBar({ placeholder = 'Search...', value, onChange, className = '' }) {
  return (
    <div className={`searchbar ${className}`}>
      <span className="searchbar-icon">&#8981;</span>
      <input
        className="searchbar-input"
        placeholder={placeholder}
        value={value}
        onChange={e => onChange(e.target.value)}
      />
      {value && (
        <button className="searchbar-clear" onClick={() => onChange('')}>&times;</button>
      )}
    </div>
  )
}

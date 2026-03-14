import { useState } from 'react'
import './Accordion.css'

export default function Accordion({ items }) {
  const [openIndex, setOpenIndex] = useState(null)

  return (
    <div className="accordion">
      {items.map((item, i) => (
        <div key={i} className={`accordion-item ${openIndex === i ? 'open' : ''}`}>
          <button className="accordion-trigger" onClick={() => setOpenIndex(openIndex === i ? null : i)}>
            <span className="accordion-question">{item.question}</span>
            <span className="accordion-chevron">{openIndex === i ? '\u2212' : '\u002B'}</span>
          </button>
          <div className="accordion-content">
            <div className="accordion-answer">{item.answer}</div>
          </div>
        </div>
      ))}
    </div>
  )
}

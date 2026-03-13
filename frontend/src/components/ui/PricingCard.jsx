import './PricingCard.css'

export default function PricingCard({ plan }) {
  return (
    <div className={`pcard ${plan.highlighted ? 'pcard-highlighted' : ''}`}>
      {plan.highlighted && <div className="pcard-badge">Most Popular</div>}
      <div className="pcard-header">
        <div className="pcard-name">{plan.name}</div>
        <div className="pcard-price">
          {plan.price === 0 ? (
            <span className="pcard-amount">Free</span>
          ) : (
            <>
              <span className="pcard-currency">$</span>
              <span className="pcard-amount">{plan.price}</span>
              <span className="pcard-period">/{plan.period}</span>
            </>
          )}
        </div>
        <div className="pcard-desc">{plan.description}</div>
      </div>
      <div className="pcard-features">
        {plan.features.map((f, i) => (
          <div key={i} className="pcard-feature">
            <span className="pcard-check">&#10003;</span>
            {f}
          </div>
        ))}
      </div>
      <button className={`pcard-cta ${plan.highlighted ? 'pcard-cta-gold' : ''}`}>
        {plan.cta}
      </button>
    </div>
  )
}

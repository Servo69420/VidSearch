import { HOW_IT_WORKS_STEPS, FEATURES } from '../../data/data'
import './HowItWorksPage.css'

export default function HowItWorksPage() {
  return (
    <div className="hiw-page">
      <section className="hiw-hero">
        <div className="container">
          <div className="section-header">
            <div className="hiw-badge">How It Works</div>
            <h1>From Video to Understanding<br />in Seconds</h1>
            <p>VideoSearch uses AI to transform any YouTube video into an interactive learning experience.</p>
          </div>
        </div>
      </section>

      <section className="section hiw-steps-section">
        <div className="container">
          <div className="hiw-steps">
            {HOW_IT_WORKS_STEPS.map((s, i) => (
              <div className="hiw-step" key={s.step}>
                <div className="hiw-step-visual">
                  <div className="hiw-step-number">{s.step}</div>
                  {i < HOW_IT_WORKS_STEPS.length - 1 && <div className="hiw-step-line" />}
                </div>
                <div className="hiw-step-content">
                  <h3>{s.title}</h3>
                  <p>{s.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section hiw-features-section">
        <div className="container">
          <div className="section-header">
            <h2>Powerful Features</h2>
            <p>Everything you need for effective video-based learning.</p>
          </div>
          <div className="hiw-features-grid">
            {FEATURES.map((f, i) => (
              <div className="hiw-feature-card" key={i}>
                <div className="hiw-feature-icon">{f.icon}</div>
                <h5>{f.title}</h5>
                <p>{f.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section hiw-cta-section">
        <div className="container">
          <div className="hiw-cta">
            <h2>Ready to Try It?</h2>
            <p>Start with 5 free video explanations per month. No credit card required.</p>
            <a href="#/signup" className="hiw-cta-btn">Get Started Free</a>
          </div>
        </div>
      </section>
    </div>
  )
}

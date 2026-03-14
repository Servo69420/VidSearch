import { PRICING_PLANS, FAQ_ITEMS } from '../../data/data'
import PricingCard from '../../components/ui/PricingCard'
import Accordion from '../../components/ui/Accordion'
import './PricingPage.css'

export default function PricingPage() {
  return (
    <div className="pricing-page">
      <section className="pricing-hero">
        <div className="container">
          <div className="section-header">
            <div className="pricing-badge">Pricing</div>
            <h1>Simple, Transparent Pricing</h1>
            <p>Start for free. Upgrade when you need more. Cancel anytime.</p>
          </div>
        </div>
      </section>

      <section className="pricing-cards-section">
        <div className="container">
          <div className="pricing-grid">
            {PRICING_PLANS.map((plan, i) => (
              <PricingCard key={i} plan={plan} />
            ))}
          </div>
        </div>
      </section>

      <section className="section pricing-comparison">
        <div className="container">
          <h3 style={{ textAlign: 'center', marginBottom: 32 }}>Feature Comparison</h3>
          <div className="comparison-table-wrapper">
            <table className="comparison-table">
              <thead>
                <tr>
                  <th>Feature</th>
                  <th>Free</th>
                  <th className="highlight-col">Pro</th>
                  <th>Premium</th>
                </tr>
              </thead>
              <tbody>
                <tr><td>Video explanations</td><td>5 / month</td><td className="highlight-col">Unlimited</td><td>Unlimited</td></tr>
                <tr><td>AI Q&A</td><td>Basic</td><td className="highlight-col">Advanced</td><td>Custom AI</td></tr>
                <tr><td>Saved clips</td><td>&#8212;</td><td className="highlight-col">&#10003;</td><td>&#10003;</td></tr>
                <tr><td>Search history</td><td>&#8212;</td><td className="highlight-col">&#10003;</td><td>&#10003;</td></tr>
                <tr><td>Export notes</td><td>&#8212;</td><td className="highlight-col">PDF</td><td>PDF + API</td></tr>
                <tr><td>Team features</td><td>&#8212;</td><td className="highlight-col">&#8212;</td><td>&#10003;</td></tr>
                <tr><td>API access</td><td>&#8212;</td><td className="highlight-col">&#8212;</td><td>&#10003;</td></tr>
                <tr><td>Support</td><td>Community</td><td className="highlight-col">Priority</td><td>Dedicated</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="section pricing-faq">
        <div className="container" style={{ maxWidth: 720 }}>
          <div className="section-header">
            <h3>Frequently Asked Questions</h3>
          </div>
          <Accordion items={FAQ_ITEMS.slice(0, 4)} />
          <div style={{ textAlign: 'center', marginTop: 24 }}>
            <a href="#/faq" className="pricing-faq-link">View all FAQs &#8594;</a>
          </div>
        </div>
      </section>
    </div>
  )
}

import { useAuth } from '../../contexts/AuthContext'
import { PRICING_PLANS } from '../../data/data'
import PricingCard from '../../components/ui/PricingCard'
import './SubscriptionPage.css'

const BILLING_HISTORY = [
  { date: 'Mar 1, 2026', description: 'Pro Plan - Monthly', amount: '$12.00', status: 'Paid' },
  { date: 'Feb 1, 2026', description: 'Pro Plan - Monthly', amount: '$12.00', status: 'Paid' },
  { date: 'Jan 1, 2026', description: 'Pro Plan - Monthly', amount: '$12.00', status: 'Paid' },
]

export default function SubscriptionPage() {
  const { user } = useAuth()
  const currentPlan = user?.subscription || 'free'

  return (
    <div className="sub-page">
      <div className="sub-header">
        <h3>Subscription & Billing</h3>
        <p>Manage your plan and billing information.</p>
      </div>

      <div className="sub-current">
        <div className="sub-current-info">
          <div className="sub-current-label">Current Plan</div>
          <div className="sub-current-plan">{currentPlan.charAt(0).toUpperCase() + currentPlan.slice(1)}</div>
          <div className="sub-current-desc">
            {currentPlan === 'free' ? '5 video explanations per month' : 'Unlimited video explanations'}
          </div>
        </div>
        {currentPlan === 'free' && (
          <a href="#/pricing" className="sub-upgrade-btn">Upgrade Plan</a>
        )}
      </div>

      <div className="sub-plans-section">
        <h5>Available Plans</h5>
        <div className="sub-plans-grid">
          {PRICING_PLANS.map((plan, i) => (
            <PricingCard key={i} plan={plan} />
          ))}
        </div>
      </div>

      <div className="sub-billing">
        <h5>Billing History</h5>
        <div className="sub-billing-table-wrapper">
          <table className="sub-billing-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Description</th>
                <th>Amount</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {BILLING_HISTORY.map((b, i) => (
                <tr key={i}>
                  <td>{b.date}</td>
                  <td>{b.description}</td>
                  <td>{b.amount}</td>
                  <td><span className="sub-status-badge">{b.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

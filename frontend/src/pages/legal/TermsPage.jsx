import './LegalPage.css'

export default function TermsPage() {
  return (
    <div className="legal-page">
      <section className="legal-hero">
        <div className="container"><h1>Terms of Service</h1><p>Last updated: March 2026</p></div>
      </section>
      <section className="section legal-content">
        <div className="container legal-container">
          <h4>1. Acceptance of Terms</h4>
          <p>By accessing or using VidSearch, you agree to be bound by these Terms of Service. If you do not agree, you may not use the service.</p>

          <h4>2. Description of Service</h4>
          <p>VidSearch provides AI-powered video explanation tools that allow users to ask questions about YouTube video content and receive AI-generated answers. The service includes video browsing, Q&A, bookmarking, and progress tracking features.</p>

          <h4>3. User Accounts</h4>
          <p>You are responsible for maintaining the confidentiality of your account credentials. You agree to provide accurate information when creating an account and to update it as needed.</p>

          <h4>4. Acceptable Use</h4>
          <p>You agree not to use VidSearch for any unlawful purpose, to harass others, to distribute malware, or to attempt to gain unauthorized access to our systems. We reserve the right to terminate accounts that violate these terms.</p>

          <h4>5. Intellectual Property</h4>
          <p>VidSearch and its original content are protected by copyright and other intellectual property laws. Video content accessed through VidSearch remains the property of its respective creators.</p>

          <h4>6. Subscriptions and Payments</h4>
          <p>Paid subscriptions are billed monthly or annually. You may cancel at any time, and access continues until the end of the billing period. Prices may change with 30 days advance notice.</p>

          <h4>7. Limitation of Liability</h4>
          <p>VidSearch is provided as-is. We make no warranties about the accuracy of AI-generated explanations. Our liability is limited to the amount paid for the service in the preceding 12 months.</p>

          <h4>8. Changes to Terms</h4>
          <p>We may update these terms from time to time. Continued use of VidSearch after changes constitutes acceptance of the new terms.</p>
        </div>
      </section>
    </div>
  )
}

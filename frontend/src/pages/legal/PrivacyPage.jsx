import './LegalPage.css'

export default function PrivacyPage() {
  return (
    <div className="legal-page">
      <section className="legal-hero">
        <div className="container"><h1>Privacy Policy</h1><p>Last updated: March 2026</p></div>
      </section>
      <section className="section legal-content">
        <div className="container legal-container">
          <h4>1. Information We Collect</h4>
          <p>We collect information you provide directly, such as your name, email address, and learning interests when you create an account. We also collect usage data including videos viewed, questions asked, and interaction patterns to improve our service.</p>

          <h4>2. How We Use Your Information</h4>
          <p>Your information is used to provide and personalize the VidSearch service, including generating AI-powered explanations, recommending content, and tracking your learning progress. We do not sell your personal data to third parties.</p>

          <h4>3. Data Security</h4>
          <p>We implement industry-standard encryption for all data in transit and at rest. Access to personal data is restricted to authorized personnel only, and we regularly audit our security practices.</p>

          <h4>4. Data Retention</h4>
          <p>We retain your personal data for as long as your account is active. If you delete your account, your data will be permanently removed within 30 days, except where retention is required by law.</p>

          <h4>5. Your Rights</h4>
          <p>You have the right to access, correct, or delete your personal data at any time through your account settings. You may also request a copy of your data or ask us to restrict processing.</p>

          <h4>6. Cookies</h4>
          <p>We use essential cookies to maintain your session and preferences. Analytics cookies help us understand how you use VidSearch so we can improve the experience. You can manage cookie preferences in your browser settings.</p>

          <h4>7. Contact</h4>
          <p>If you have questions about this policy, contact us at privacy@vidsearch.com or through our <a href="#/contact">contact page</a>.</p>
        </div>
      </section>
    </div>
  )
}

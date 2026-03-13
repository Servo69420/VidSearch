import './LegalPage.css'

export default function CookiePage() {
  return (
    <div className="legal-page">
      <section className="legal-hero">
        <div className="container"><h1>Cookie Policy</h1><p>Last updated: March 2026</p></div>
      </section>
      <section className="section legal-content">
        <div className="container legal-container">
          <h4>1. What Are Cookies</h4>
          <p>Cookies are small text files stored on your device when you visit a website. They help us remember your preferences and understand how you use VidSearch.</p>

          <h4>2. Cookies We Use</h4>
          <p><strong>Essential cookies:</strong> Required for the service to function. These maintain your login session and remember your preferences.</p>
          <p><strong>Analytics cookies:</strong> Help us understand how users interact with VidSearch so we can improve the experience. These collect anonymized usage data.</p>
          <p><strong>Preference cookies:</strong> Remember your settings such as language, display preferences, and notification choices.</p>

          <h4>3. Managing Cookies</h4>
          <p>You can control and delete cookies through your browser settings. Note that disabling essential cookies may affect the functionality of VidSearch.</p>

          <h4>4. Third-Party Cookies</h4>
          <p>YouTube video embeds may set their own cookies. Please refer to Google&apos;s privacy policy for information about their cookie practices.</p>

          <h4>5. Contact</h4>
          <p>For questions about our cookie practices, contact us at privacy@vidsearch.com or through our <a href="#/contact">contact page</a>.</p>
        </div>
      </section>
    </div>
  )
}

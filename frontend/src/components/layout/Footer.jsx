import './Footer.css'

const COLUMNS = [
  {
    title: 'Product',
    links: [
      { label: 'Home', href: '#/' },
      { label: 'Browse Videos', href: '#/browse' },
      { label: 'Pricing', href: '#/pricing' },
      { label: 'How It Works', href: '#/how-it-works' },
    ],
  },
  {
    title: 'Resources',
    links: [
      { label: 'FAQ', href: '#/faq' },
      { label: 'About', href: '#/about' },
      { label: 'Contact', href: '#/contact' },
    ],
  },
  {
    title: 'Legal',
    links: [
      { label: 'Privacy Policy', href: '#/privacy' },
      { label: 'Terms of Service', href: '#/terms' },
      { label: 'Cookie Policy', href: '#/cookies' },
    ],
  },
]

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner container-lg">
        <div className="footer-grid">
          <div className="footer-brand">
            <div className="footer-logo">
              <div className="footer-logo-icon">&#9654;</div>
              <span>VideoSearch</span>
            </div>
            <p className="footer-tagline">AI-powered video learning platform. Understand any video instantly.</p>
            <div className="footer-social">
              <a href="#" className="footer-social-link" title="Twitter">&#120143;</a>
              <a href="#" className="footer-social-link" title="GitHub">&#9741;</a>
              <a href="#" className="footer-social-link" title="LinkedIn">in</a>
              <a href="#" className="footer-social-link" title="YouTube">&#9654;</a>
            </div>
          </div>
          {COLUMNS.map(col => (
            <div key={col.title} className="footer-col">
              <div className="footer-col-title">{col.title}</div>
              {col.links.map(l => (
                <a key={l.href} href={l.href} className="footer-link">{l.label}</a>
              ))}
            </div>
          ))}
        </div>
        <div className="footer-bottom">
          <span>&copy; 2026 VideoSearch. All rights reserved.</span>
          <span>Made with learning in mind.</span>
        </div>
      </div>
    </footer>
  )
}

import { FAQ_ITEMS } from '../../data/data'
import Accordion from '../../components/ui/Accordion'
import './FAQPage.css'

export default function FAQPage() {
  return (
    <div className="faq-page">
      <section className="faq-hero">
        <div className="container">
          <div className="section-header">
            <h1>Frequently Asked Questions</h1>
            <p>Everything you need to know about VidSearch.</p>
          </div>
        </div>
      </section>

      <section className="section faq-content">
        <div className="container" style={{ maxWidth: 720 }}>
          <Accordion items={FAQ_ITEMS} />
        </div>
      </section>

      <section className="section faq-contact">
        <div className="container" style={{ textAlign: 'center' }}>
          <h4>Still have questions?</h4>
          <p style={{ marginBottom: 20 }}>We are here to help. Reach out and we will get back to you.</p>
          <a href="#/contact" className="faq-contact-btn">Contact Us</a>
        </div>
      </section>
    </div>
  )
}

import { useState } from 'react'
import './ContactPage.css'

export default function ContactPage() {
  const [form, setForm] = useState({ name: '', email: '', subject: '', message: '' })
  const [sent, setSent] = useState(false)

  function handleChange(field) {
    return e => setForm(prev => ({ ...prev, [field]: e.target.value }))
  }

  function handleSubmit(e) {
    e.preventDefault()
    setSent(true)
  }

  return (
    <div className="contact-page">
      <section className="contact-hero">
        <div className="container">
          <div className="section-header">
            <h1>Contact Us</h1>
            <p>Have a question? We would love to hear from you.</p>
          </div>
        </div>
      </section>

      <section className="section contact-content">
        <div className="container">
          <div className="contact-layout">
            <div className="contact-form-wrapper">
              {sent ? (
                <div className="contact-success">
                  <div className="contact-success-icon">&#10003;</div>
                  <h3>Message Sent!</h3>
                  <p>Thank you for reaching out. We will get back to you within 24 hours.</p>
                  <button className="contact-btn" onClick={() => setSent(false)}>Send Another</button>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="contact-form">
                  <div className="contact-row">
                    <div className="contact-field">
                      <label>Name</label>
                      <input type="text" placeholder="Your name" value={form.name} onChange={handleChange('name')} required />
                    </div>
                    <div className="contact-field">
                      <label>Email</label>
                      <input type="email" placeholder="you@example.com" value={form.email} onChange={handleChange('email')} required />
                    </div>
                  </div>
                  <div className="contact-field">
                    <label>Subject</label>
                    <input type="text" placeholder="What is this about?" value={form.subject} onChange={handleChange('subject')} required />
                  </div>
                  <div className="contact-field">
                    <label>Message</label>
                    <textarea placeholder="Tell us more..." rows={6} value={form.message} onChange={handleChange('message')} required />
                  </div>
                  <button type="submit" className="contact-btn">Send Message</button>
                </form>
              )}
            </div>

            <div className="contact-info">
              <div className="contact-info-card">
                <h5>Get in Touch</h5>
                <div className="contact-info-item">
                  <span className="contact-info-icon">&#9993;</span>
                  <div>
                    <div className="contact-info-label">Email</div>
                    <div className="contact-info-value">support@videosearch.com</div>
                  </div>
                </div>
                <div className="contact-info-item">
                  <span className="contact-info-icon">&#128205;</span>
                  <div>
                    <div className="contact-info-label">Location</div>
                    <div className="contact-info-value">Vilnius, Lithuania</div>
                  </div>
                </div>
                <div className="contact-info-item">
                  <span className="contact-info-icon">&#128337;</span>
                  <div>
                    <div className="contact-info-label">Response Time</div>
                    <div className="contact-info-value">Within 24 hours</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

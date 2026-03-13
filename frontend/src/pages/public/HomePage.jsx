import { FEATURES, HOW_IT_WORKS_STEPS, TESTIMONIALS, ALL_VIDEOS } from '../../data/data'
import { useAuth } from '../../contexts/AuthContext'
import VideoCard from '../../components/ui/VideoCard'
import './HomePage.css'

export default function HomePage() {
  const { user } = useAuth()

  return (
    <div className="home">
      {/* ── Hero ── */}
      <section className="hero">
        <div className="hero-inner container">
          <div className="hero-content">
            <div className="hero-badge">AI-Powered Video Learning</div>
            <h1>Understand Any Video<br /><span className="hero-accent">Instantly.</span></h1>
            <p className="hero-subtitle">
              Paste a YouTube link. Ask questions. Get instant, AI-powered explanations
              with smart timestamps and context-aware answers.
            </p>
            <div className="hero-actions">
              {user ? (
                <a href="#/watch" className="btn-hero-primary">Open Workspace</a>
              ) : (
                <>
                  <a href="#/signup" className="btn-hero-primary">Get Started Free</a>
                  <a href="#/how-it-works" className="btn-hero-secondary">See How It Works</a>
                </>
              )}
            </div>
            <p className="hero-note">No credit card required. 5 free explanations per month.</p>
          </div>
          <div className="hero-visual">
            <div className="hero-mockup">
              <div className="mockup-header">
                <span className="mockup-dot" />
                <span className="mockup-dot" />
                <span className="mockup-dot" />
              </div>
              <div className="mockup-body">
                <div className="mockup-video">
                  <div className="mockup-play">&#9654;</div>
                </div>
                <div className="mockup-chat">
                  <div className="mockup-msg ai">Hi! Ask me anything about this video.</div>
                  <div className="mockup-msg user">What is a neural network?</div>
                  <div className="mockup-msg ai">A neural network is a system of interconnected layers...</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section className="section features-section">
        <div className="container">
          <div className="section-header">
            <h2>Everything You Need to Learn Faster</h2>
            <p>Powerful tools designed to make video-based learning efficient and engaging.</p>
          </div>
          <div className="features-grid">
            {FEATURES.map((f, i) => (
              <div className="feature-card" key={i}>
                <div className="feature-icon">{f.icon}</div>
                <h5>{f.title}</h5>
                <p>{f.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How It Works ── */}
      <section className="section how-section">
        <div className="container">
          <div className="section-header">
            <h2>How VidSearch Works</h2>
            <p>From paste to understanding in seconds.</p>
          </div>
          <div className="steps-grid">
            {HOW_IT_WORKS_STEPS.map(s => (
              <div className="step-card" key={s.step}>
                <div className="step-number">{s.step}</div>
                <h5>{s.title}</h5>
                <p>{s.description}</p>
              </div>
            ))}
          </div>
          <div style={{ textAlign: 'center', marginTop: 32 }}>
            <a href="#/how-it-works" className="btn-link">Learn more about how it works &#8594;</a>
          </div>
        </div>
      </section>

      {/* ── Video Preview ── */}
      <section className="section videos-preview-section">
        <div className="container">
          <div className="section-header">
            <h2>Explore Our Video Library</h2>
            <p>Start learning from hundreds of educational videos across multiple subjects.</p>
          </div>
          <div className="videos-preview-grid">
            {ALL_VIDEOS.slice(0, 6).map(v => (
              <VideoCard key={v.id} video={v} onClick={() => window.location.hash = `#/video/${v.id}`} />
            ))}
          </div>
          <div style={{ textAlign: 'center', marginTop: 32 }}>
            <a href="#/browse" className="btn-link">Browse all videos &#8594;</a>
          </div>
        </div>
      </section>

      {/* ── Testimonials ── */}
      <section className="section testimonials-section">
        <div className="container">
          <div className="section-header">
            <h2>Loved by Learners</h2>
            <p>See what our users have to say about VidSearch.</p>
          </div>
          <div className="testimonials-grid">
            {TESTIMONIALS.map((t, i) => (
              <div className="testimonial-card" key={i}>
                <div className="testimonial-quote">&ldquo;{t.quote}&rdquo;</div>
                <div className="testimonial-author">
                  <div className="testimonial-avatar">{t.avatar}</div>
                  <div>
                    <div className="testimonial-name">{t.name}</div>
                    <div className="testimonial-role">{t.role}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="section cta-section">
        <div className="container">
          <div className="cta-box">
            <h2>Start Learning Smarter Today</h2>
            <p>Join thousands of learners using AI to understand videos faster.</p>
            <div className="cta-actions">
              <a href="#/signup" className="btn-cta">Create Free Account</a>
              <a href="#/pricing" className="btn-cta-outline">View Pricing</a>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

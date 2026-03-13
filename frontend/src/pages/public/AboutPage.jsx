import './AboutPage.css'

const TEAM = [
  { name: 'Alex Chen', role: 'Founder & CEO', avatar: 'AC', bio: 'Former ML engineer passionate about making education accessible through AI.' },
  { name: 'Sarah Miller', role: 'Head of Product', avatar: 'SM', bio: 'EdTech veteran with 10 years of experience building learning platforms.' },
  { name: 'David Kim', role: 'Lead Engineer', avatar: 'DK', bio: 'Full-stack developer specializing in AI integrations and real-time systems.' },
  { name: 'Maria Garcia', role: 'Head of Design', avatar: 'MG', bio: 'UX designer focused on creating intuitive, accessible educational experiences.' },
]

const VALUES = [
  { title: 'Learning First', description: 'Every feature we build is designed to help people learn more effectively from video content.', icon: '\uD83C\uDF93' },
  { title: 'Accessible to All', description: 'We believe quality education tools should be available to everyone, everywhere.', icon: '\uD83C\uDF0D' },
  { title: 'Privacy Matters', description: 'Your data is yours. We never sell or share your personal information or learning history.', icon: '\uD83D\uDD12' },
  { title: 'Always Improving', description: 'We continuously refine our AI to provide better, more accurate explanations.', icon: '\uD83D\uDE80' },
]

export default function AboutPage() {
  return (
    <div className="about-page">
      <section className="about-hero">
        <div className="container">
          <div className="section-header">
            <h1>About VidSearch</h1>
            <p>Making video-based learning smarter, faster, and more interactive.</p>
          </div>
        </div>
      </section>

      <section className="section about-mission">
        <div className="container" style={{ maxWidth: 720, textAlign: 'center' }}>
          <h2>Our Mission</h2>
          <p className="about-mission-text">
            We are building the future of video-based education. VidSearch transforms passive
            video watching into active learning by letting you ask questions, get instant AI-powered
            explanations, and save key insights for later review.
          </p>
        </div>
      </section>

      <section className="section about-values">
        <div className="container">
          <div className="section-header">
            <h2>Our Values</h2>
          </div>
          <div className="about-values-grid">
            {VALUES.map((v, i) => (
              <div className="about-value-card" key={i}>
                <div className="about-value-icon">{v.icon}</div>
                <h5>{v.title}</h5>
                <p>{v.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section about-team">
        <div className="container">
          <div className="section-header">
            <h2>Meet the Team</h2>
            <p>The people behind VidSearch.</p>
          </div>
          <div className="about-team-grid">
            {TEAM.map((t, i) => (
              <div className="about-team-card" key={i}>
                <div className="about-team-avatar">{t.avatar}</div>
                <h5>{t.name}</h5>
                <div className="about-team-role">{t.role}</div>
                <p>{t.bio}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  )
}

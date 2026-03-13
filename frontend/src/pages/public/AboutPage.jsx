import './AboutPage.css'

const TEAM = [
  { name: 'Timofej Gaiworonskij', role: 'Founder & CEO', avatar: 'TG', bio: 'Speedcuber turned software engineer. Approaches every problem like a Rubik\'s cube — break it down, find the algorithm, solve it fast. Passionate about mathematics, pattern recognition, and building tools that make complex ideas click.' },
  { name: 'Adam Szablowski', role: 'Founder & CEO', avatar: 'AS', bio: 'Linux power user, weightlifter, and professional prompt engineer. Runs Arch btw. Combines deep technical knowledge with a passion for pushing AI to its limits — whether that\'s fine-tuning models or hitting a new PR at the gym.' },
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
            <h1>About VideoSearch</h1>
            <p>Making video-based learning smarter, faster, and more interactive.</p>
          </div>
        </div>
      </section>

      <section className="section about-mission">
        <div className="container" style={{ maxWidth: 720, textAlign: 'center' }}>
          <h2>Our Mission</h2>
          <p className="about-mission-text">
            We are building the future of video-based education. VideoSearch transforms passive
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
            <p>The people behind VideoSearch.</p>
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

import './VideoCard.css'

export default function VideoCard({ video, onClick, recommended }) {
  return (
    <div className={`vcard ${recommended ? 'vcard-recommended' : ''}`} onClick={onClick}>
      <div className={`vcard-thumb ${video.color}`}>
        <span className="vcard-icon">{video.icon}</span>
        <span className="vcard-duration">{video.duration}</span>
      </div>
      <div className="vcard-body">
        <div className="vcard-subject">{video.subject}</div>
        <div className="vcard-title">{video.title}</div>
      </div>
    </div>
  )
}

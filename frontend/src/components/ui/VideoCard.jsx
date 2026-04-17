import './VideoCard.css'

export default function VideoCard({ video, onClick, recommended, isFavourite, onToggleFavourite }) {
  return (
    <div className={`vcard ${recommended ? 'vcard-recommended' : ''}`} onClick={onClick}>
      <div className={`vcard-thumb ${video.color}`}>
        <span className="vcard-icon">{video.icon}</span>
        {video.duration?.trim() && (
          <span className="vcard-duration">{video.duration}</span>
        )}
        {onToggleFavourite && (
          <button
            className={`vcard-fav ${isFavourite ? 'vcard-fav-active' : ''}`}
            onClick={e => { e.stopPropagation(); onToggleFavourite(video.id) }}
            aria-label={isFavourite ? 'Remove from favourites' : 'Add to favourites'}
          >
            {isFavourite ? '♥' : '♡'}
          </button>
        )}
      </div>
      <div className="vcard-body">
        <div className="vcard-subject">{video.subject}</div>
        <div className="vcard-title">{video.title}</div>
      </div>
    </div>
  )
}

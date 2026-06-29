import { useEffect, useState } from "react";
import { animeImageUrl } from "../api";

// Each recommendation's source, shown as a card rather than a plain
// citation footnote — cover art (fetched live by mal_id, since the
// dataset itself doesn't store images), score, genres, and the
// retrieval relevance as a small mono "evidence" readout.

export default function AnimeCard({ source }) {
  const [image, setImage] = useState(null);
  const [imageFailed, setImageFailed] = useState(false);

  useEffect(() => {
    if (!source.mal_id) {
      setImageFailed(true);
      return;
    }
    let cancelled = false;
    animeImageUrl(source.mal_id)
      .then((data) => {
        if (cancelled) return;
        if (data.image_url) {
          setImage(data.image_url);
        } else {
          setImageFailed(true);
        }
      })
      .catch(() => {
        if (!cancelled) setImageFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, [source.mal_id]);

  return (
    <div className="anime-card">
      <div className="anime-card-art">
        {image && !imageFailed ? (
          <img
            src={image}
            alt={`${source.title} cover art`}
            onError={() => setImageFailed(true)}
          />
        ) : (
          <div className="anime-card-art-fallback" aria-hidden="true">
            <span>{source.title.slice(0, 1)}</span>
          </div>
        )}
      </div>

      <div className="anime-card-body">
        <h4 className="anime-card-title">{source.title}</h4>

        <div className="anime-card-meta">
          {source.score != null && (
            <span className="anime-card-score">★ {source.score.toFixed(1)}</span>
          )}
          {source.genres && (
            <span className="anime-card-genres">{source.genres}</span>
          )}
        </div>

        <div className="anime-card-evidence">
          relevance {Math.round(source.relevance * 100)}%
        </div>
      </div>
    </div>
  );
}

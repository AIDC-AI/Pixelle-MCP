'use client';

import { FileType } from "@/types/chat";
import { useEffect, useMemo, useRef, useState } from "react";
import MediaPauseIcon from "../icons/media-pause";
import MediaPlayIcon from "../icons/media-play";

interface IProps {
  url: string;
  type: FileType;
  lazy?: boolean;
  autoPlay?: boolean;
  preload?: 'none' | 'metadata' | 'auto';
  poster?: string;
  className?: string;
}

const Media: React.FC<IProps> = ({ url, type, lazy = true, autoPlay = false, preload, poster, className = '' }) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const ref = useRef<HTMLVideoElement | HTMLAudioElement | HTMLImageElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isVisible, setIsVisible] = useState(!lazy);

  const handlePlay = () => {
    if (ref && 'play' in (ref.current || {})) {
      // @ts-ignore
      ref.current?.play?.();
      setIsPlaying(true);
    }
  };

  const handlePause = () => {
    if (ref && 'pause' in (ref.current || {})) {
      // @ts-ignore
      ref.current?.pause?.();
      setIsPlaying(false);
    }
  };

  useEffect(() => {
    if (!lazy) return;
    const el = containerRef.current;
    if (!el) return;
    const io = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        const visible = entry.isIntersecting && entry.intersectionRatio > 0;
        setIsVisible(visible);
      },
      { root: null, rootMargin: '200px 0px', threshold: [0, 0.1, 0.25, 0.5, 1] }
    );
    io.observe(el);
    return () => {
      io.disconnect();
    };
  }, [lazy]);

  useEffect(() => {
    if (type !== FileType.VIDEO) return;
    if (!ref.current) return;
    if (!isVisible) {
      // Pause when leaving viewport
      // @ts-ignore
      ref.current?.pause?.();
      setIsPlaying(false);
    } else if (autoPlay) {
      // @ts-ignore
      ref.current?.play?.().catch(() => {});
      setIsPlaying(true);
    }
  }, [isVisible, autoPlay, type]);

  const content = useMemo(() => {
    switch(type) {
      case FileType.AUDIO:
        return isVisible
          ? <audio ref={ref as any} src={url} preload={preload || (lazy ? 'metadata' : 'auto')} className="w-full h-full" />
          : <div className="w-full h-full" />
      case FileType.VIDEO:
        return isVisible
          ? <video
              ref={ref as any}
              src={url}
              autoPlay={autoPlay}
              loop
              muted
              playsInline
              preload={preload || (lazy ? 'metadata' : 'auto')}
              poster={poster}
              className="w-full h-full object-cover"
            />
          : <div className="w-full h-full bg-black/30" />
      case FileType.IMAGE:
      default:
        return <img src={isVisible ? url : undefined as any} loading={lazy ? 'lazy' : undefined} alt="img" className="w-full h-full object-cover" />
    }
  }, [type, url, isVisible, autoPlay, preload, poster, lazy]);

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      {
        content
      } 
      {
        type === 'audio' && <div className="absolute inset-0 flex items-center justify-center z-10">
          {
            isPlaying ? <button
              onClick={handlePause}
              className="relative"
            >
              <MediaPauseIcon />
            </button>
            : <button
              onClick={handlePlay}
            >
              <MediaPlayIcon />
            </button>
          }
        </div>
      }
    </div>
  );
};

export default Media;
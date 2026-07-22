import { useState, useMemo } from "react";

interface Props {
  instrumentName: string;
  className?: string;
  width?: number;
  height?: number;
}

/**
 * Generates AI illustrations of instruments using Pollinations.ai
 * URL-based, no API key needed: https://image.pollinations.ai/prompt/...
 */
export default function AIInstrumentArt({ instrumentName, className = "", width = 512, height = 512 }: Props) {
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);

  const prompt = useMemo(() => {
    const clean = instrumentName
      .replace(/\(.*?\)/g, "")
      .replace(/3D-printed|3D printable/g, "3D-printable")
      .trim();
    return `Technical illustration of a ${clean}, detailed cross-section showing internal bore profile, professional engineering diagram style, dark background, highlighted acoustic chambers, clean lines, educational illustration, 4k`;
  }, [instrumentName]);

  const url = useMemo(() => {
    const encoded = encodeURIComponent(prompt);
    return `https://image.pollinations.ai/prompt/${encoded}?width=${width}&height=${height}&nologo=true&seed=${instrumentName.length * 7}`;
  }, [prompt, width, height, instrumentName]);

  if (error) {
    return (
      <div className={`bg-neutral-800/50 rounded-xl flex items-center justify-center ${className}`} style={{ width, height }}>
        <div className="text-center text-neutral-500">
          <div className="text-3xl mb-2">🎵</div>
          <div className="text-xs">Illustration unavailable</div>
        </div>
      </div>
    );
  }

  return (
    <div className={`relative overflow-hidden rounded-xl ${className}`}>
      {!loaded && (
        <div className="absolute inset-0 bg-neutral-800/50 animate-pulse flex items-center justify-center">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            <div className="text-xs text-neutral-500">Generating illustration...</div>
          </div>
        </div>
      )}
      <img
        src={url}
        alt={`${instrumentName} cross-section`}
        className={`w-full h-full object-cover transition-opacity duration-500 ${loaded ? "opacity-100" : "opacity-0"}`}
        onLoad={() => setLoaded(true)}
        onError={() => setError(true)}
      />
      {loaded && (
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-3">
          <div className="text-[10px] text-neutral-400">AI-generated illustration</div>
        </div>
      )}
    </div>
  );
}

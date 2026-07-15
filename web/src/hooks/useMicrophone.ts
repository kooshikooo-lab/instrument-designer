import { useCallback, useRef, useState } from "react";

export interface MicrophoneState {
  active: boolean;
  error: string | null;
  permissionDenied: boolean;
}

export function useMicrophone() {
  const audioCtxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [state, setState] = useState<MicrophoneState>({
    active: false,
    error: null,
    permissionDenied: false,
  });

  const start = useCallback(async () => {
    if (state.active) return;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: false,
          noiseSuppression: false,
          autoGainControl: false,
        },
      });

      const audioCtx = new AudioContext();
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 8192;
      analyser.smoothingTimeConstant = 0.8;

      const source = audioCtx.createMediaStreamSource(stream);
      source.connect(analyser);

      audioCtxRef.current = audioCtx;
      analyserRef.current = analyser;
      sourceRef.current = source;
      streamRef.current = stream;

      setState({ active: true, error: null, permissionDenied: false });
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      const denied = message.toLowerCase().includes("permission") || message.toLowerCase().includes("denied");
      setState({
        active: false,
        error: denied ? "Microphone permission denied" : message,
        permissionDenied: denied,
      });
    }
  }, [state.active]);

  const stop = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    sourceRef.current?.disconnect();
    audioCtxRef.current?.close();

    audioCtxRef.current = null;
    analyserRef.current = null;
    sourceRef.current = null;
    streamRef.current = null;

    setState({ active: false, error: null, permissionDenied: false });
  }, []);

  const getAnalyser = useCallback(() => analyserRef.current, []);

  const getAudioContext = useCallback(() => audioCtxRef.current, []);

  return { state, start, stop, getAnalyser, getAudioContext };
}

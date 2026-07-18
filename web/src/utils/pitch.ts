const NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];

export interface PitchResult {
  frequency: number;
  note: string;
  octave: number;
  cents: number;
  midi: number;
}

export function freqToNote(freq: number): PitchResult | null {
  if (freq <= 0 || !isFinite(freq)) return null;

  const A4 = 440.0;
  const semitones = 12 * Math.log2(freq / A4);
  const noteNum = Math.round(semitones) + 69;
  const noteName = NOTE_NAMES[((noteNum % 12) + 12) % 12];
  const octave = Math.floor(noteNum / 12) - 1;
  const cents = Math.round((semitones - Math.round(semitones)) * 100);

  return { frequency: freq, note: noteName, octave, cents, midi: noteNum };
}

export function detectPitch(
  analyser: AnalyserNode,
  sampleRate: number
): PitchResult | null {
  const bufferLength = analyser.frequencyBinCount;
  const timeData = new Float32Array(analyser.fftSize);
  analyser.getFloatTimeDomainData(timeData);

  let bestCorrelation = 0;
  let bestPeriod = -1;

  const minPeriod = Math.floor(sampleRate / 1000);
  const maxPeriod = Math.floor(sampleRate / 80);

  for (let period = minPeriod; period <= maxPeriod && period < timeData.length / 2; period++) {
    let correlation = 0;
    let count = 0;
    for (let i = 0; i < timeData.length - period; i++) {
      correlation += timeData[i] * timeData[i + period];
      count++;
    }
    correlation /= count;

    if (correlation > bestCorrelation) {
      bestCorrelation = correlation;
      bestPeriod = period;
    }
  }

  if (bestCorrelation < 0.01 || bestPeriod < 0) return null;

  return freqToNote(sampleRate / bestPeriod);
}

export function detectPitchHPS(
  frequencyData: Float32Array,
  sampleRate: number,
  fftSize: number
): PitchResult | null {
  const spectrum = new Float32Array(frequencyData.length);
  for (let i = 0; i < frequencyData.length; i++) {
    spectrum[i] = frequencyData[i];
  }

  const numHarmonics = 5;
  const hps = new Float32Array(spectrum);

  for (let n = 2; n <= numHarmonics; n++) {
    const downsampledLen = Math.floor(spectrum.length / n);
    for (let i = 0; i < downsampledLen; i++) {
      hps[i] *= spectrum[i * n];
    }
  }

  const minBin = Math.floor(80 * fftSize / sampleRate);
  let maxIdx = minBin;
  for (let i = minBin; i < hps.length; i++) {
    if (hps[i] > hps[maxIdx]) maxIdx = i;
  }

  const freq = (maxIdx * sampleRate) / fftSize;
  return freqToNote(freq);
}

export function getFrequencyBins(
  analyser: AnalyserNode,
  sampleRate: number
): { frequencies: number[]; magnitudes: number[] } {
  const bufferLength = analyser.frequencyBinCount;
  const dataArray = new Float32Array(bufferLength);
  analyser.getFloatFrequencyData(dataArray);

  const frequencies: number[] = [];
  const magnitudes: number[] = [];
  const binWidth = sampleRate / (analyser.fftSize);

  for (let i = 1; i < bufferLength; i++) {
    const freq = i * binWidth;
    if (freq > sampleRate / 2) break;
    frequencies.push(freq);
    magnitudes.push(dataArray[i]);
  }

  return { frequencies, magnitudes };
}

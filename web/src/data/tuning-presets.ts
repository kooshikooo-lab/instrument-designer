export interface TuningPreset {
  name: string;
  description: string;
  category: string;
  notes_per_octave: number;
  /** cents per step for equal temperaments, or null for non-equal */
  cents_per_step: number | null;
  /** frequency ratios from root for each note (just intonation / historical) */
  ratios: number[] | null;
  /** human-readable note labels */
  labels: string[];
}

function equalTemperament(name: string, category: string, n: number, description: string): TuningPreset {
  const cents = 1200 / n;
  const labels: string[] = [];
  for (let i = 0; i < n; i++) {
    labels.push(`${i}/${n}`);
  }
  return {
    name,
    description,
    category,
    notes_per_octave: n,
    cents_per_step: cents,
    ratios: null,
    labels,
  };
}

function justIntonation(name: string, category: string, ratios: number[], description: string): TuningPreset {
  const labels = ratios.map((r) => {
    const cents = 1200 * Math.log2(r);
    return `${cents.toFixed(0)}¢`;
  });
  return {
    name,
    description,
    category,
    notes_per_octave: ratios.length,
    cents_per_step: null,
    ratios,
    labels,
  };
}

export const TUNING_PRESETS: TuningPreset[] = [
  // Equal Temperaments
  equalTemperament("12-TET (Standard)", "Equal Temperament", 12,
    "Standard Western tuning. 100 cents per step. Used in virtually all modern instruments."),

  equalTemperament("19-TET", "Equal Temperament", 19,
    "19-tone equal temperament. ~63 cents per step. Near-pure major thirds. Popular in microtonal music."),

  equalTemperament("24-TET (Quarter-Tone)", "Equal Temperament", 24,
    "Quarter-tone tuning. 50 cents per step. Used in Middle Eastern maqam music."),

  equalTemperament("31-TET", "Equal Temperament", 31,
    "31-tone equal temperament. ~39 cents per step. Excellent meantone approximation. Historical keyboards."),

  equalTemperament("53-TET", "Equal Temperament", 53,
    "53-tone equal temperament. ~23 cents per step. Near-perfect just intonation for 5-limit intervals."),

  // Just Intonation
  justIntonation("5-Limit JI (Major)", "Just Intonation", [1, 16/15, 9/8, 6/5, 5/4, 4/3, 45/32, 3/2, 8/5, 5/3, 9/5, 15/8],
    "Pure harmonic ratios based on primes 2, 3, 5. Perfect thirds and fifths. Key-specific (shifts with modulation)."),

  justIntonation("7-Limit JI", "Just Intonation", [1, 8/7, 7/6, 5/4, 4/3, 7/5, 3/2, 8/5, 5/3, 7/4, 9/5, 15/8],
    "Adds 7th harmonic. Bluesy, warm character. 7/4 is a 'harmonic seventh' — flatter than equal-tempered minor 7th."),

  justIntonation("Pythagorean", "Historical", [1, 256/243, 9/8, 32/27, 81/64, 4/3, 729/512, 3/2, 128/81, 27/16, 16/9, 243/128],
    "Built from pure 3:2 fifths. Crisp fifths, but wide major thirds (~408 cents vs 400 in 12-TET). Medieval European tuning."),

  justIntonation("Meantone (1/4 Comma)", "Historical", [1, 16/15, 9/8, 6/5, 5/4, 4/3, 45/32, 3/2, 8/5, 5/3, 9/5, 15/8],
    "Historical compromise: pure thirds with slightly narrowed fifths. Sweet, consonant sound. 16th-17th century European."),

  justIntonation("Well Temperament (Werckmeister III)", "Historical",
    [1, 256/243, 9/8, 32/27, 5/4, 4/3, 45/32, 3/2, 128/81, 27/16, 16/9, 243/128],
    "Each key has a different character. Gently used for Bach's Well-Tempered Clavier. Practical historical compromise."),

  // Non-Western
  justIntonation("Maqam Rast (Arabic)", "Non-Western", [1, 9/8, 1.189, 4/3, 3/2, 5/3, 1.480, 2],
    "Middle Eastern maqam with neutral thirds (~355 cents). Quarter-tone intervals. Modal melodic system."),

  justIntonation("Slendro (Javanese)", "Non-Western", [1, 1.135, 1.265, 1.500, 1.770],
    "Indonesian 5-note equidistant scale. Not equal-tempered — each interval slightly different. Used in gamelan."),

  justIntonation("Pelog (Javanese)", "Non-Western", [1, 1.067, 1.217, 1.333, 1.500, 1.667, 1.900],
    "Indonesian 7-note unequal scale. Wide and narrow intervals create distinctive character. Used in gamelan."),

  // Experimental
  justIntonation("Bohlen-Pierce (Tritave)", "Experimental",
    [1, 27/25, 25/21, 9/7, 7/5, 5/3, 9/5, 15/7, 7/3, 5/2, 12/5, 7/3, 27/10],
    "Replaces octave (2:1) with tritave (3:1). 13 tones per tritave. Alien, otherworldly character. Bohlen, Pierce, Barbour."),

  justIntonation("Partch 43-Tone", "Experimental",
    [1, 81/80, 33/32, 21/20, 16/15, 12/11, 11/10, 10/9, 9/8, 8/7, 7/6, 6/5, 11/9, 5/4, 14/11, 9/7,
     21/16, 4/3, 27/20, 11/8, 7/5, 10/7, 16/11, 40/27, 3/2, 32/21, 14/9, 8/5, 11/7, 5/3, 12/7, 7/4,
     11/6, 15/8, 27/14, 16/9, 9/5, 20/11, 56/30, 28/15, 63/32],
    "Harry Partch's 43-tone just intonation scale. Pure harmonic ratios using primes 2,3,5,7,11. Unique, expressive, requires custom instruments."),

  justIntonation("Superflat (19-Harmonic)", "Experimental",
    Array.from({ length: 19 }, (_, i) => (i + 1) / (i === 0 ? 1 : i + 1)),
    "All 19 harmonics used as notes. Extremely dense tuning. Microtonal exploration. Experimental drone music."),
];

export const TUNING_CATEGORIES = [...new Set(TUNING_PRESETS.map((t) => t.category))];

/** Convert a tuning preset to frequency ratios relative to a base frequency */
export function tuningToRatios(preset: TuningPreset): number[] {
  if (preset.ratios) return preset.ratios;
  // For equal temperaments, compute from cents
  return Array.from({ length: preset.notes_per_octave }, (_, i) =>
    Math.pow(2, (i * (preset.cents_per_step ?? 100)) / 1200)
  );
}

/** Get frequency for a note in a tuning preset given a base frequency */
export function tuningNoteFrequency(preset: TuningPreset, noteIndex: number, baseFreq: number): number {
  const ratios = tuningToRatios(preset);
  const octave = Math.floor(noteIndex / ratios.length);
  const index = ((noteIndex % ratios.length) + ratios.length) % ratios.length;
  return baseFreq * ratios[index] * Math.pow(2, octave);
}

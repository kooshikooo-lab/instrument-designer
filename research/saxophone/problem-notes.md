# Known Problem Notes — Saxophone & Clarinet

Every woodwind instrument has inherent pitch tendencies that **cannot be fully eliminated** by design alone. The player must compensate. Understanding these is critical for setting realistic optimization targets.

## Saxophone Problem Notes

### Natural Intonation Spectrum (Andrew D Meyer)
The saxophone's pitch tendencies follow a predictable pattern:
1. **Bottom of horn** → sharp
2. **Middle short-tube notes** → flat
3. **Long-tube notes** → sharp
4. **Notes around concert A** → roughly in tune
5. **Upper register / palm keys** → extremely sharp

### Specific Problem Notes (Alto Saxophone)

| Register | Note | Tendency | Typical Deviation |
|---|---|---|---|
| Low | Bb, B | Sharp | +5 to +15c |
| Low | C# (open) | Flat | -10 to -20c |
| Middle | D, Eb, E | Sharp | +10 to +25c |
| Middle | F# | Flat | -5 to -15c |
| Middle | G | Flat | -5 to -10c |
| Upper | D, Eb, E, F (palm keys) | Sharp | +15 to +30c |

### Key Sources
- **Bullseye Intonation**: "There are some notes that will always be out of tune even with good embouchure"
- **Taming the Saxophone**: "Notes from D upwards will be sharp, with F# as exception; notes from C# downwards tend to be flat"
- **Larry Teal study (1943)**: Alto range -10c (low Eb) to +16c (high C#)
- **MusicMedic/SaxProShop**: "If notes get progressively sharper going up, may be a key height issue"

---

## Clarinet Problem Notes

### The Throat Tone Problem

The clarinet's most infamous intonation issue is the **throat tone register** (G4, G#4, A4, Bb4). These notes are consistently sharp.

**Why they're sharp:**
1. Shortened effective tube length — very few tone holes closed below the open hole
2. Missing acoustic resistance — normally closed holes below provide feedback that stabilizes pitch
3. The register key serves dual function — too small for Bb tone hole, too large for register vent

| Note | Average Deviation | Typical Range |
|---|---|---|
| G4 (open) | +8 cents | +3 to +15 cents |
| G#4 | +14 cents | +8 to +22 cents |
| A4 | +12 cents | +6 to +20 cents |
| Bb4 | +10 cents | +4 to +18 cents |

**For comparison:** Clarion register notes (B4 and above) average within ±5 cents — more than twice as accurate.

### Other Problem Areas

| Register | Notes | Tendency | Notes |
|---|---|---|---|
| Chalumeau low | E3, F3 | Flat | Requires firmer embouchure |
| Chalumeau | F#3 | Reference note | Often used for tuning |
| Throat tones | G4-Bb4 | Sharp (see above) | Worst on clarinet |
| Clarion | A5-E5 | Can be sharp | Especially A5 (same hole as throat A) |
| Altissimo | All notes | Variable | Sharp in experienced players, flat in beginners |

### The Register Key Compromise

The clarinet's register key serves **two conflicting functions**:
1. **Register vent** for clarion/altissimo (should be small and high)
2. **Tone hole** for written Bb5 / throat Bb (should be large and lower)

This compromise means:
- Throat Bb is stuffy and weak
- Some clarion notes become sharp and unstable
- The A3 → E5 → C#6 chain is consistently sharp across all three registers

### The Twelfth Problem

The clarinet overblows at the **twelfth** (not the octave), meaning:
- When you add the register key, the note jumps a 12th, not an octave
- This creates wider intervals that are harder to tune
- Adjusting one register affects the other in complex ways
- "A ten cent spread between the twelfths is very acceptable" (Clark Fobes)

---

## Implications for Optimization

### What's achievable:
- **±5 cents**: Excellent — professional quality (Lefebvre target)
- **±10 cents**: Good — acceptable for most players
- **±15 cents**: Acceptable — normal for student instruments
- **±20+ cents**: Problematic — needs mechanical or player compensation

### What's NOT achievable by design alone:
- Perfect intonation on every note (physically impossible)
- Eliminating all throat tone sharpness on clarinet
- Making palm key notes perfectly in tune on saxophone
- Perfect octave/12th matching across all registers

### What our optimization should target:
1. **Evenness** — minimize spread between notes (not necessarily hit 0 cents)
2. **Known problem notes** — accept that some notes will be inherently off
3. **Harmonicity** — ensure 2nd resonance is within ~10 cents of 2× fundamental (Lefebvre)
4. **Compensatable errors** — design so remaining errors can be fixed by player embouchure

### For our TMM model:
- The model's accuracy limit is ~10 cents (Lefebvre thesis)
- We should expect optimization to achieve **<10 cents evenness** as a good result
- Notes that are inherently problematic (throat tones, palm keys) may show larger deviations even in an optimized design

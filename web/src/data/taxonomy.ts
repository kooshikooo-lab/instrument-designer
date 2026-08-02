/**
 * Unified Acoustic Taxonomy for Instrument Designer
 * Based on Hornbostel-Sachs classification
 * 
 * This is the SINGLE SOURCE OF TRUTH for instrument categorization.
 * Both DEMAKEIN_PRESET_GROUPS and cadquery_export.py _meta must align with this.
 */

export interface TaxonomyNode {
  id: string;           // Unique identifier
  label: string;        // Human-readable label
  parentId?: string;    // Parent node ID (null for top-level)
  description?: string; // Optional description
  hsCode?: string;      // Hornbostel-Sachs code (optional)
}

// ============================================================================
// TOP-LEVEL FAMILIES (Level 1)
// ============================================================================

export const FAMILIES: TaxonomyNode[] = [
  { id: "flutes", label: "Flutes", description: "Edge-blown aerophones (duct, transverse, pan, vessel, end-blown, overtone)", hsCode: "421" },
  { id: "single-reed", label: "Single Reed", description: "Single reed aerophones (clarinets, saxophones, chalumeaux)", hsCode: "422.2" },
  { id: "double-reed", label: "Double Reed", description: "Double reed aerophones (oboes, bassoons, shawms)", hsCode: "422.1" },
  { id: "brass", label: "Brass", description: "Lip-vibrated aerophones (trumpets, horns, trombones, tubas, natural horns)", hsCode: "423" },
  { id: "drone", label: "Drone", description: "Drone aerophones (didgeridoo, drone flutes, alphorn)", hsCode: "424" },
  { id: "membrane", label: "Membrane", description: "Membrane aerophones (kazoo, mirlitons, membrane reeds)", hsCode: "425" },
  { id: "hybrid", label: "Hybrid & Experimental", description: "Hybrid instruments, slide/glissando mechanisms, experimental designs" },
  { id: "parts", label: "Parts & Accessories", description: "Mouthpieces, bocals, extensions, tools, reeds" },
];

// ============================================================================
// SUBFAMILIES (Level 2) - grouped by parent family
// ============================================================================

export const SUBFAMILIES: TaxonomyNode[] = [
  // Flutes
  { id: "fipple-flute", label: "Fipple / Duct Flutes", parentId: "flutes", description: "Whistles, recorders, tabor pipes, penny whistles", hsCode: "421.221" },
  { id: "transverse-flute", label: "Transverse Flutes", parentId: "flutes", description: "Concert flutes, piccolos, baroque traversos, fifes", hsCode: "421.121" },
  { id: "pan-flute", label: "Pan Flutes", parentId: "flutes", description: "Panpipes, syrinx, multi-pipe duct flutes", hsCode: "421.112" },
  { id: "vessel-flute", label: "Vessel Flutes", parentId: "flutes", description: "Ocarinas, xuns, globular flutes", hsCode: "421.131" },
  { id: "end-blown-flute", label: "End-Blown Flutes", parentId: "flutes", description: "Shakuhachi, quena, kaval, ney", hsCode: "421.111" },
  { id: "overtone-flute", label: "Overtone Flutes", parentId: "flutes", description: "Fujara, koncovka, tilinca, seljefløyte, willow flutes", hsCode: "421.111.2" },
  { id: "recorder", label: "Recorders", parentId: "flutes", description: "Soprano through bass recorders, historical fingerings", hsCode: "421.221.1" },
  { id: "whistle", label: "Whistles / Pennywhistles", parentId: "flutes", description: "Tin whistles, low whistles, folk whistles", hsCode: "421.221.2" },
  { id: "folk-flute", label: "Folk Flutes", parentId: "flutes", description: "Simple 6-hole folk flutes, keyless designs" },
  { id: "nordic-folk-flute", label: "Nordic Folk Flutes", parentId: "flutes", description: "Seljefløyte, Willow flutes, Nordic traditions" },
  { id: "historical-flute", label: "Historical Flutes", parentId: "flutes", description: "Baroque traversos, classical flutes, renaissance flutes" },

  // Single Reed
  { id: "clarinet", label: "Clarinets", parentId: "single-reed", description: "Bb, A, Eb, bass, contra-alto, contra-bass, octocontra clarinets" },
  { id: "saxophone", label: "Saxophones", parentId: "single-reed", description: "Soprano through bass saxophones, C-melody, straight" },
  { id: "chalumeau", label: "Chalumeaux", parentId: "single-reed", description: "Historical single-reed instruments, diatonic/chromatic" },
  { id: "pocket-sax", label: "Pocket Sax / Xaphoon", parentId: "single-reed", description: "Compact single-reed instruments (xaphoon, pocket sax, minsax)" },
  { id: "single-reed-experimental", label: "Experimental Single Reed", parentId: "single-reed", description: "Glissotar, tarogato, slide sax, hybrid single-reed designs" },

  // Double Reed
  { id: "oboe", label: "Oboes", parentId: "double-reed", description: "Modern conservatory, baroque, classical, English horn" },
  { id: "bassoon", label: "Bassoons", parentId: "double-reed", description: "Heckel, French, contrabassoon, dulcian" },
  { id: "shawm", label: "Shawms", parentId: "double-reed", description: "Medieval/renaissance shawms, folk shawms, dulzaina" },
  { id: "folk-double-reed", label: "Folk Double Reeds", parentId: "double-reed", description: "Regional folk double reeds (zurna, suona, hichiriki)" },
  { id: "historical-double-reed", label: "Historical Double Reeds", parentId: "double-reed", description: "Dulcian, curtal, baroque oboe, baroque bassoon" },

  // Brass
  { id: "trumpet", label: "Trumpets", parentId: "brass", description: "Bb, C, Eb, D, piccolo trumpets, cornets, flugelhorns" },
  { id: "horn", label: "Horns", parentId: "brass", description: "French horn, double horn, Vienna horn, natural horn" },
  { id: "trombone", label: "Trombones", parentId: "brass", description: "Tenor, bass, alto, contrabass trombones, sackbuts" },
  { id: "tuba", label: "Tubas", parentId: "brass", description: "BBb, CC, Eb, F tubas, sousaphones, helicons" },
  { id: "natural-horn", label: "Natural Horns / Lip-Vibrated", parentId: "brass", description: "Alphorn, cornett, serpent, ophicleide, shofar, lur" },

  // Drone
  { id: "drone-flute", label: "Drone Flutes", parentId: "drone", description: "Multi-pipe flutes with dedicated drone pipes" },
  { id: "didgeridoo", label: "Didgeridoo / Yidaki", parentId: "drone", description: "Traditional and modern didgeridoos" },
  { id: "drone-reed", label: "Reed Drones", parentId: "drone", description: "Continuous reed drones, bagpipe drones" },

  // Membrane
  { id: "kazoo", label: "Kazoo / Mirliton", parentId: "membrane", description: "Classic kazoo, membrane aerophones" },
  { id: "membrane-reed", label: "Membrane Reeds", parentId: "membrane", description: "Membrane clarinets, diplica, sipsi, zummara, duduk" },

  // Hybrid & Experimental
  { id: "slide-mechanism", label: "Slide / Glissando Mechanisms", parentId: "hybrid", description: "Glissotar, slide sax, tromboon, trombone-slide hybrids" },
  { id: "tarogato", label: "Tarogato / Hybrid Reeds", parentId: "hybrid", description: "Hungarian tarogato, single-reed conical bore hybrids" },
  { id: "glissando-reed", label: "Glissando Reeds", parentId: "hybrid", description: "Continuous pitch control via sliding mechanisms" },
  { id: "experimental", label: "Experimental / Novel", parentId: "hybrid", description: "Atomica, membrane clarinets, novel acoustic designs" },

  // Parts & Accessories
  { id: "mouthpiece", label: "Mouthpieces", parentId: "parts", description: "Clarinet, saxophone, trumpet, trombone, horn, tuba mouthpieces" },
  { id: "bocal", label: "Bocals / Crooks", parentId: "parts", description: "Bassoon, contrabassoon, sax bocals and crooks" },
  { id: "extension", label: "Extensions", parentId: "parts", description: "Low A extensions, low C extensions, barrel extensions" },
  { id: "tool", label: "Tools", parentId: "parts", description: "Mouthpiece pullers, reed tools, adjustment tools" },
  { id: "reed", label: "Reeds", parentId: "parts", description: "Cane reeds, synthetic reeds, membrane reeds" },
];

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

export function getFamily(id: string): TaxonomyNode | undefined {
  return FAMILIES.find(f => f.id === id);
}

export function getSubfamily(id: string): TaxonomyNode | undefined {
  return SUBFAMILIES.find(s => s.id === id);
}

export function getSubfamiliesForFamily(familyId: string): TaxonomyNode[] {
  return SUBFAMILIES.filter(s => s.parentId === familyId);
}

export function getFullPath(subfamilyId: string): { family: TaxonomyNode; subfamily: TaxonomyNode } | null {
  const subfamily = getSubfamily(subfamilyId);
  if (!subfamily || !subfamily.parentId) return null;
  const family = getFamily(subfamily.parentId);
  if (!family) return null;
  return { family, subfamily };
}

export function getDisplayLabel(subfamilyId: string): string {
  const path = getFullPath(subfamilyId);
  if (!path) return subfamilyId;
  return `${path.family.label} \u2013 ${path.subfamily.label}`;
}

export function getAllSubfamilyIds(): string[] {
  return SUBFAMILIES.map(s => s.id);
}

// ============================================================================
// MAPPING: Legacy DEMAKEIN preset keys -> Subfamily IDs
// ============================================================================

export const DEMAKEIN_PRESET_TO_SUBFAMILY: Record<string, string> = {
  // Flutes
  "folk_whistle": "whistle",
  "folk_flute": "folk-flute",
  "recorder": "recorder",
  "dorian_whistle": "whistle",
  "three_hole_whistle": "fipple-flute",
  "pflute": "pan-flute",
  
  // Single Reed
  "reedpipe": "chalumeau",
  "chalumier_clarinet": "clarinet",
  "chalumier_bass_clarinet": "clarinet",
  "baroque_clarinet": "clarinet",
  "soprano_sax": "saxophone",
  "alto_sax": "saxophone",
  "tenor_sax": "saxophone",
  "baritone_sax": "saxophone",
  
  // Double Reed
  "folk_shawm": "shawm",
  "shawm": "shawm",
  "lohner_oboe": "oboe",
  "modern_oboe": "oboe",
  "baroque_oboe": "historical-double-reed",
  
  // Drone
  "reed_drone": "drone-reed",
  
  // Brass
  "trumpet_bb": "trumpet",
  "trombone": "trombone",
  "french_horn": "horn",
  "tuba": "tuba",
  
  // Parts & Accessories
  "clarinet_mouthpiece": "mouthpiece",
  "bass_clarinet_mouthpiece": "mouthpiece",
  "alto_sax_mouthpiece": "mouthpiece",
  "tenor_sax_mouthpiece": "mouthpiece",
  "trumpet_mouthpiece": "mouthpiece",
};
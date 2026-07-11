import type { Instrument } from "../data/instruments";

export interface Filters {
  subcategory: string;
  typeLabel: string;
  difficulty: string;
  tag: string;
  search: string;
}

export const EMPTY_FILTERS: Filters = {
  subcategory: "",
  typeLabel: "",
  difficulty: "",
  tag: "",
  search: "",
};

export function filterInstruments(instruments: Instrument[], filters: Filters): Instrument[] {
  return instruments.filter((i) => {
    if (filters.subcategory && i.subcategory !== filters.subcategory) return false;
    if (filters.typeLabel && i.type_label !== filters.typeLabel) return false;
    if (filters.difficulty && i.difficulty !== filters.difficulty) return false;
    if (filters.tag && !i.tags.includes(filters.tag)) return false;
    if (filters.search) {
      const q = filters.search.toLowerCase();
      const haystack = `${i.name} ${i.description} ${i.tags.join(" ")} ${i.type_label} ${i.key}`.toLowerCase();
      if (!haystack.includes(q)) return false;
    }
    return true;
  });
}

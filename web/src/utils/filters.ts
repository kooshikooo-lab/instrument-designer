import type { Instrument } from "../data/instruments";

interface FilterState {
  search: string;
  subcategory: string;
  typeLabel: string;
  difficulty: string;
  tags: string[];
}

export function filterInstruments(
  instruments: Instrument[],
  filters: FilterState
): Instrument[] {
  return instruments.filter((inst) => {
    if (
      filters.search &&
      !inst.name.toLowerCase().includes(filters.search.toLowerCase()) &&
      !inst.description.toLowerCase().includes(filters.search.toLowerCase()) &&
      !inst.family.toLowerCase().includes(filters.search.toLowerCase())
    )
      return false;

    if (filters.subcategory && inst.subcategory !== filters.subcategory)
      return false;

    if (filters.typeLabel && inst.type_label !== filters.typeLabel)
      return false;

    if (filters.difficulty && inst.difficulty !== filters.difficulty)
      return false;

    if (
      filters.tags.length > 0 &&
      !filters.tags.some((t) => inst.tags.includes(t))
    )
      return false;

    return true;
  });
}

export interface SearchResult {
  id: string;
  collection: string;
  volume: number;
  part_no: number;
  page_no_start: number;
  page_no_end: number;
  section_title: string;
  content: string;
  similarity: number;
}

export interface SearchRequest {
  query: string;
  limit?: number;
  collection?: string;
}

export const COLLECTION_LABELS: Record<string, string> = {
  ibn_bazz: "Majmoo' al-Fatawa (Ibn Bazz)",
  iftaa: "Permanent Committee (Iftaa)",
  noor_ala_darb: "Noor ala al-Darb",
};

export const COLLECTION_COLORS: Record<string, string> = {
  ibn_bazz: "bg-emerald-100 text-emerald-800",
  iftaa: "bg-blue-100 text-blue-800",
  noor_ala_darb: "bg-amber-100 text-amber-800",
};

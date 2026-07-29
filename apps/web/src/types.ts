export type User = {
  id: string;
  email: string;
  name: string;
};

export type AgeBand = "2-5" | "5-9" | "6-9" | "9-12";

export type StorySummary = {
  id: string;
  title: string;
  gender: "boy" | "girl" | "unisex";
  age_range: string;
  age_bands: AgeBand[];
  theme: string;
  page_count: number;
};

export type Book = {
  id: string;
  child_name: string;
  child_age: number;
  child_gender: string;
  story_id: string | null;
  age_band: AgeBand | null;
  suggested_age_band: AgeBand | null;
  status: string;
  progress: number;
  progress_message: string;
  error_message: string | null;
  created_at: string;
  has_photo: boolean;
  pdf_url: string | null;
  page_urls: string[];
};

export type Job = {
  id: string;
  book_id: string;
  status: string;
  error_message: string | null;
};

export const AGE_BANDS: AgeBand[] = ["2-5", "5-9", "6-9", "9-12"];

/** Espelha a regra do backend: faixa mais especifica que contem a idade. */
export function suggestAgeBand(age: number): AgeBand {
  const clamped = Math.max(1, Math.min(12, age));
  const parsed = AGE_BANDS.map((band) => {
    const [lo, hi] = band.split("-").map(Number);
    return { band, lo, hi };
  });
  const matching = parsed.filter((b) => b.lo <= clamped && clamped <= b.hi);
  if (!matching.length) return clamped < 2 ? "2-5" : "9-12";
  matching.sort(
    (a, b) => a.hi - a.lo - (b.hi - b.lo) || Math.abs((a.lo + a.hi) / 2 - clamped) - Math.abs((b.lo + b.hi) / 2 - clamped),
  );
  return matching[0].band;
}

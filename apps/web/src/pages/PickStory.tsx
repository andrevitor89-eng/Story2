import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import type { AgeBand, Book, StorySummary } from "../types";
import { AGE_BANDS, suggestAgeBand } from "../types";

const GENDER_LABEL: Record<string, string> = {
  boy: "Menino",
  girl: "Menina",
  unisex: "Unissex",
};

export function PickStory() {
  const { bookId } = useParams();
  const navigate = useNavigate();
  const [book, setBook] = useState<Book | null>(null);
  const [stories, setStories] = useState<StorySummary[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [ageMode, setAgeMode] = useState<"auto" | "manual">("auto");
  const [ageBand, setAgeBand] = useState<AgeBand>("5-9");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const suggested = useMemo(() => {
    if (!book) return "5-9" as AgeBand;
    return book.suggested_age_band || suggestAgeBand(book.child_age);
  }, [book]);

  useEffect(() => {
    if (!bookId) return;
    api
      .getBook(bookId)
      .then(async (b) => {
        setBook(b);
        const auto = b.suggested_age_band || suggestAgeBand(b.child_age);
        setAgeBand(auto);
        const list = await api.stories(b.child_gender === "unisex" ? undefined : b.child_gender);
        setStories(list);
      })
      .catch((err) => setError(err.message));
  }, [bookId]);

  useEffect(() => {
    if (ageMode === "auto") setAgeBand(suggested);
  }, [ageMode, suggested]);

  async function generate() {
    if (!bookId || !selected) return;
    setBusy(true);
    setError("");
    try {
      await api.generate(bookId, selected, {
        age_band: ageBand,
        age_band_mode: ageMode,
      });
      navigate(`/app/books/${bookId}/status`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao gerar");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="panel">
      <Link to="/app/new" className="muted">
        Voltar
      </Link>
      <h1>Escolha a historia</h1>
      {book && (
        <p className="muted">
          Para <strong>{book.child_name}</strong> ({book.child_age} anos) — historias compativeis com o
          perfil.
        </p>
      )}

      <div className="age-band-box">
        <h2>Faixa etaria do texto</h2>
        <p className="muted">
          Cada historia tem 4 versoes de texto. Use a sugestao automatica pela idade ou escolha
          manualmente.
        </p>
        <div className="age-mode-row">
          <label className={`age-mode ${ageMode === "auto" ? "on" : ""}`}>
            <input
              type="radio"
              name="ageMode"
              checked={ageMode === "auto"}
              onChange={() => setAgeMode("auto")}
            />
            Automatica (sugerida: {suggested} anos)
          </label>
          <label className={`age-mode ${ageMode === "manual" ? "on" : ""}`}>
            <input
              type="radio"
              name="ageMode"
              checked={ageMode === "manual"}
              onChange={() => setAgeMode("manual")}
            />
            Manual
          </label>
        </div>
        <div className="age-band-row">
          {AGE_BANDS.map((band) => (
            <button
              key={band}
              type="button"
              className={`age-chip ${ageBand === band ? "selected" : ""}`}
              disabled={ageMode === "auto"}
              onClick={() => {
                setAgeMode("manual");
                setAgeBand(band);
              }}
            >
              {band}
              {band === suggested ? " · sugerida" : ""}
            </button>
          ))}
        </div>
      </div>

      <div className="story-grid">
        {stories.map((s) => (
          <button
            key={s.id}
            type="button"
            className={`story-card ${selected === s.id ? "selected" : ""}`}
            onClick={() => setSelected(s.id)}
          >
            <h3>{s.title.replace("{NOME}", book?.child_name || "...")}</h3>
            <p>{s.theme}</p>
            <div className="meta">
              <span>{GENDER_LABEL[s.gender] || s.gender}</span>
              <span>texto {ageBand} anos</span>
              <span>{s.page_count} paginas</span>
            </div>
          </button>
        ))}
      </div>
      {error && <p className="error">{error}</p>}
      <div className="row" style={{ marginTop: "1.5rem" }}>
        <button className="btn btn-coral" disabled={!selected || busy} type="button" onClick={generate}>
          {busy ? "Iniciando..." : "Gerar ebook"}
        </button>
      </div>
    </div>
  );
}

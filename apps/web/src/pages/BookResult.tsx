import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, getToken } from "../api";
import type { Book, UserVoice } from "../types";

function withToken(path: string | null | undefined): string | null {
  if (!path) return null;
  const token = getToken();
  if (!token) return path;
  const sep = path.includes("?") ? "&" : "?";
  return `${path}${sep}token=${encodeURIComponent(token)}`;
}

export function BookResult() {
  const { bookId } = useParams();
  const [book, setBook] = useState<Book | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState<"animation" | "narrated" | null>(null);
  const [voices, setVoices] = useState<UserVoice[]>([]);
  const [customVoiceAvailable, setCustomVoiceAvailable] = useState(false);
  const [selectedVoiceId, setSelectedVoiceId] = useState<string>("");
  const [voiceName, setVoiceName] = useState("Minha voz");
  const [voiceUploading, setVoiceUploading] = useState(false);

  async function refresh() {
    if (!bookId) return;
    const next = await api.getBook(bookId);
    setBook(next);
    return next;
  }

  async function refreshVoices() {
    try {
      const data = await api.listVoices();
      setVoices(data.items);
      setCustomVoiceAvailable(data.custom_voice_available);
      setSelectedVoiceId((prev) => {
        if (prev && data.items.some((v) => v.id === prev)) return prev;
        const def = data.items.find((v) => v.is_default);
        return def?.id || data.items[0]?.id || "";
      });
    } catch {
      /* ignore */
    }
  }

  useEffect(() => {
    if (!bookId) return;
    refresh().catch((err) => setError(err.message));
    refreshVoices();
  }, [bookId]);

  useEffect(() => {
    if (!busy || !bookId) return;
    const id = window.setInterval(() => {
      refresh()
        .then((b) => {
          if (!b) return;
          if (busy === "animation" && b.video_url) setBusy(null);
          if (busy === "narrated" && b.narrated_video_url) setBusy(null);
          if (b.error_message && (b.progress_message || "").toLowerCase().includes("falha")) {
            setError(b.error_message);
            setBusy(null);
          }
        })
        .catch((err) => {
          setError(err.message);
          setBusy(null);
        });
    }, 2500);
    return () => window.clearInterval(id);
  }, [busy, bookId]);

  async function startAnimation() {
    if (!bookId) return;
    setError("");
    setBusy("animation");
    try {
      await api.generateVideo(bookId);
      await refresh();
    } catch (err) {
      setBusy(null);
      setError(err instanceof Error ? err.message : "Falha ao iniciar animacao");
    }
  }

  async function startNarrated() {
    if (!bookId) return;
    setError("");
    setBusy("narrated");
    try {
      await api.generateNarratedVideo(bookId, {
        voice_id: selectedVoiceId || null,
      });
      await refresh();
    } catch (err) {
      setBusy(null);
      setError(err instanceof Error ? err.message : "Falha ao iniciar video narrado");
    }
  }

  async function onVoiceFile(file: File | null) {
    if (!file) return;
    setVoiceUploading(true);
    setError("");
    try {
      const voice = await api.uploadVoice(file, voiceName.trim() || "Minha voz", voices.length === 0);
      await refreshVoices();
      setSelectedVoiceId(voice.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao clonar voz");
    } finally {
      setVoiceUploading(false);
    }
  }

  async function removeVoice(id: string) {
    setError("");
    try {
      await api.deleteVoice(id);
      await refreshVoices();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao remover voz");
    }
  }

  const videoSrc = withToken(book?.video_url);
  const narratedSrc = withToken(book?.narrated_video_url);

  return (
    <div className="panel">
      <Link to="/app" className="muted">
        Meus livros
      </Link>
      <h1>{book ? `Livro de ${book.child_name}` : "Seu ebook"}</h1>
      <p className="muted">Preview das paginas, download do PDF e videos.</p>
      {error && <p className="error">{error}</p>}
      {busy && <p className="muted">{book?.progress_message || "Gerando..."}</p>}
      {book && (
        <>
          <div className="page-gallery">
            {book.page_urls.map((url, i) => (
              <img key={url} src={withToken(url) || url} alt={`Pagina ${i + 1}`} loading="lazy" />
            ))}
          </div>

          <div className="result-block" style={{ marginTop: 20 }}>
            <h3>Voz da narração</h3>
            {!customVoiceAvailable ? (
              <p className="muted">
                Voz personalizada indisponível neste servidor (ElevenLabs não configurado). O vídeo
                usará a narração padrão.
              </p>
            ) : (
              <>
                <p className="muted" style={{ marginBottom: 10 }}>
                  Envie 30–60s de fala clara (MP3, WAV ou M4A), sem música de fundo. Fale naturalmente,
                  como se estivesse contando uma história. A voz fica salva na sua conta.
                </p>
                <div className="row" style={{ flexWrap: "wrap", gap: 8, marginBottom: 10 }}>
                  <input
                    type="text"
                    value={voiceName}
                    onChange={(e) => setVoiceName(e.target.value)}
                    placeholder="Nome da voz"
                    style={{ minWidth: 160 }}
                  />
                  <label className="btn btn-ghost" style={{ cursor: voiceUploading ? "wait" : "pointer" }}>
                    {voiceUploading ? "Clonando..." : "Enviar áudio"}
                    <input
                      type="file"
                      accept="audio/mpeg,audio/wav,audio/mp4,audio/x-m4a,audio/webm,audio/ogg,.mp3,.wav,.m4a,.webm,.ogg"
                      hidden
                      disabled={voiceUploading || !!busy}
                      onChange={(e) => onVoiceFile(e.target.files?.[0] || null)}
                    />
                  </label>
                </div>
                {voices.length > 0 && (
                  <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                    <label className="muted" htmlFor="voice-select">
                      Usar nesta narração
                    </label>
                    <div className="row" style={{ flexWrap: "wrap", gap: 8 }}>
                      <select
                        id="voice-select"
                        value={selectedVoiceId}
                        onChange={(e) => setSelectedVoiceId(e.target.value)}
                        disabled={!!busy}
                      >
                        <option value="">Automática (padrão da conta ou sistema)</option>
                        {voices.map((v) => (
                          <option key={v.id} value={v.id}>
                            {v.name}
                            {v.is_default ? " (padrão)" : ""}
                          </option>
                        ))}
                      </select>
                      {selectedVoiceId && (
                        <button
                          className="btn btn-ghost"
                          type="button"
                          disabled={!!busy}
                          onClick={() => removeVoice(selectedVoiceId)}
                        >
                          Remover voz
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          <div className="row">
            {book.pdf_url && (
              <a className="btn btn-coral" href={withToken(book.pdf_url) || book.pdf_url} target="_blank" rel="noreferrer">
                Baixar PDF
              </a>
            )}
            <button className="btn btn-ghost" type="button" disabled={!!busy} onClick={startAnimation}>
              {busy === "animation" ? "Gerando animacao..." : "Gerar animacao"}
            </button>
            <button className="btn btn-ghost" type="button" disabled={!!busy} onClick={startNarrated}>
              {busy === "narrated" ? "Gerando video narrado..." : "Gerar video narrado"}
            </button>
            <Link className="btn btn-ghost" to="/app/new">
              Criar outro
            </Link>
          </div>

          {videoSrc && (
            <div className="result-block" style={{ marginTop: 24 }}>
              <h3>Animacao</h3>
              {book.video_mime === "image/gif" ? (
                <img src={videoSrc} alt="Animacao" style={{ maxWidth: 420, width: "100%", borderRadius: 12 }} />
              ) : (
                <video src={videoSrc} controls style={{ maxWidth: 420, width: "100%" }} />
              )}
            </div>
          )}

          {narratedSrc && (
            <div className="result-block" style={{ marginTop: 24 }}>
              <h3>Video narrado</h3>
              <video src={narratedSrc} controls style={{ maxWidth: 420, width: "100%" }} />
            </div>
          )}
        </>
      )}
    </div>
  );
}

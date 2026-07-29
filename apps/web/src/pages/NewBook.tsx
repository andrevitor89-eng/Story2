import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";

export function NewBook() {
  const navigate = useNavigate();
  const [childName, setChildName] = useState("");
  const [childAge, setChildAge] = useState(5);
  const [childGender, setChildGender] = useState<"boy" | "girl" | "unisex">("unisex");
  const [photo, setPhoto] = useState<File | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!photo) {
      setError("Envie uma foto da crianca");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const book = await api.createBook({
        child_name: childName,
        child_age: childAge,
        child_gender: childGender,
      });
      await api.uploadPhoto(book.id, photo);
      navigate(`/app/books/${book.id}/story`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao criar livro");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="panel">
      <Link to="/app" className="muted">
        Voltar
      </Link>
      <h1>Dados da crianca</h1>
      <p className="muted">Vamos personalizar a historia com o nome e a foto.</p>
      <form className="form-grid" onSubmit={onSubmit}>
        <label>
          Nome
          <input
            value={childName}
            onChange={(e) => setChildName(e.target.value)}
            required
            maxLength={80}
          />
        </label>
        <label>
          Idade
          <input
            type="number"
            min={1}
            max={12}
            value={childAge}
            onChange={(e) => setChildAge(Number(e.target.value))}
            required
          />
          <span className="muted" style={{ fontWeight: 500, fontSize: "0.85rem" }}>
            Na proxima etapa voce escolhe a faixa do texto (automatica ou manual: 2-5, 5-9, 6-9, 9-12).
          </span>
        </label>
        <label>
          Genero (para filtrar historias)
          <select
            value={childGender}
            onChange={(e) => setChildGender(e.target.value as "boy" | "girl" | "unisex")}
          >
            <option value="boy">Menino</option>
            <option value="girl">Menina</option>
            <option value="unisex">Tanto faz</option>
          </select>
        </label>
        <label>
          Foto
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={(e) => setPhoto(e.target.files?.[0] || null)}
            required
          />
        </label>
        {error && <p className="error">{error}</p>}
        <button className="btn btn-primary" disabled={busy} type="submit">
          {busy ? "Salvando..." : "Escolher historia"}
        </button>
      </form>
    </div>
  );
}
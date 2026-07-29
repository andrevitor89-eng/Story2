import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import type { Book } from "../types";

const STATUS_LABEL: Record<string, string> = {
  draft: "Rascunho",
  queued: "Na fila",
  generating: "Gerando",
  ready: "Pronto",
  failed: "Falhou",
};

export function Library() {
  const { user, logout } = useAuth();
  const [books, setBooks] = useState<Book[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .listBooks()
      .then(setBooks)
      .catch((err) => setError(err.message));
  }, []);

  return (
    <>
      <nav className="site-nav">
        <Link to="/" className="brand">
          Story R Us
        </Link>
        <div className="nav-actions">
          <span className="muted">{user?.email}</span>
          <button className="btn btn-ghost" type="button" onClick={logout}>
            Sair
          </button>
        </div>
      </nav>
      <div className="panel">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <h1 style={{ margin: 0 }}>Meus livros</h1>
          <Link className="btn btn-primary" to="/app/new">
            Novo livro
          </Link>
        </div>
        {error && <p className="error">{error}</p>}
        {books.length === 0 && <p className="muted">Nenhum livro ainda. Crie o primeiro!</p>}
        <div className="story-grid" style={{ marginTop: "1.5rem" }}>
          {books.map((b) => {
            const href =
              b.status === "ready"
                ? `/app/books/${b.id}/result`
                : b.status === "generating" || b.status === "queued"
                  ? `/app/books/${b.id}/status`
                  : b.has_photo
                    ? `/app/books/${b.id}/story`
                    : `/app/new`;
            return (
              <Link key={b.id} to={href} className="story-card" style={{ display: "block" }}>
                <h3>{b.child_name}</h3>
                <p>
                  {STATUS_LABEL[b.status] || b.status}
                  {b.story_id ? ` - ${b.story_id}` : ""}
                </p>
              </Link>
            );
          })}
        </div>
      </div>
    </>
  );
}
import { useEffect, useState } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import { api } from "../api";
import type { Book } from "../types";

export function BookStatus() {
  const { bookId } = useParams();
  const [book, setBook] = useState<Book | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!bookId) return;
    let alive = true;
    const tick = async () => {
      try {
        const b = await api.getBook(bookId);
        if (alive) setBook(b);
      } catch (err) {
        if (alive) setError(err instanceof Error ? err.message : "Erro");
      }
    };
    tick();
    const id = window.setInterval(tick, 2000);
    return () => {
      alive = false;
      window.clearInterval(id);
    };
  }, [bookId]);

  if (book?.status === "ready") {
    return <Navigate to={`/app/books/${bookId}/result`} replace />;
  }

  return (
    <div className="panel">
      <Link to="/app" className="muted">
        Meus livros
      </Link>
      <h1>Gerando o livro...</h1>
      <p className="muted">
        {book?.progress_message || "Preparando ilustracoes personalizadas."}
      </p>
      <div className="progress-wrap">
        <div className="progress-track">
          <div className="progress-fill" style={{ width: `${book?.progress ?? 5}%` }} />
        </div>
        <p className="muted" style={{ marginTop: "0.5rem" }}>
          {book?.progress ?? 0}%
        </p>
      </div>
      {book?.status === "failed" && (
        <p className="error">{book.error_message || "A geracao falhou. Tente novamente."}</p>
      )}
      {error && <p className="error">{error}</p>}
      {book?.status === "failed" && (
        <Link className="btn btn-primary" to={`/app/books/${bookId}/story`}>
          Tentar de novo
        </Link>
      )}
    </div>
  );
}
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, getToken } from "../api";
import type { Book } from "../types";

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

  useEffect(() => {
    if (!bookId) return;
    api
      .getBook(bookId)
      .then(setBook)
      .catch((err) => setError(err.message));
  }, [bookId]);

  return (
    <div className="panel">
      <Link to="/app" className="muted">
        Meus livros
      </Link>
      <h1>{book ? `Livro de ${book.child_name}` : "Seu ebook"}</h1>
      <p className="muted">Preview das paginas e download do PDF.</p>
      {error && <p className="error">{error}</p>}
      {book && (
        <>
          <div className="page-gallery">
            {book.page_urls.map((url, i) => (
              <img key={url} src={withToken(url) || url} alt={`Pagina ${i + 1}`} loading="lazy" />
            ))}
          </div>
          <div className="row">
            {book.pdf_url && (
              <a className="btn btn-coral" href={withToken(book.pdf_url) || book.pdf_url} target="_blank" rel="noreferrer">
                Baixar PDF
              </a>
            )}
            <Link className="btn btn-ghost" to="/app/new">
              Criar outro
            </Link>
          </div>
        </>
      )}
    </div>
  );
}

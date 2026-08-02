import { FormEvent, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";
import logo from "../assets/logo.png";
import "../landing.css";

export function Register() {
  const { user, register } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/app" replace />;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await register(email, password, name);
      navigate("/app/new");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha no cadastro");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="kid auth-kid" data-theme="light">
      <div className="sky" aria-hidden>
        <svg className="dstar d1" viewBox="0 0 24 24" aria-hidden>
          <path fill="currentColor" d="M12 2l2.4 7.4H22l-6 4.6 2.3 7-6.3-4.6L5.7 21l2.3-7-6-4.6h7.6z" />
        </svg>
        <svg className="dstar d2" viewBox="0 0 24 24" aria-hidden>
          <path fill="currentColor" d="M12 2l2.4 7.4H22l-6 4.6 2.3 7-6.3-4.6L5.7 21l2.3-7-6-4.6h7.6z" />
        </svg>
        <svg className="dstar d3" viewBox="0 0 24 24" aria-hidden>
          <path fill="currentColor" d="M12 2l2.4 7.4H22l-6 4.6 2.3 7-6.3-4.6L5.7 21l2.3-7-6-4.6h7.6z" />
        </svg>
        <svg className="dmoon m1" viewBox="0 0 24 24" aria-hidden>
          <path d="M17 15A8 8 0 1 1 9 4a7 7 0 0 0 8 11z" fill="#f4b740" />
        </svg>
      </div>

      <div className="auth-shell">
        <div className="auth-card">
          <Link to="/" className="kbrand auth-logo">
            <img src={logo} alt="Story R Us" />
          </Link>
          <h1>Criar conta</h1>
          <p className="auth-lead">Comece a transformar fotos em livros e vídeos mágicos.</p>
          <form className="auth-form" onSubmit={onSubmit}>
            <label>
              Seu nome
              <input value={name} onChange={(e) => setName(e.target.value)} />
            </label>
            <label>
              Email
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </label>
            <label>
              Senha
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
              />
            </label>
            {error && <p className="auth-error">{error}</p>}
            <button className="kbtn kbtn-primary auth-cta" disabled={busy} type="submit">
              {busy ? "Criando..." : "Começar"}
            </button>
          </form>
          <p className="auth-foot">
            Já tem conta? <Link to="/login">Entrar</Link>
          </p>
        </div>
      </div>
    </div>
  );
}

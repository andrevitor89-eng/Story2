import { FormEvent, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";
import logo from "../assets/logo.png";

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
    <div className="auth-page">
      <div className="auth-sky" aria-hidden />
      <div className="panel auth-panel">
        <Link to="/" className="auth-brand">
          <img src={logo} alt="Story R Us" />
        </Link>
        <h1>Criar conta</h1>
        <p className="auth-lead">Comece a transformar fotos em livros e vídeos mágicos.</p>
        <form className="form-grid" onSubmit={onSubmit}>
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
          {error && <p className="error">{error}</p>}
          <button className="btn btn-primary auth-submit" disabled={busy} type="submit">
            {busy ? "Criando..." : "Começar"}
          </button>
        </form>
        <p className="muted">
          Já tem conta? <Link to="/login">Entrar</Link>
        </p>
      </div>
    </div>
  );
}

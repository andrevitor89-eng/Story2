import { Navigate, Outlet, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth";
import { Landing } from "./Landing";
import { BookResult } from "./pages/BookResult";
import { BookStatus } from "./pages/BookStatus";
import { Library } from "./pages/Library";
import { Login } from "./pages/Login";
import { NewBook } from "./pages/NewBook";
import { PickStory } from "./pages/PickStory";
import { Register } from "./pages/Register";

function Protected() {
  const { user, loading } = useAuth();
  if (loading) return <div className="panel">Carregando...</div>;
  if (!user) return <Navigate to="/login" replace />;
  return <Outlet />;
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/app" element={<Protected />}>
          <Route index element={<Library />} />
          <Route path="new" element={<NewBook />} />
          <Route path="books/:bookId/story" element={<PickStory />} />
          <Route path="books/:bookId/status" element={<BookStatus />} />
          <Route path="books/:bookId/result" element={<BookResult />} />
        </Route>
      </Routes>
    </AuthProvider>
  );
}
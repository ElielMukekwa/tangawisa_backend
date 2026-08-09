import { useState } from "react";
import { getBackendBaseUrl, login, setBackendBaseUrl } from "../lib/api";

export default function LoginPage() {
  const isFileMode = window.location.protocol === "file:";
  const [email, setEmail] = useState("admin@tangawisa.app");
  const [password, setPassword] = useState("12345678");
  const [backendBase, setBackendBase] = useState(getBackendBaseUrl());
  const [status, setStatus] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      if (isFileMode) {
        setBackendBaseUrl(backendBase);
      }
      const result = await login(email, password);
      setStatus(`Connecte en tant que ${result.user.full_name}.`);
      window.location.hash = "/dashboard";
    } catch (error) {
      setStatus(error.message);
    }
  };

  return (
    <main className="mx-auto flex min-h-screen max-w-7xl items-center px-4 py-10 sm:px-6 lg:px-8">
      <section className="grid w-full gap-8 lg:grid-cols-[1.05fr_0.95fr]">
        <div className="rounded-[2rem] border border-white/10 bg-white/5 p-8 backdrop-blur-xl">
          <div className="inline-flex rounded-full border border-brand-300/20 bg-brand-500/10 px-4 py-2 text-xs font-bold uppercase tracking-[0.35em] text-brand-100">
            Administration React
          </div>
          <h1 className="mt-6 font-display text-4xl font-bold text-white sm:text-5xl">
            Connecte-toi pour gerer le contenu de Tangawisa.
          </h1>
          <p className="mt-5 max-w-2xl text-base leading-8 text-stone-300">
            Cette version React reprend le back-office du site avec connexion, resume backend, edition du contenu et bibliotheque media.
          </p>
        </div>

        <div className="rounded-[2rem] border border-white/10 bg-stone-950/80 p-8 shadow-2xl">
          <h2 className="font-display text-3xl font-bold text-white">Connexion admin</h2>
          <form className="mt-6 grid gap-4" onSubmit={handleSubmit}>
            {isFileMode ? (
              <label className="block">
                <span className="mb-2 block text-sm font-semibold text-stone-200">URL du backend</span>
                <input
                  value={backendBase}
                  onChange={(event) => setBackendBase(event.target.value)}
                  className="w-full rounded-2xl border border-white/10 bg-stone-900 px-4 py-3 text-white outline-none"
                />
              </label>
            ) : null}

            <label className="block">
              <span className="mb-2 block text-sm font-semibold text-stone-200">E-mail</span>
              <input
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                type="email"
                className="w-full rounded-2xl border border-white/10 bg-stone-900 px-4 py-3 text-white outline-none"
                required
              />
            </label>

            <label className="block">
              <span className="mb-2 block text-sm font-semibold text-stone-200">Mot de passe</span>
              <input
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                type="password"
                className="w-full rounded-2xl border border-white/10 bg-stone-900 px-4 py-3 text-white outline-none"
                required
              />
            </label>

            <button type="submit" className="mt-2 inline-flex h-12 items-center justify-center rounded-full bg-brand-500 px-6 text-sm font-bold text-white transition hover:bg-brand-400">
              Ouvrir l'administration React
            </button>
          </form>

          {status ? (
            <div className="mt-6 rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-stone-300">
              {status}
            </div>
          ) : null}
        </div>
      </section>
    </main>
  );
}

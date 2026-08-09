import { useEffect, useState } from "react";
import { clearStoredToken, getProfile, getSummary } from "../lib/api";

export default function DashboardPage() {
  const [profile, setProfile] = useState(null);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([getProfile(), getSummary()])
      .then(([user, data]) => {
        setProfile(user);
        setSummary(data);
      })
      .catch((err) => setError(err.message));
  }, []);

  const handleLogout = () => {
    clearStoredToken();
    window.location.hash = "/login";
  };

  return (
    <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <header className="mb-6 rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
        <div className="flex flex-col gap-5 xl:flex-row xl:items-center xl:justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.35em] text-brand-100">Back-office React</p>
            <h1 className="mt-3 font-display text-3xl font-bold text-white sm:text-4xl">Tableau de bord admin</h1>
            <p className="mt-3 text-sm leading-7 text-stone-300">
              {profile ? `Connecte en tant que ${profile.full_name} (${profile.role}).` : "Chargement de la session..."}
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <a href="/presentation/" target="_blank" rel="noreferrer" className="inline-flex h-11 items-center justify-center rounded-full border border-white/10 bg-white/5 px-5 text-sm font-bold text-white">Voir le site public</a>
            <button onClick={handleLogout} type="button" className="inline-flex h-11 items-center justify-center rounded-full bg-brand-500 px-5 text-sm font-bold text-white">Se deconnecter</button>
          </div>
        </div>
      </header>

      {error ? <div className="mb-6 rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">{error}</div> : null}

      <section className="grid gap-5 md:grid-cols-3">
        <a href="#/content" className="rounded-[2rem] border border-white/10 bg-white/5 p-6 transition hover:-translate-y-1 hover:bg-white/10">
          <p className="text-sm uppercase tracking-[0.25em] text-brand-100">01</p>
          <h2 className="mt-4 font-display text-2xl font-bold text-white">Contenu du site</h2>
          <p className="mt-3 text-sm leading-7 text-stone-300">Edition complete du JSON du site via React.</p>
        </a>
        <a href="#/media" className="rounded-[2rem] border border-white/10 bg-white/5 p-6 transition hover:-translate-y-1 hover:bg-white/10">
          <p className="text-sm uppercase tracking-[0.25em] text-brand-100">02</p>
          <h2 className="mt-4 font-display text-2xl font-bold text-white">Bibliotheque media</h2>
          <p className="mt-3 text-sm leading-7 text-stone-300">Upload et reutilisation des images du site.</p>
        </a>
        <a href="/static/admin/login.html" className="rounded-[2rem] border border-white/10 bg-gradient-to-br from-brand-500/20 to-white/5 p-6 transition hover:-translate-y-1 hover:bg-white/10">
          <p className="text-sm uppercase tracking-[0.25em] text-brand-100">03</p>
          <h2 className="mt-4 font-display text-2xl font-bold text-white">Admin HTML legacy</h2>
          <p className="mt-3 text-sm leading-7 text-stone-300">Acces temporaire a l'ancienne version pendant la transition.</p>
        </a>
      </section>

      {summary ? (
        <section className="mt-6 grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-[2rem] border border-white/10 bg-white/5 p-6">
            <p className="text-xs font-bold uppercase tracking-[0.35em] text-brand-100">Resume backend</p>
            <h2 className="mt-3 font-display text-3xl font-bold text-white">Statistiques reelles</h2>
            <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {[
                ["Utilisateurs", summary.stats.total_users],
                ["Clients", summary.stats.total_clients],
                ["Vendeurs", summary.stats.total_sellers],
                ["Admin + support", summary.stats.total_admins_support],
                ["Boutiques actives", summary.stats.active_shops],
                ["Produits actifs", summary.stats.active_products],
                ["Conversations", summary.stats.conversations],
                ["Tickets ouverts", summary.stats.open_tickets],
                ["Signalements ouverts", summary.stats.open_reports],
                ["Images uploades", summary.stats.uploaded_images],
              ].map(([label, value]) => (
                <div key={label} className="rounded-[1.5rem] border border-white/10 bg-black/20 p-4">
                  <p className="text-xs uppercase tracking-[0.25em] text-stone-400">{label}</p>
                  <p className="mt-3 font-display text-3xl font-bold text-white">{value}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-[2rem] border border-white/10 bg-white/5 p-6">
            <p className="text-xs font-bold uppercase tracking-[0.35em] text-brand-100">Etat du site</p>
            <h2 className="mt-3 font-display text-3xl font-bold text-white">Contenu public</h2>
            <div className="mt-6 grid gap-3">
              {Object.entries(summary.content_blocks).map(([key, value]) => (
                <div key={key} className="rounded-2xl border border-white/10 bg-black/20 px-4 py-4">
                  <p className="text-xs uppercase tracking-[0.25em] text-stone-400">{key}</p>
                  <p className="mt-2 text-sm font-semibold text-white">{value}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      ) : null}
    </main>
  );
}

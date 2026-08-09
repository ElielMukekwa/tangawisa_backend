import { useEffect, useMemo, useState } from "react";
import { getContent, saveContent } from "../lib/api";

const labels = {
  app_name: "Identite",
  hero: "Accueil",
  features: "Fonctionnalites",
  feature_items: "Cartes fonctionnalites",
  screenshots: "Captures",
  screenshot_items: "Galerie",
  download: "Telechargement",
  updates: "Nouveautes",
  faq: "Questions frequentes",
  contact: "Contact",
  privacy: "Confidentialite",
  terms: "Conditions",
  footer: "Pied de page",
};

const sectionLabel = (key) => labels[key] || key.replaceAll("_", " ");

export default function SiteContentPage() {
  const [content, setContent] = useState(null);
  const [selectedKey, setSelectedKey] = useState("");
  const [sectionDraft, setSectionDraft] = useState("");
  const [status, setStatus] = useState("Chargement du contenu...");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getContent()
      .then((data) => {
        const keys = Object.keys(data.content);
        const firstKey = keys.includes("hero") ? "hero" : keys[0];
        setContent(data.content);
        setSelectedKey(firstKey);
        setSectionDraft(JSON.stringify(data.content[firstKey], null, 2));
        setStatus(`Contenu charge depuis ${data.source}. Choisissez une section a gauche.`);
      })
      .catch((error) => setStatus(error.message));
  }, []);

  const sectionKeys = useMemo(() => (content ? Object.keys(content) : []), [content]);

  const selectSection = (key) => {
    if (!content) return;
    setSelectedKey(key);
    setSectionDraft(JSON.stringify(content[key], null, 2));
    setStatus(`Section « ${sectionLabel(key)} » ouverte.`);
  };

  const handleSave = async () => {
    if (!content || !selectedKey) return;
    setSaving(true);
    try {
      const parsedSection = JSON.parse(sectionDraft);
      const nextContent = { ...content, [selectedKey]: parsedSection };
      const response = await saveContent(nextContent);
      setContent(response.content);
      setSectionDraft(JSON.stringify(response.content[selectedKey], null, 2));
      setStatus(`Section « ${sectionLabel(selectedKey)} » enregistree et publiee.`);
    } catch (error) {
      setStatus(`Enregistrement refuse : ${error.message}`);
    } finally {
      setSaving(false);
    }
  };

  const restoreSection = () => {
    if (!content || !selectedKey) return;
    setSectionDraft(JSON.stringify(content[selectedKey], null, 2));
    setStatus("Modifications locales annulees.");
  };

  return (
    <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <header className="mb-6 flex flex-col gap-4 rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur-xl lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.35em] text-brand-100">Contenu public</p>
          <h1 className="mt-3 font-display text-3xl font-bold text-white">Gestion du site Tangawisa</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-stone-400">
            Modifiez une seule section a la fois. Le backend valide toujours la structure complete avant publication.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <a href="#/dashboard" className="inline-flex h-11 items-center justify-center rounded-full border border-white/10 bg-white/5 px-5 text-sm font-bold text-white">Dashboard</a>
          <a href="/presentation/" target="_blank" rel="noreferrer" className="inline-flex h-11 items-center justify-center rounded-full border border-brand-300/30 bg-brand-500/10 px-5 text-sm font-bold text-brand-100">Voir le site</a>
          <button disabled={saving || !content} onClick={handleSave} type="button" className="inline-flex h-11 items-center justify-center rounded-full bg-brand-500 px-5 text-sm font-bold text-white disabled:cursor-not-allowed disabled:opacity-50">
            {saving ? "Publication..." : "Enregistrer et publier"}
          </button>
        </div>
      </header>

      <div className="mb-6 rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-stone-300">{status}</div>

      <section className="grid gap-6 lg:grid-cols-[280px_minmax(0,1fr)]">
        <aside className="h-fit rounded-[2rem] border border-white/10 bg-white/5 p-4 lg:sticky lg:top-6">
          <p className="px-3 pb-3 text-xs font-bold uppercase tracking-[0.3em] text-stone-400">Sections</p>
          <nav className="grid gap-2">
            {sectionKeys.map((key) => (
              <button
                key={key}
                type="button"
                onClick={() => selectSection(key)}
                className={`rounded-2xl px-4 py-3 text-left text-sm font-semibold transition ${
                  selectedKey === key
                    ? "bg-brand-500 text-white"
                    : "bg-black/20 text-stone-300 hover:bg-white/10 hover:text-white"
                }`}
              >
                {sectionLabel(key)}
              </button>
            ))}
          </nav>
        </aside>

        <div className="rounded-[2rem] border border-white/10 bg-white/5 p-5 sm:p-6">
          <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.3em] text-brand-100">Section active</p>
              <h2 className="mt-2 font-display text-2xl font-bold text-white">{selectedKey ? sectionLabel(selectedKey) : "Chargement"}</h2>
            </div>
            <button type="button" onClick={restoreSection} disabled={!content} className="inline-flex h-10 items-center justify-center rounded-full border border-white/10 px-4 text-sm font-bold text-stone-200 disabled:opacity-50">
              Annuler les changements
            </button>
          </div>

          <label className="block">
            <span className="mb-2 block text-sm text-stone-400">Donnees structurees de cette section</span>
            <textarea
              value={sectionDraft}
              onChange={(event) => setSectionDraft(event.target.value)}
              className="min-h-[62vh] w-full resize-y rounded-[1.5rem] border border-white/10 bg-stone-950 px-4 py-4 font-mono text-sm leading-6 text-white outline-none focus:border-brand-300/50"
              spellCheck="false"
              aria-label={`Contenu de la section ${selectedKey}`}
            />
          </label>
          <p className="mt-3 text-xs leading-5 text-stone-500">
            Les guillemets, virgules et crochets doivent rester valides. En cas d erreur, aucune modification n est publiee.
          </p>
        </div>
      </section>
    </main>
  );
}

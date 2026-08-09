import { useEffect, useState } from "react";
import { listMedia, uploadImage } from "../lib/api";

export default function MediaLibraryPage() {
  const [items, setItems] = useState([]);
  const [status, setStatus] = useState("Chargement...");

  const refresh = async () => {
    try {
      const response = await listMedia();
      setItems(response.items);
      setStatus("Bibliotheque chargee.");
    } catch (error) {
      setStatus(error.message);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const handleUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      await uploadImage(file);
      setStatus("Image televersee avec succes.");
      await refresh();
    } catch (error) {
      setStatus(error.message);
    } finally {
      event.target.value = "";
    }
  };

  return (
    <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <header className="mb-6 flex flex-col gap-4 rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur-xl lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.35em] text-brand-100">React Media</p>
          <h1 className="mt-3 font-display text-3xl font-bold text-white">Bibliotheque media</h1>
        </div>
        <div className="flex flex-wrap gap-3">
          <a href="#/dashboard" className="inline-flex h-11 items-center justify-center rounded-full border border-white/10 bg-white/5 px-5 text-sm font-bold text-white">Dashboard</a>
          <label className="inline-flex h-11 cursor-pointer items-center justify-center rounded-full bg-brand-500 px-5 text-sm font-bold text-white">
            Televerser
            <input type="file" accept="image/*" onChange={handleUpload} className="hidden" />
          </label>
        </div>
      </header>

      <div className="mb-6 rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-stone-300">{status}</div>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {items.map((item) => (
          <article key={item.filename} className="rounded-[1.5rem] border border-white/10 bg-white/5 p-4">
            <img src={item.url} alt={item.filename} className="h-52 w-full rounded-[1.25rem] object-cover bg-stone-900" />
            <p className="mt-4 truncate text-sm font-semibold text-white">{item.filename}</p>
            <p className="mt-2 break-all text-xs text-stone-400">{item.url}</p>
          </article>
        ))}
      </section>
    </main>
  );
}

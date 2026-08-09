window.siteAdmin = (() => {
  const tokenKey = "sitePresentationAdminToken";
  const backendBaseKey = "sitePresentationAdminBackendBaseUrl";
  let cachedContent = null;

  const getToken = () => localStorage.getItem(tokenKey) || "";
  const getStoredBackendBaseUrl = () => localStorage.getItem(backendBaseKey) || "";

  const normalizeBaseUrl = (value) => (value || "").trim().replace(/\/+$/, "");

  const isFileMode = () => window.location.protocol === "file:";

  const getBackendBaseUrl = () => {
    if (!isFileMode()) {
      return window.location.origin;
    }
    return normalizeBaseUrl(getStoredBackendBaseUrl()) || "http://127.0.0.1:8000";
  };

  const setBackendBaseUrl = (value) => {
    const normalized = normalizeBaseUrl(value);
    if (!normalized) {
      localStorage.removeItem(backendBaseKey);
      return "";
    }
    localStorage.setItem(backendBaseKey, normalized);
    return normalized;
  };

  const apiUrl = (path) => `${getBackendBaseUrl()}${path}`;

  const setToken = (token) => {
    localStorage.setItem(tokenKey, token);
  };

  const bootstrapTokenFromUrl = () => {
    const currentUrl = new URL(window.location.href);
    const hashParams = new URLSearchParams(currentUrl.hash.startsWith("#") ? currentUrl.hash.slice(1) : "");
    const queryToken = currentUrl.searchParams.get("access_token");
    const hashToken = hashParams.get("access_token");
    const token = queryToken || hashToken;

    if (!token) {
      return "";
    }

    setToken(token);

    currentUrl.searchParams.delete("access_token");
    hashParams.delete("access_token");
    currentUrl.hash = hashParams.toString() ? `#${hashParams.toString()}` : "";
    window.history.replaceState({}, document.title, currentUrl.toString());
    return token;
  };

  const logout = () => {
    localStorage.removeItem(tokenKey);
  };

  const authHeaders = () => ({
    "Content-Type": "application/json",
    ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {})
  });

  const fetchJson = async (url, options = {}) => {
    const requestUrl = url.startsWith("http://") || url.startsWith("https://")
      ? url
      : (isFileMode() ? apiUrl(url) : url);
    const response = await fetch(requestUrl, options);
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail || "Operation impossible.");
    }
    return response.json();
  };

  const login = async (email, password) => {
    const result = await fetchJson("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    setToken(result.access_token);
    return result;
  };

  const getProfile = async () => {
    return fetchJson("/api/v1/auth/me", {
      headers: {
        Accept: "application/json",
        ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {})
      }
    });
  };

  const getSummary = async () => {
    return fetchJson("/api/v1/site-presentation/admin/summary", {
      headers: {
        Accept: "application/json",
        ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {})
      }
    });
  };

  const requireAuth = (redirectUrl) => {
    const token = getToken() || bootstrapTokenFromUrl();
    if (!token) {
      window.location.href = redirectUrl;
    }
  };

  const loadContent = async () => {
    const data = await fetchJson("/api/v1/site-presentation/admin/content", {
      headers: {
        Accept: "application/json",
        ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {})
      }
    });
    cachedContent = data.content;
    return data;
  };

  const saveContent = async (payload) => {
    const data = await fetchJson("/api/v1/site-presentation/admin/content", {
      method: "PUT",
      headers: authHeaders(),
      body: JSON.stringify(payload)
    });
    cachedContent = data.content;
    return data;
  };

  const uploadImage = async (file) => {
    const formData = new FormData();
    formData.append("image", file);
    const response = await fetch(isFileMode() ? apiUrl("/api/v1/site-presentation/admin/upload-image") : "/api/v1/site-presentation/admin/upload-image", {
      method: "POST",
      headers: getToken() ? { Authorization: `Bearer ${getToken()}` } : {},
      body: formData
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail || "Upload impossible.");
    }

    return response.json();
  };

  const listMedia = async () => {
    return fetchJson("/api/v1/site-presentation/admin/media", {
      headers: {
        Accept: "application/json",
        ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {})
      }
    });
  };

  const setBanner = (element, text, tone = "neutral") => {
    element.textContent = text;
    element.className = `mb-6 rounded-2xl border px-4 py-3 text-sm ${
      tone === "success"
        ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-200"
        : tone === "error"
          ? "border-red-500/30 bg-red-500/10 text-red-200"
          : "border-white/10 bg-black/20 text-stone-300"
    }`;
  };

  const syncEditableState = () => {
    document.querySelectorAll(".editable").forEach((element) => {
      const hasText = element.textContent.trim().length > 0;
      element.classList.toggle("editable-empty", !hasText);
    });
  };

  const createCard = (title, html, classes = "") => {
    const wrapper = document.createElement("article");
    wrapper.className = `rounded-[1.5rem] border border-white/10 bg-black/20 p-4 ${classes}`;
    wrapper.innerHTML = `
      <div class="mb-3 flex items-center justify-between gap-4">
        <h4 class="font-display text-lg font-bold text-white">${title}</h4>
        <button type="button" class="rounded-full border border-red-500/20 bg-red-500/10 px-3 py-1 text-xs font-bold text-red-200" data-remove-item>Supprimer</button>
      </div>
      <div class="grid gap-3">${html}</div>
    `;
    wrapper.querySelector("[data-remove-item]").addEventListener("click", () => {
      wrapper.remove();
      syncEditableState();
    });
    return wrapper;
  };

  const collectCards = (containerId, mapper) => [...document.getElementById(containerId).children].map(mapper);

  const mountEditableBase = () => {
    document.querySelectorAll(".editable").forEach((element) => {
      element.addEventListener("input", syncEditableState);
    });
    syncEditableState();
  };

  const bindImageUploader = (inputId, buttonId, onUploaded, banner) => {
    const input = document.getElementById(inputId);
    const button = document.getElementById(buttonId);
    if (!input || !button) {
      return;
    }

    button.addEventListener("click", () => input.click());
    input.addEventListener("change", async () => {
      const file = input.files?.[0];
      if (!file) return;
      try {
        const result = await uploadImage(file);
        onUploaded(result.url);
        setBanner(banner, "Image televersee avec succes.", "success");
      } catch (error) {
        setBanner(banner, error.message, "error");
      } finally {
        input.value = "";
      }
    });
  };

  const footerLinkCard = (item) => createCard("Lien footer", `
    <div contenteditable="true" data-role="label" data-placeholder="Libelle" class="editable rounded-xl px-3 py-2 text-lg font-bold text-white">${item.label || ""}</div>
    <div contenteditable="true" data-role="url" data-placeholder="URL" class="editable rounded-xl px-3 py-2 text-sm text-stone-300">${item.url || ""}</div>
  `);

  const mountHomeEditor = async () => {
    const banner = document.getElementById("status-banner");

    const renderStats = (stats) => {
      const container = document.getElementById("stats-list");
      container.innerHTML = "";
      stats.forEach((item) => {
        const card = createCard("Statistique", `
          <div contenteditable="true" data-role="value" data-placeholder="Valeur" class="editable rounded-xl px-3 py-2 text-2xl font-bold text-white">${item.value || ""}</div>
          <div contenteditable="true" data-role="label" data-placeholder="Libelle" class="editable rounded-xl px-3 py-2 text-xs uppercase tracking-[0.25em] text-stone-400">${item.label || ""}</div>
        `);
        container.appendChild(card);
      });
      syncEditableState();
    };

    const renderSteps = (steps) => {
      const container = document.getElementById("steps-list");
      container.innerHTML = "";
      steps.forEach((step) => {
        const card = createCard("Etape", `
          <div contenteditable="true" data-role="value" data-placeholder="Texte de l'etape" class="editable rounded-xl px-3 py-2 text-sm leading-7 text-stone-300">${step || ""}</div>
        `);
        container.appendChild(card);
      });
      syncEditableState();
    };

    const assign = (id, value) => {
      document.getElementById(id).textContent = value || "";
    };

    const data = await loadContent();
    setBanner(banner, `Contenu charge avec succes. Source: ${data.source}.`, "success");
    const content = data.content;
    assign("hero-badge", content.hero.badge);
    assign("hero-title", content.hero.title);
    assign("hero-description", content.hero.description);
    assign("hero-primary-cta", content.hero.primary_cta_label);
    assign("hero-secondary-cta", content.hero.secondary_cta_label);
    assign("download-eyebrow", content.download.eyebrow);
    assign("download-title", content.download.title);
    assign("download-description", content.download.description);
    assign("latest-version", `Version ${content.download.latest_version.version}`);
    assign("latest-date", `Date : ${content.download.latest_version.date}`);
    assign("latest-size", `Taille : ${content.download.latest_version.size}`);
    assign("latest-android", `Android minimum : ${content.download.latest_version.android_min}`);
    assign("latest-changes", `Nouveautes : ${content.download.latest_version.changes}`);
    document.getElementById("hero-preview-admin-image").src = content.hero.preview_image_url || "";
    document.getElementById("hero-preview-admin-image").alt = content.hero.preview_image_alt || "";
    document.getElementById("hero-image-url").textContent = content.hero.preview_image_url || "";
    renderStats(content.hero.stats);
    renderSteps(content.download.steps);

    const footerContainer = document.getElementById("footer-primary-links-list");
    if (footerContainer) {
      footerContainer.innerHTML = "";
      (content.footer.primary_links || []).forEach((item) => {
        footerContainer.appendChild(footerLinkCard(item));
      });
    }

    bindImageUploader("hero-image-upload", "hero-image-upload-button", (url) => {
      cachedContent.hero.preview_image_url = url;
      document.getElementById("hero-preview-admin-image").src = url;
      document.getElementById("hero-image-url").textContent = url;
    }, banner);

    document.getElementById("add-stat-button").addEventListener("click", () => {
      renderStats([...collectCards("stats-list", (card) => ({
        value: card.querySelector('[data-role="value"]').textContent.trim(),
        label: card.querySelector('[data-role="label"]').textContent.trim()
      })), { value: "", label: "" }]);
    });

    document.getElementById("add-step-button").addEventListener("click", () => {
      renderSteps([...collectCards("steps-list", (card) => card.querySelector('[data-role="value"]').textContent.trim()), ""]);
    });

    document.getElementById("add-footer-primary-link-button")?.addEventListener("click", () => {
      footerContainer.appendChild(footerLinkCard({ label: "", url: "" }));
      syncEditableState();
    });

    document.getElementById("save-button").addEventListener("click", async () => {
      try {
        const payload = structuredClone(cachedContent);
        payload.hero.badge = document.getElementById("hero-badge").textContent.trim();
        payload.hero.title = document.getElementById("hero-title").textContent.trim();
        payload.hero.description = document.getElementById("hero-description").textContent.trim();
        payload.hero.primary_cta_label = document.getElementById("hero-primary-cta").textContent.trim();
        payload.hero.secondary_cta_label = document.getElementById("hero-secondary-cta").textContent.trim();
        payload.hero.preview_image_url = document.getElementById("hero-image-url").textContent.trim();
        payload.hero.stats = collectCards("stats-list", (card) => ({
          value: card.querySelector('[data-role="value"]').textContent.trim(),
          label: card.querySelector('[data-role="label"]').textContent.trim()
        })).filter((item) => item.value || item.label);
        payload.download.eyebrow = document.getElementById("download-eyebrow").textContent.trim();
        payload.download.title = document.getElementById("download-title").textContent.trim();
        payload.download.description = document.getElementById("download-description").textContent.trim();
        payload.download.latest_version.version = document.getElementById("latest-version").textContent.trim().replace(/^Version\s*/i, "");
        payload.download.latest_version.date = document.getElementById("latest-date").textContent.trim().replace(/^Date\s*:\s*/i, "");
        payload.download.latest_version.size = document.getElementById("latest-size").textContent.trim().replace(/^Taille\s*:\s*/i, "");
        payload.download.latest_version.android_min = document.getElementById("latest-android").textContent.trim().replace(/^Android minimum\s*:\s*/i, "");
        payload.download.latest_version.changes = document.getElementById("latest-changes").textContent.trim().replace(/^Nouveautes\s*:\s*/i, "");
        payload.download.steps = collectCards("steps-list", (card) => card.querySelector('[data-role="value"]').textContent.trim()).filter(Boolean);
        payload.footer.primary_links = collectCards("footer-primary-links-list", (card) => ({
          name: card.querySelector('[data-role="label"]').textContent.trim(),
          label: card.querySelector('[data-role="label"]').textContent.trim(),
          description: "",
          url: card.querySelector('[data-role="url"]').textContent.trim()
        })).filter((item) => item.label || item.url);
        const saved = await saveContent(payload);
        setBanner(banner, `Contenu enregistre avec succes. Source: ${saved.source}.`, "success");
      } catch (error) {
        setBanner(banner, error.message, "error");
      }
    });

    syncEditableState();
  };

  const mountContentPagesEditor = async () => {
    const banner = document.getElementById("status-banner");

    const renderCollection = (containerId, items, factory) => {
      const container = document.getElementById(containerId);
      container.innerHTML = "";
      items.forEach((item) => container.appendChild(factory(item)));
      syncEditableState();
    };

    const featureCard = (item) => createCard("Carte fonctionnalite", `
      <div contenteditable="true" data-role="icon" data-placeholder="Icone" class="editable rounded-xl px-3 py-2 text-3xl">${item.icon || ""}</div>
      <div contenteditable="true" data-role="title" data-placeholder="Titre" class="editable rounded-xl px-3 py-2 text-xl font-bold text-white">${item.title || ""}</div>
      <div contenteditable="true" data-role="description" data-placeholder="Description" class="editable rounded-xl px-3 py-2 text-sm leading-7 text-stone-300">${item.description || ""}</div>
    `);

    const screenshotCard = (item) => {
      const card = createCard("Capture", `
        <img src="${item.image_url || ""}" alt="${item.image_alt || ""}" class="h-52 w-full rounded-[1.25rem] object-cover bg-stone-900" data-role="image-preview">
        <div class="flex flex-wrap gap-3">
          <input type="file" accept="image/*" class="hidden" data-role="image-input">
          <button type="button" class="inline-flex h-10 items-center justify-center rounded-full border border-white/10 bg-white/5 px-4 text-sm font-bold text-white" data-role="image-upload-button">Uploader l'image</button>
        </div>
        <div class="break-all text-xs text-stone-400" data-role="image-url">${item.image_url || ""}</div>
        <div contenteditable="true" data-role="title" data-placeholder="Titre" class="editable rounded-xl px-3 py-2 text-xl font-bold text-white">${item.title || ""}</div>
        <div contenteditable="true" data-role="description" data-placeholder="Description" class="editable rounded-xl px-3 py-2 text-sm leading-7 text-stone-300">${item.description || ""}</div>
        <div contenteditable="true" data-role="image-alt" data-placeholder="Alt image" class="editable rounded-xl px-3 py-2 text-sm text-stone-300">${item.image_alt || ""}</div>
      `);
      card.dataset.imageUrl = item.image_url || "";
      const input = card.querySelector('[data-role="image-input"]');
      const button = card.querySelector('[data-role="image-upload-button"]');
      const image = card.querySelector('[data-role="image-preview"]');
      const urlText = card.querySelector('[data-role="image-url"]');
      button.addEventListener("click", () => input.click());
      input.addEventListener("change", async () => {
        const file = input.files?.[0];
        if (!file) return;
        try {
          const result = await uploadImage(file);
          card.dataset.imageUrl = result.url;
          image.src = result.url;
          urlText.textContent = result.url;
          setBanner(banner, "Capture televersee avec succes.", "success");
        } catch (error) {
          setBanner(banner, error.message, "error");
        } finally {
          input.value = "";
        }
      });
      return card;
    };

    const updateCard = (item) => {
      const card = createCard("Article", `
        <div contenteditable="true" data-role="version" data-placeholder="Version" class="editable rounded-xl px-3 py-2 text-xs font-bold uppercase tracking-[0.25em] text-brand-100">${item.version || ""}</div>
        <div contenteditable="true" data-role="title" data-placeholder="Titre" class="editable rounded-xl px-3 py-2 text-2xl font-bold text-white">${item.title || ""}</div>
        <div contenteditable="true" data-role="summary" data-placeholder="Resume" class="editable rounded-xl px-3 py-2 text-sm leading-7 text-stone-300">${item.summary || ""}</div>
      `);
      card.dataset.date = item.date || "";
      card.dataset.highlights = JSON.stringify(item.highlights || []);
      return card;
    };

    const faqCard = (item) => createCard("FAQ", `
      <div contenteditable="true" data-role="question" data-placeholder="Question" class="editable rounded-xl px-3 py-2 text-lg font-bold text-white">${item.question || ""}</div>
      <div contenteditable="true" data-role="answer" data-placeholder="Reponse" class="editable rounded-xl px-3 py-2 text-sm leading-7 text-stone-300">${item.answer || ""}</div>
    `);

    const contactCard = (item) => {
      const card = createCard("Canal", `
        <div contenteditable="true" data-role="name" data-placeholder="Nom" class="editable rounded-xl px-3 py-2 text-xs font-bold uppercase tracking-[0.25em] text-brand-100">${item.name || ""}</div>
        <div contenteditable="true" data-role="label" data-placeholder="Libelle" class="editable rounded-xl px-3 py-2 text-xl font-bold text-white">${item.label || ""}</div>
        <div contenteditable="true" data-role="description" data-placeholder="Description" class="editable rounded-xl px-3 py-2 text-sm leading-7 text-stone-300">${item.description || ""}</div>
      `);
      card.dataset.url = item.url || "";
      return card;
    };

    const legalCard = (item) => createCard("Bloc legal", `
      <div contenteditable="true" data-role="title" data-placeholder="Titre" class="editable rounded-xl px-3 py-2 text-lg font-bold text-white">${item.title || ""}</div>
      <div contenteditable="true" data-role="body" data-placeholder="Texte" class="editable rounded-xl px-3 py-2 text-sm leading-7 text-stone-300">${item.body || ""}</div>
    `);

    const assign = (id, value) => { document.getElementById(id).textContent = value || ""; };

    const data = await loadContent();
    setBanner(banner, `Contenu charge avec succes. Source: ${data.source}.`, "success");
    const content = data.content;
    assign("features-eyebrow", content.features.eyebrow);
    assign("features-title", content.features.title);
    assign("features-description", content.features.description);
    assign("screenshots-eyebrow", content.screenshots.eyebrow);
    assign("screenshots-title", content.screenshots.title);
    assign("screenshots-description", content.screenshots.description);
    assign("updates-eyebrow", content.updates.eyebrow);
    assign("updates-title", content.updates.title);
    assign("updates-description", content.updates.description);
    assign("faq-eyebrow", content.faq.eyebrow);
    assign("faq-title", content.faq.title);
    assign("faq-description", content.faq.description);
    assign("contact-eyebrow", content.contact.eyebrow);
    assign("contact-title", content.contact.title);
    assign("contact-description", content.contact.description);
    assign("privacy-eyebrow", content.privacy.eyebrow);
    assign("privacy-title", content.privacy.title);
    assign("privacy-description", content.privacy.description);
    assign("terms-eyebrow", content.terms.eyebrow);
    assign("terms-title", content.terms.title);
    assign("terms-description", content.terms.description);
    assign("footer-copy", content.footer.copyright);

    renderCollection("features-list", content.feature_items, featureCard);
    renderCollection("screenshots-list", content.screenshot_items, screenshotCard);
    renderCollection("updates-list", content.updates.posts, updateCard);
    renderCollection("faq-list", content.faq.items, faqCard);
    renderCollection("contact-list", content.contact.channels, contactCard);
    renderCollection("privacy-list", content.privacy.sections, legalCard);
    renderCollection("terms-list", content.terms.sections, legalCard);
    renderCollection("footer-primary-links-list", content.footer.primary_links || [], footerLinkCard);
    renderCollection("footer-legal-links-list", content.footer.legal_links || [], footerLinkCard);

    document.getElementById("add-feature-button").addEventListener("click", () => {
      document.getElementById("features-list").appendChild(featureCard({ icon: "", title: "", description: "" }));
      syncEditableState();
    });
    document.getElementById("add-screenshot-button").addEventListener("click", () => {
      document.getElementById("screenshots-list").appendChild(screenshotCard({ title: "", description: "", image_url: "", image_alt: "" }));
      syncEditableState();
    });
    document.getElementById("add-update-button").addEventListener("click", () => {
      document.getElementById("updates-list").appendChild(updateCard({ version: "", date: "", title: "", summary: "", highlights: [] }));
      syncEditableState();
    });
    document.getElementById("add-faq-button").addEventListener("click", () => {
      document.getElementById("faq-list").appendChild(faqCard({ question: "", answer: "" }));
      syncEditableState();
    });
    document.getElementById("add-contact-button").addEventListener("click", () => {
      document.getElementById("contact-list").appendChild(contactCard({ name: "", label: "", description: "", url: "" }));
      syncEditableState();
    });
    document.getElementById("add-privacy-button").addEventListener("click", () => {
      document.getElementById("privacy-list").appendChild(legalCard({ title: "", body: "" }));
      syncEditableState();
    });
    document.getElementById("add-terms-button").addEventListener("click", () => {
      document.getElementById("terms-list").appendChild(legalCard({ title: "", body: "" }));
      syncEditableState();
    });
    document.getElementById("add-footer-primary-link-button")?.addEventListener("click", () => {
      document.getElementById("footer-primary-links-list").appendChild(footerLinkCard({ label: "", url: "" }));
      syncEditableState();
    });
    document.getElementById("add-footer-legal-link-button")?.addEventListener("click", () => {
      document.getElementById("footer-legal-links-list").appendChild(footerLinkCard({ label: "", url: "" }));
      syncEditableState();
    });

    document.getElementById("save-button").addEventListener("click", async () => {
      try {
        const payload = structuredClone(cachedContent);
        payload.features.eyebrow = document.getElementById("features-eyebrow").textContent.trim();
        payload.features.title = document.getElementById("features-title").textContent.trim();
        payload.features.description = document.getElementById("features-description").textContent.trim();
        payload.screenshots.eyebrow = document.getElementById("screenshots-eyebrow").textContent.trim();
        payload.screenshots.title = document.getElementById("screenshots-title").textContent.trim();
        payload.screenshots.description = document.getElementById("screenshots-description").textContent.trim();
        payload.updates.eyebrow = document.getElementById("updates-eyebrow").textContent.trim();
        payload.updates.title = document.getElementById("updates-title").textContent.trim();
        payload.updates.description = document.getElementById("updates-description").textContent.trim();
        payload.faq.eyebrow = document.getElementById("faq-eyebrow").textContent.trim();
        payload.faq.title = document.getElementById("faq-title").textContent.trim();
        payload.faq.description = document.getElementById("faq-description").textContent.trim();
        payload.contact.eyebrow = document.getElementById("contact-eyebrow").textContent.trim();
        payload.contact.title = document.getElementById("contact-title").textContent.trim();
        payload.contact.description = document.getElementById("contact-description").textContent.trim();
        payload.privacy.eyebrow = document.getElementById("privacy-eyebrow").textContent.trim();
        payload.privacy.title = document.getElementById("privacy-title").textContent.trim();
        payload.privacy.description = document.getElementById("privacy-description").textContent.trim();
        payload.terms.eyebrow = document.getElementById("terms-eyebrow").textContent.trim();
        payload.terms.title = document.getElementById("terms-title").textContent.trim();
        payload.terms.description = document.getElementById("terms-description").textContent.trim();
        payload.footer.copyright = document.getElementById("footer-copy").textContent.trim();

        payload.feature_items = collectCards("features-list", (card) => ({
          icon: card.querySelector('[data-role="icon"]').textContent.trim(),
          title: card.querySelector('[data-role="title"]').textContent.trim(),
          description: card.querySelector('[data-role="description"]').textContent.trim()
        })).filter((item) => item.icon || item.title || item.description);

        payload.screenshot_items = collectCards("screenshots-list", (card) => ({
          title: card.querySelector('[data-role="title"]').textContent.trim(),
          description: card.querySelector('[data-role="description"]').textContent.trim(),
          image_url: card.dataset.imageUrl || "",
          image_alt: card.querySelector('[data-role="image-alt"]').textContent.trim()
        })).filter((item) => item.title || item.description || item.image_url);

        payload.updates.posts = collectCards("updates-list", (card) => ({
          version: card.querySelector('[data-role="version"]').textContent.trim(),
          date: card.dataset.date || "",
          title: card.querySelector('[data-role="title"]').textContent.trim(),
          summary: card.querySelector('[data-role="summary"]').textContent.trim(),
          highlights: JSON.parse(card.dataset.highlights || "[]")
        })).filter((item) => item.version || item.title || item.summary);

        payload.faq.items = collectCards("faq-list", (card) => ({
          question: card.querySelector('[data-role="question"]').textContent.trim(),
          answer: card.querySelector('[data-role="answer"]').textContent.trim()
        })).filter((item) => item.question || item.answer);

        payload.contact.channels = collectCards("contact-list", (card) => ({
          name: card.querySelector('[data-role="name"]').textContent.trim(),
          label: card.querySelector('[data-role="label"]').textContent.trim(),
          description: card.querySelector('[data-role="description"]').textContent.trim(),
          url: card.dataset.url || ""
        })).filter((item) => item.name || item.label || item.description);

        payload.footer.primary_links = collectCards("footer-primary-links-list", (card) => ({
          name: card.querySelector('[data-role="label"]').textContent.trim(),
          label: card.querySelector('[data-role="label"]').textContent.trim(),
          description: "",
          url: card.querySelector('[data-role="url"]').textContent.trim()
        })).filter((item) => item.label || item.url);

        payload.footer.legal_links = collectCards("footer-legal-links-list", (card) => ({
          name: card.querySelector('[data-role="label"]').textContent.trim(),
          label: card.querySelector('[data-role="label"]').textContent.trim(),
          description: "",
          url: card.querySelector('[data-role="url"]').textContent.trim()
        })).filter((item) => item.label || item.url);

        payload.privacy.sections = collectCards("privacy-list", (card) => ({
          title: card.querySelector('[data-role="title"]').textContent.trim(),
          body: card.querySelector('[data-role="body"]').textContent.trim()
        })).filter((item) => item.title || item.body);

        payload.terms.sections = collectCards("terms-list", (card) => ({
          title: card.querySelector('[data-role="title"]').textContent.trim(),
          body: card.querySelector('[data-role="body"]').textContent.trim()
        })).filter((item) => item.title || item.body);

        const saved = await saveContent(payload);
        setBanner(banner, `Contenu enregistre avec succes. Source: ${saved.source}.`, "success");
      } catch (error) {
        setBanner(banner, error.message, "error");
      }
    });

    syncEditableState();
  };

  const mountMediaLibrary = () => {
    const banner = document.getElementById("status-banner");
    const uploadForm = document.getElementById("upload-form");
    const resultBox = document.getElementById("upload-result");
    const uploadedUrl = document.getElementById("uploaded-url");
    const previewImage = document.getElementById("preview-image");
    const previewPlaceholder = document.getElementById("preview-placeholder");
    const mediaGrid = document.getElementById("media-grid");
    const mediaEmpty = document.getElementById("media-empty");
    const refreshButton = document.getElementById("refresh-media-button");

    const formatSize = (sizeBytes) => {
      if (sizeBytes < 1024) return `${sizeBytes} o`;
      if (sizeBytes < 1024 * 1024) return `${(sizeBytes / 1024).toFixed(1)} Ko`;
      return `${(sizeBytes / (1024 * 1024)).toFixed(1)} Mo`;
    };

    const renderMediaLibrary = async () => {
      try {
        const result = await listMedia();
        if (!mediaGrid || !mediaEmpty) return;

        mediaGrid.innerHTML = "";
        mediaEmpty.classList.toggle("hidden", result.items.length > 0);

        result.items.forEach((item) => {
          const card = document.createElement("article");
          card.className = "rounded-[1.5rem] border border-white/10 bg-black/20 p-4";
          card.innerHTML = `
            <img src="${item.url}" alt="${item.filename}" class="h-44 w-full rounded-[1.1rem] object-cover bg-stone-900">
            <div class="mt-4">
              <p class="truncate text-sm font-semibold text-white">${item.filename}</p>
              <p class="mt-1 text-xs text-stone-400">${formatSize(item.size_bytes)}</p>
            </div>
            <div class="mt-4 flex gap-2">
              <button type="button" class="inline-flex h-10 flex-1 items-center justify-center rounded-full border border-white/10 bg-white/5 px-4 text-sm font-bold text-white" data-copy-url="${item.url}">Copier l'URL</button>
              <button type="button" class="inline-flex h-10 flex-1 items-center justify-center rounded-full border border-brand-500/20 bg-brand-500/10 px-4 text-sm font-bold text-brand-100" data-preview-url="${item.url}">Apercu</button>
            </div>
          `;
          mediaGrid.appendChild(card);
        });

        mediaGrid.querySelectorAll("[data-copy-url]").forEach((button) => {
          button.addEventListener("click", async () => {
            await navigator.clipboard.writeText(button.dataset.copyUrl);
            setBanner(banner, "URL copiee dans le presse-papiers.", "success");
          });
        });

        mediaGrid.querySelectorAll("[data-preview-url]").forEach((button) => {
          button.addEventListener("click", () => {
            previewImage.src = button.dataset.previewUrl;
            previewImage.classList.remove("hidden");
            previewPlaceholder.classList.add("hidden");
          });
        });
      } catch (error) {
        setBanner(banner, error.message, "error");
      }
    };

    setBanner(banner, "Selectionne une image a televerser.", "neutral");

    uploadForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const file = document.getElementById("image-file").files?.[0];
      if (!file) {
        setBanner(banner, "Choisis d'abord une image.", "error");
        return;
      }

      try {
        const result = await uploadImage(file);
        uploadedUrl.value = result.url;
        resultBox.classList.remove("hidden");
        previewImage.src = result.url;
        previewImage.classList.remove("hidden");
        previewPlaceholder.classList.add("hidden");
        setBanner(banner, "Image televersee avec succes.", "success");
        await renderMediaLibrary();
      } catch (error) {
        setBanner(banner, error.message, "error");
      }
    });

    document.getElementById("copy-url-button").addEventListener("click", async () => {
      await navigator.clipboard.writeText(uploadedUrl.value);
      setBanner(banner, "URL copiee dans le presse-papiers.", "success");
    });

    refreshButton?.addEventListener("click", () => {
      renderMediaLibrary();
    });

    renderMediaLibrary();
  };

  return {
    login,
    logout,
    getProfile,
    getSummary,
    getBackendBaseUrl,
    setBackendBaseUrl,
    requireAuth,
    loadContent,
    saveContent,
    uploadImage,
    listMedia,
    mountEditableBase,
    mountHomeEditor,
    mountContentPagesEditor,
    mountMediaLibrary
  };
})();

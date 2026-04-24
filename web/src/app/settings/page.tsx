"use client";

import { useState, useEffect } from "react";
import type { AppSettings, ResearchDomain } from "@/lib/types";
import { fetchSettings, saveSettings, updatePreferences } from "@/lib/api";
import { useLanguage } from "@/components/LanguageContext";

const MODEL_OPTIONS = [
  "claude-opus-4-6",
  "claude-sonnet-4-6",
  "claude-haiku-4-5-20251001",
];

export default function SettingsPage() {
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const { t, setLanguage: setGlobalLanguage } = useLanguage();

  useEffect(() => {
    fetchSettings()
      .then(setSettings)
      .catch((err: Error) => setMessage(`Error: ${err.message}`))
      .finally(() => setLoading(false));
  }, []);

  async function handleSave() {
    if (!settings) return;
    setSaving(true);
    setMessage(null);
    try {
      await saveSettings(settings);
      const lang = settings.general.language;
      if (lang === "en" || lang === "zh") setGlobalLanguage(lang);
      setMessage(`✅ ${t("settings.saved")}`);
    } catch (err) {
      setMessage(
        `❌ Failed: ${err instanceof Error ? err.message : "Unknown"}`
      );
    } finally {
      setSaving(false);
    }
  }

  async function handleUpdatePreferences() {
    setMessage(null);
    try {
      const result = await updatePreferences();
      setMessage(`🧠 ${result.changes.summary}`);
    } catch (err) {
      setMessage(
        `❌ ${err instanceof Error ? err.message : "Unknown error"}`
      );
    }
  }

  function updateDomain(name: string, field: keyof ResearchDomain, value: unknown) {
    if (!settings) return;
    setSettings({
      ...settings,
      research: {
        ...settings.research,
        research_domains: {
          ...settings.research.research_domains,
          [name]: {
            ...settings.research.research_domains[name],
            [field]: value,
          },
        },
      },
    });
  }

  function addDomain() {
    if (!settings) return;
    const name = prompt(t("settings.newDomainPrompt"));
    if (!name) return;
    setSettings({
      ...settings,
      research: {
        ...settings.research,
        research_domains: {
          ...settings.research.research_domains,
          [name]: { keywords: [], arxiv_categories: [], priority: 3 },
        },
      },
    });
  }

  function removeDomain(name: string) {
    if (!settings) return;
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { [name]: _removed, ...rest } = settings.research.research_domains;
    setSettings({
      ...settings,
      research: {
        ...settings.research,
        research_domains: rest,
      },
    });
  }

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-[var(--accent-blue)] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!settings) {
    return (
      <div className="h-full flex items-center justify-center text-[var(--accent-red)]">
        Failed to load settings
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto px-4 lg:px-6 py-4 lg:py-6 max-w-3xl mx-auto space-y-4 lg:space-y-5">
      <Section title={`🤖 ${t("settings.claudeConfig")}`} color="var(--accent-blue)">
        <p className="text-xs text-[var(--text-secondary)] mb-3">
          {t("settings.claudeConfigDesc")}
        </p>
        <Field label={t("settings.modelSelection")}>
          <select
            value={settings.claude.model}
            onChange={(e) =>
              setSettings({
                ...settings,
                claude: { ...settings.claude, model: e.target.value },
              })
            }
            className="w-full bg-[var(--bg-primary)] border border-[var(--border)] rounded px-3 py-2 text-sm lg:text-base"
          >
            {MODEL_OPTIONS.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </Field>
        <Field label={t("settings.apiKeyLabel")}>
          <input
            type="password"
            value={settings.claude.api_key}
            onChange={(e) =>
              setSettings({
                ...settings,
                claude: { ...settings.claude, api_key: e.target.value },
              })
            }
            className="w-full bg-[var(--bg-primary)] border border-[var(--border)] rounded px-3 py-2 text-sm lg:text-base"
            placeholder={t("settings.apiKeyPlaceholder")}
          />
        </Field>
      </Section>

      <Section title={`🔬 ${t("settings.researchInterests")}`} color="var(--accent-green)">
        {Object.entries(settings.research.research_domains).map(
          ([name, domain]) => (
            <div
              key={name}
              className="bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg p-3 mb-3"
            >
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-bold text-[var(--accent-blue)]">
                  {name}
                </span>
                <button
                  onClick={() => removeDomain(name)}
                  className="text-xs text-[var(--accent-red)] hover:underline"
                >
                  {t("settings.delete")}
                </button>
              </div>
              <Field label={t("settings.priority", { value: domain.priority })}>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={domain.priority}
                  onChange={(e) =>
                    updateDomain(name, "priority", parseInt(e.target.value))
                  }
                  className="w-full"
                />
              </Field>
              <Field label={t("settings.keywords")}>
                <input
                  type="text"
                  value={domain.keywords.join(", ")}
                  onChange={(e) =>
                    updateDomain(
                      name,
                      "keywords",
                      e.target.value.split(",").map((s: string) => s.trim()).filter(Boolean)
                    )
                  }
                  className="w-full bg-[var(--bg-secondary)] border border-[var(--border)] rounded px-3 py-1.5 text-xs"
                  placeholder="keyword1, keyword2, ..."
                />
              </Field>
              <Field label={t("settings.arxivCategories")}>
                <input
                  type="text"
                  value={domain.arxiv_categories.join(", ")}
                  onChange={(e) =>
                    updateDomain(
                      name,
                      "arxiv_categories",
                      e.target.value.split(",").map((s: string) => s.trim()).filter(Boolean)
                    )
                  }
                  className="w-full bg-[var(--bg-secondary)] border border-[var(--border)] rounded px-3 py-1.5 text-xs"
                  placeholder="cs.AI, cs.CV, ..."
                />
              </Field>
            </div>
          )
        )}
        <button
          onClick={addDomain}
          className="w-full py-2 border border-dashed border-[var(--border)] rounded-lg text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--accent-blue)] transition-colors"
        >
          {t("settings.addDomain")}
        </button>
      </Section>

      <Section title={`📋 ${t("settings.generalSettings")}`} color="var(--accent-orange)">
        <Field label={t("settings.language")}>
          <select
            value={settings.general.language}
            onChange={(e) =>
              setSettings({
                ...settings,
                general: { ...settings.general, language: e.target.value },
                research: { ...settings.research, language: e.target.value },
              })
            }
            className="bg-[var(--bg-primary)] border border-[var(--border)] rounded px-3 py-2 text-sm"
          >
            <option value="zh">中文</option>
            <option value="en">English</option>
          </select>
        </Field>
        <Field label="Semantic Scholar API Key">
          <input
            type="text"
            value={settings.general.semantic_scholar_api_key}
            onChange={(e) =>
              setSettings({
                ...settings,
                general: {
                  ...settings.general,
                  semantic_scholar_api_key: e.target.value,
                },
                research: {
                  ...settings.research,
                  semantic_scholar_api_key: e.target.value,
                },
              })
            }
            className="w-full bg-[var(--bg-primary)] border border-[var(--border)] rounded px-3 py-2 text-sm lg:text-base"
            placeholder={t("settings.optional")}
          />
        </Field>
      </Section>

      <Section title={`🧠 ${t("settings.preferenceUpdate")}`} color="var(--accent-purple)">
        <button
          onClick={handleUpdatePreferences}
          className="w-full py-2 bg-[var(--accent-purple)]/20 border border-[var(--accent-purple)]/50 rounded-lg text-sm text-[var(--accent-purple)] hover:bg-[var(--accent-purple)]/30 transition-colors"
        >
          🔄 {t("settings.triggerPreferenceAnalysis")}
        </button>
      </Section>

      {message && (
        <div className="text-center text-sm py-2">{message}</div>
      )}

      <button
        onClick={handleSave}
        disabled={saving}
        className="w-full py-3 bg-[var(--accent-blue)] text-[var(--bg-primary)] rounded-lg font-bold text-sm lg:text-base hover:opacity-90 transition-opacity disabled:opacity-50"
      >
        {saving ? t("settings.saving") : `💾 ${t("settings.saveSettings")}`}
      </button>

      <div className="h-4" />
    </div>
  );
}

function Section({
  title,
  color,
  children,
}: {
  title: string;
  color: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-4 lg:p-5">
      <h2
        className="font-bold text-sm lg:text-base mb-3"
        style={{ color }}
      >
        {title}
      </h2>
      {children}
    </div>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="mb-3">
      <label className="block text-xs lg:text-sm text-[var(--text-secondary)] mb-1">
        {label}
      </label>
      {children}
    </div>
  );
}

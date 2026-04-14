"use client";

import { useState, useRef, useCallback, useEffect } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type ViewMode = "diff" | "before" | "after" | "split";

interface DiffItem {
  selector: string;
  original: string;
  replacement: string;
  reason: string;
  status: string;
}

interface AdContext {
  hook: string;
  offer: string;
  audience: string;
  tone: string;
  keywords: string[];
  cta_text: string;
  visual_theme: string;
}

interface GenerateResult {
  success: boolean;
  landing_page_url: string;
  ad_context: AdContext;
  personalization_summary: string;
  changes: {
    applied: number;
    failed: number;
    diff: DiffItem[];
  };
  original_html: string;
  modified_html: string;
  meta: { title: string; description: string };
  dom_nodes_extracted: number;
}

const LOADING_STEPS = [
  { id: "scrape", label: "Scraping landing page...", icon: "🔍" },
  { id: "vision", label: "Analyzing ad creative...", icon: "👁️" },
  { id: "copy", label: "Generating personalized copy...", icon: "✍️" },
  { id: "merge", label: "Building personalized page...", icon: "🔧" },
];

export default function Home() {
  const [adImage, setAdImage] = useState<File | null>(null);
  const [adPreview, setAdPreview] = useState<string | null>(null);
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [result, setResult] = useState<GenerateResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("diff");
  const [dragOver, setDragOver] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // URL validation
  const isValidUrl = useCallback((u: string) => {
    try {
      new URL(u);
      return true;
    } catch {
      return false;
    }
  }, []);

  const canGenerate = adImage && url && isValidUrl(url) && !loading;

  // File handling
  const handleFileSelect = (file: File) => {
    if (!file.type.startsWith("image/")) {
      setError("Please upload an image file (PNG, JPG, WEBP)");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError("Image must be under 10MB");
      return;
    }
    setAdImage(file);
    setError(null);
    const reader = new FileReader();
    reader.onload = (e) => setAdPreview(e.target?.result as string);
    reader.readAsDataURL(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFileSelect(file);
  };

  const clearImage = () => {
    setAdImage(null);
    setAdPreview(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  // Generate
  const handleGenerate = async () => {
    if (!canGenerate) return;

    setLoading(true);
    setError(null);
    setResult(null);
    setLoadingStep(0);

    // Simulate step progression
    const stepInterval = setInterval(() => {
      setLoadingStep((prev) => Math.min(prev + 1, LOADING_STEPS.length - 1));
    }, 3000);

    try {
      const formData = new FormData();
      formData.append("ad_image", adImage!);
      formData.append("landing_page_url", url);

      const response = await fetch(`${API_BASE}/api/generate`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => null);
        throw new Error(
          errData?.detail || `Server error: ${response.status}`
        );
      }

      const data: GenerateResult = await response.json();
      setResult(data);
      setViewMode("diff");
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : "Something went wrong";
      setError(errorMessage);
    } finally {
      clearInterval(stepInterval);
      setLoading(false);
    }
  };

  // Write HTML to iframe
  const writeToIframe = (iframeRef: HTMLIFrameElement | null, html: string) => {
    if (!iframeRef) return;
    const doc = iframeRef.contentDocument;
    if (doc) {
      doc.open();
      doc.write(html);
      doc.close();
    }
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="header">
        <div className="logo">
          <div className="logo-icon">T</div>
          <span className="logo-text">Troopod Harmonizer</span>
          <span className="logo-badge">AI Beta</span>
        </div>
      </header>

      {/* Main content */}
      <main className="main-content">
        {/* Hero */}
        <section className="hero">
          <h1>Ad ↔ Landing Page Harmonizer</h1>
          <p>
            Upload your ad creative and enter a landing page URL. Our AI will
            personalize the page copy using CRO principles to match your ad
            — boosting conversion with message consistency.
          </p>
        </section>

        {/* Input Section */}
        <section className="input-section">
          {/* Ad Upload Card */}
          <div className="card">
            <div className="card-label">
              <span className="card-label-icon">🎨</span>
              Ad Creative
            </div>
            <div
              className={`upload-zone ${dragOver ? "drag-over" : ""} ${
                adImage ? "has-file" : ""
              }`}
              onClick={() => fileInputRef.current?.click()}
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) handleFileSelect(f);
                }}
                style={{ display: "none" }}
                id="ad-upload-input"
              />

              {adPreview ? (
                <>
                  <button
                    className="upload-clear"
                    onClick={(e) => {
                      e.stopPropagation();
                      clearImage();
                    }}
                  >
                    ✕
                  </button>
                  <img
                    src={adPreview}
                    alt="Ad preview"
                    className="upload-preview"
                  />
                  <div className="upload-file-name">
                    ✓ {adImage?.name}
                  </div>
                </>
              ) : (
                <>
                  <div className="upload-icon">📤</div>
                  <div className="upload-text">
                    Drop your ad image here or click to upload
                  </div>
                  <div className="upload-hint">
                    PNG, JPG, WEBP • Max 10MB
                  </div>
                </>
              )}
            </div>
          </div>

          {/* URL Input Card */}
          <div className="card">
            <div className="card-label">
              <span className="card-label-icon">🔗</span>
              Landing Page URL
            </div>
            <div className="url-input-wrapper">
              <span className="url-input-icon">🌐</span>
              <input
                id="url-input"
                type="url"
                className="url-input"
                placeholder="https://example.com/landing-page"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
            </div>
            {url && (
              <div
                className={`url-validation ${
                  isValidUrl(url) ? "valid" : "invalid"
                }`}
              >
                {isValidUrl(url) ? "✓ Valid URL" : "✗ Please enter a valid URL"}
              </div>
            )}
            <div
              style={{
                marginTop: 16,
                fontSize: 13,
                color: "var(--text-muted)",
                lineHeight: 1.6,
              }}
            >
              Enter the landing page URL that your ad points to. We&apos;ll scrape
              the page content and personalize it to match your ad creative.
            </div>
          </div>
        </section>

        {/* Generate Button */}
        <section className="generate-section">
          <button
            id="generate-btn"
            className={`generate-btn ${loading ? "loading" : ""}`}
            disabled={!canGenerate}
            onClick={handleGenerate}
          >
            {loading ? "Harmonizing..." : "✨ Generate Personalized Page"}
          </button>
        </section>

        {/* Loading State */}
        {loading && (
          <div className="loading-overlay">
            <div className="loading-spinner" />
            <div className="loading-steps">
              {LOADING_STEPS.map((step, i) => (
                <div
                  key={step.id}
                  className={`loading-step ${
                    i === loadingStep
                      ? "active"
                      : i < loadingStep
                      ? "done"
                      : ""
                  }`}
                >
                  <span className="loading-step-icon">
                    {i < loadingStep ? "✓" : step.icon}
                  </span>
                  {step.label}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="error-card">
            <span className="error-icon">⚠️</span>
            <div>
              <div className="error-message">{error}</div>
              <div className="error-retry">
                <button
                  className="generate-btn"
                  style={{ padding: "8px 20px", fontSize: 13 }}
                  onClick={() => setError(null)}
                >
                  Dismiss
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Results */}
        {result && (
          <section className="results-section">
            <div className="results-header">
              <h2 className="results-title">🎯 Personalization Results</h2>
              <div className="results-stats">
                <span className="stat-badge success">
                  ✓ {result.changes.applied} changes applied
                </span>
                <span className="stat-badge info">
                  📊 {result.dom_nodes_extracted} nodes extracted
                </span>
              </div>
            </div>

            {/* Ad Context */}
            <div className="ad-context-card">
              <div className="ad-context-title">
                🧠 AI-Extracted Ad Context
              </div>
              <div style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 16 }}>
                {result.personalization_summary}
              </div>
              <div className="ad-context-grid">
                <div className="ad-context-item">
                  <div className="ad-context-item-label">Hook</div>
                  <div className="ad-context-item-value">
                    {result.ad_context?.hook}
                  </div>
                </div>
                <div className="ad-context-item">
                  <div className="ad-context-item-label">Offer</div>
                  <div className="ad-context-item-value">
                    {result.ad_context?.offer}
                  </div>
                </div>
                <div className="ad-context-item">
                  <div className="ad-context-item-label">Audience</div>
                  <div className="ad-context-item-value">
                    {result.ad_context?.audience}
                  </div>
                </div>
                <div className="ad-context-item">
                  <div className="ad-context-item-label">Tone</div>
                  <div className="ad-context-item-value">
                    {result.ad_context?.tone}
                  </div>
                </div>
                <div className="ad-context-item">
                  <div className="ad-context-item-label">CTA</div>
                  <div className="ad-context-item-value">
                    {result.ad_context?.cta_text}
                  </div>
                </div>
                <div className="ad-context-item">
                  <div className="ad-context-item-label">Visual Theme</div>
                  <div className="ad-context-item-value">
                    {result.ad_context?.visual_theme}
                  </div>
                </div>
                <div className="ad-context-item" style={{ gridColumn: "1 / -1" }}>
                  <div className="ad-context-item-label">Keywords</div>
                  <div className="keywords-list">
                    {result.ad_context?.keywords?.map((kw, i) => (
                      <span key={i} className="keyword-tag">
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* View Tabs */}
            <div className="view-tabs">
              {(
                [
                  { key: "diff", label: "📋 Changes" },
                  { key: "before", label: "⬅️ Before" },
                  { key: "after", label: "➡️ After" },
                  { key: "split", label: "↔️ Split View" },
                ] as const
              ).map((tab) => (
                <button
                  key={tab.key}
                  className={`view-tab ${viewMode === tab.key ? "active" : ""}`}
                  onClick={() => setViewMode(tab.key)}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Diff View */}
            {viewMode === "diff" && (
              <div className="diff-list">
                {result.changes.diff.map((item, i) => (
                  <div key={i} className="diff-item">
                    <div className="diff-item-header">
                      <span className="diff-selector">{item.selector}</span>
                      <span
                        className={`diff-status ${item.status}`}
                      >
                        {item.status}
                      </span>
                    </div>
                    {item.reason && (
                      <div className="diff-reason">💡 {item.reason}</div>
                    )}
                    <div className="diff-content">
                      <div className="diff-block original">
                        <div className="diff-block-label">— Original</div>
                        {item.original}
                      </div>
                      <div className="diff-block replacement">
                        <div className="diff-block-label">+ Personalized</div>
                        {item.replacement}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Before View */}
            {viewMode === "before" && (
              <div className="preview-container">
                <div className="preview-toolbar">
                  <div className="preview-dots">
                    <div className="preview-dot red" />
                    <div className="preview-dot yellow" />
                    <div className="preview-dot green" />
                  </div>
                  <div className="preview-url">
                    {result.landing_page_url}
                  </div>
                  <span className="preview-label before">Original</span>
                </div>
                <iframe
                  className="preview-iframe"
                  title="Original page"
                  ref={(ref) => writeToIframe(ref, result.original_html)}
                  sandbox="allow-same-origin"
                />
              </div>
            )}

            {/* After View */}
            {viewMode === "after" && (
              <div className="preview-container">
                <div className="preview-toolbar">
                  <div className="preview-dots">
                    <div className="preview-dot red" />
                    <div className="preview-dot yellow" />
                    <div className="preview-dot green" />
                  </div>
                  <div className="preview-url">
                    {result.landing_page_url}
                  </div>
                  <span className="preview-label after">Personalized</span>
                </div>
                <iframe
                  className="preview-iframe"
                  title="Personalized page"
                  ref={(ref) => writeToIframe(ref, result.modified_html)}
                  sandbox="allow-same-origin"
                />
              </div>
            )}

            {/* Split View */}
            {viewMode === "split" && (
              <div className="preview-split">
                <div className="preview-container">
                  <div className="preview-toolbar">
                    <div className="preview-dots">
                      <div className="preview-dot red" />
                      <div className="preview-dot yellow" />
                      <div className="preview-dot green" />
                    </div>
                    <span className="preview-label before">Original</span>
                  </div>
                  <iframe
                    className="preview-iframe"
                    title="Original page"
                    ref={(ref) => writeToIframe(ref, result.original_html)}
                    sandbox="allow-same-origin"
                  />
                </div>
                <div className="preview-container">
                  <div className="preview-toolbar">
                    <div className="preview-dots">
                      <div className="preview-dot red" />
                      <div className="preview-dot yellow" />
                      <div className="preview-dot green" />
                    </div>
                    <span className="preview-label after">Personalized</span>
                  </div>
                  <iframe
                    className="preview-iframe"
                    title="Personalized page"
                    ref={(ref) => writeToIframe(ref, result.modified_html)}
                    sandbox="allow-same-origin"
                  />
                </div>
              </div>
            )}
          </section>
        )}
      </main>

      {/* Footer removed per user request */}
    </div>
  );
}

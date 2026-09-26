"use client";

import { useEffect, useState } from "react";
import { HealthCheck } from "./health-check";
import { NirmanAiChat } from "./assistant-chat";
import { apiClient } from "@/lib/api/client";

const defaultKpis = [
  { label: "Total Projects", value: "1,723", trend: "PAIMANA Corpus", tone: "up" },
  { label: "Cost Overrun", value: "+20.1%", trend: "Revised vs Original", tone: "neutral" },
  { label: "Total Expenditure", value: "₹14.7L Cr", trend: "Utilized", tone: "neutral" },
  { label: "At-Risk Projects", value: "312", trend: "Monitored", tone: "down" },
];

const fallbackProjects = [
  { rank: 1, id: "N04000077", name: "CCS INTERNATIONAL AIRPORT , LUCKNOW", state: "UTTAR PRADESH", sector: "CIVIL AVIATION", value: "₹1,383 Cr", progress: 80.6, risk: 16, status: "Low", opStatus: "IN_PROGRESS" },
  { rank: 2, id: "N04000078", name: "LEH AIRPORT", state: "JAMMU AND KASHMIR", sector: "CIVIL AVIATION", value: "₹480 Cr", progress: 62.5, risk: 45, status: "Medium", opStatus: "IN_PROGRESS" },
  { rank: 3, id: "N04000073", name: "PORTBLAIR VSI AIRPORT TERMINAL", state: "ANDAMAN AND NICOBAR", sector: "CIVIL AVIATION", value: "₹417.2 Cr", progress: 100.0, risk: 5, status: "Low", opStatus: "COMPLETED" },
  { rank: 4, id: "N24000948", name: "HUNLI-ANINI ROAD EPC", state: "ARUNACHAL PRADESH", sector: "ROADS", value: "₹568.9 Cr", progress: 100.0, risk: 5, status: "Low", opStatus: "COMPLETED" },
];

export default function Home() {
  const [activeNav, setActiveNav] = useState("Command Center");
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [projects, setProjects] = useState<any[]>(fallbackProjects);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("N04000077");
  const [projectRisk, setProjectRisk] = useState<any | null>(null);
  const [projectDrivers, setProjectDrivers] = useState<any[]>([]);
  const [projectRecs, setProjectRecs] = useState<any | null>(null);
  const [summaryData, setSummaryData] = useState<any | null>(null);
  const [stateIntel, setStateIntel] = useState<any[]>([]);
  const [sectorIntel, setSectorIntel] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [showNotifications, setShowNotifications] = useState<boolean>(false);
  const [showProfilePopover, setShowProfilePopover] = useState<boolean>(false);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [, setLoading] = useState<boolean>(true);

  async function loadInitialData() {
    setLoading(true);
    try {
      const [projRes, summaryRes, stateRes, sectorRes] = await Promise.all([
        apiClient.getProjects(25).catch(() => null),
        apiClient.getAnalyticsSummary().catch(() => null),
        apiClient.getStateIntelligence().catch(() => null),
        apiClient.getSectorIntelligence().catch(() => null),
      ]);

      if (projRes?.success && projRes?.data?.length > 0) {
        const mapped = projRes.data.map((item: any, idx: number) => {
          const progressVal = item.physical_progress != null ? Number(item.physical_progress) : null;
          const prob = item.risk_probability != null ? Number(item.risk_probability) : 0.05;
          const riskPct = Math.round(prob * 100);
          const category = item.risk_category || "LOW";
          const opStatus = item.operational_status || (progressVal !== null && progressVal >= 100 ? "COMPLETED" : "IN_PROGRESS");
          const statusText = category === "CRITICAL" ? "Critical" : category === "HIGH" ? "High" : category === "MODERATE" ? "Medium" : "Low";

          return {
            rank: idx + 1,
            id: item.project_id,
            name: item.project_name || item.project_id,
            state: item.state && item.state.trim() ? item.state : "N/A",
            sector: item.sector && item.sector.trim() ? item.sector : "N/A",
            value: item.original_cost != null ? `₹${item.original_cost} Cr` : "N/A",
            progress: progressVal,
            risk: riskPct,
            status: statusText,
            opStatus: opStatus,
          };
        });
        setProjects(mapped);

        const firstId = projRes.data[0].project_id;
        setSelectedProjectId(firstId);
        fetchProjectDetailData(firstId);
      }

      if (summaryRes?.success) setSummaryData(summaryRes.data);
      if (stateRes?.success) setStateIntel(stateRes.data);
      if (sectorRes?.success) setSectorIntel(sectorRes.data);
    } catch (err) {
      console.warn("Using fallback static project data:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadInitialData();
  }, []);

  async function handleRefreshData() {
    setIsRefreshing(true);
    await loadInitialData();
    if (selectedProjectId) {
      await fetchProjectDetailData(selectedProjectId);
    }
    setTimeout(() => setIsRefreshing(false), 600);
  }

  async function fetchProjectDetailData(projectId: string) {
    setSelectedProjectId(projectId);
    try {
      const [riskRes, driverRes, recRes] = await Promise.all([
        apiClient.getProjectRisk(projectId).catch(() => null),
        apiClient.getProjectDrivers(projectId).catch(() => null),
        apiClient.getProjectRecommendations(projectId).catch(() => null),
      ]);

      if (riskRes?.success) {
        setProjectRisk(riskRes.data);
      } else {
        setProjectRisk(null);
      }
      if (driverRes?.success) {
        setProjectDrivers(driverRes.data);
      } else {
        setProjectDrivers([]);
      }
      if (recRes?.success) {
        setProjectRecs(recRes.data);
      } else {
        setProjectRecs(null);
      }
    } catch (e) {
      console.warn("Could not fetch project risk detail:", e);
    }
  }

  const kpis = summaryData
    ? [
        { label: "Total Projects", value: summaryData.total_projects?.toLocaleString() || "1,723", trend: "PAIMANA Corpus", tone: "up" },
        { label: "Total Budget", value: `₹${(summaryData.total_original_cost_cr / 1000).toFixed(1)}k Cr`, trend: "Sanctioned", tone: "neutral" },
        { label: "Total Expenditure", value: `₹${(summaryData.total_expenditure_cr / 1000).toFixed(1)}k Cr`, trend: "Utilized", tone: "neutral" },
        { label: "At-Risk Projects", value: summaryData.at_risk_projects_count?.toString() || "312", trend: "Monitored", tone: "down" },
      ]
    : defaultKpis;

  const navItems = [
    { label: "Command Center", icon: "grid" },
    { label: "Risk Radar", icon: "shield" },
    { label: "Projects", icon: "folder" },
    { label: "State Intelligence", icon: "map" },
    { label: "Sector Intelligence", icon: "chart" },
    { label: "AI Insights", icon: "cpu" },
  ];

  function humanCategoryTitle(cat: string): string {
    switch (cat) {
      case "MILESTONE_RECOVERY":
        return "Milestone Recovery";
      case "FINANCIAL_AUDIT":
        return "Financial Review";
      case "REPORTING_COMPLIANCE":
        return "Reporting Compliance";
      case "POST_COMPLETION_AUDIT":
        return "Post-Completion Audit";
      case "ROUTINE_CLOSURE":
        return "Routine Project Closure";
      case "ROUTINE_MONITORING":
        return "Routine Monitoring";
      default:
        return cat || "Government Directive";
    }
  }

  const filteredProjects = projects.filter((p) => {
    const q = searchQuery.trim().toLowerCase();
    const matchesSearch = !q || (
      (p.name && p.name.toLowerCase().includes(q)) ||
      (p.id && p.id.toLowerCase().includes(q)) ||
      (p.state && p.state.toLowerCase().includes(q)) ||
      (p.sector && p.sector.toLowerCase().includes(q))
    );

    if (!matchesSearch) return false;

    if (statusFilter === "ACTIVE") return p.progress < 100 && p.opStatus !== "STAGNANT";
    if (statusFilter === "STAGNANT") return p.opStatus === "STAGNANT";
    if (statusFilter === "COMPLETED") return p.progress >= 100;
    if (statusFilter === "CRITICAL") return p.risk >= 75 || p.status === "Critical";
    return true;
  });

  const selectedProjectObj = projects.find((p) => p.id === selectedProjectId) || filteredProjects[0] || projects[0];

  function handleNavClick(label: string) {
    setActiveNav(label);
    setIsMobileMenuOpen(false);
  }

  return (
    <div className="app-shell">
      {/* Mobile Backdrop Overlay */}
      <div
        className={`sidebar-overlay ${isMobileMenuOpen ? "open" : ""}`}
        onClick={() => setIsMobileMenuOpen(false)}
        aria-hidden="true"
      />

      {/* Sidebar Navigation Drawer */}
      <aside className={`sidebar ${isMobileMenuOpen ? "open" : ""}`}>
        <div className="sidebar-logo">
          <div className="sidebar-brand">
            <svg viewBox="0 0 28 28" fill="none" aria-hidden="true">
              <rect width="28" height="28" rx="6" fill="var(--accent)" />
              <path d="M8 20V8l6 6 6-6v12" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <div>
              <div className="sidebar-logo-text">NIRMAN AI</div>
              <div className="sidebar-logo-sub">Govt. of India</div>
            </div>
          </div>

          <button
            type="button"
            className="sidebar-close-btn"
            onClick={() => setIsMobileMenuOpen(false)}
            aria-label="Close navigation menu"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <nav className="sidebar-nav" aria-label="Sidebar navigation">
          {navItems.map((item) => (
            <button
              key={item.label}
              type="button"
              className={`nav-item ${activeNav === item.label ? "active" : ""}`}
              onClick={() => handleNavClick(item.label)}
            >
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">NIRMAN AI v2.4.1 • Verified</div>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <button
            type="button"
            className="mobile-menu-btn"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            aria-label="Toggle navigation menu"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </button>

          <div className="topbar-title">NIRMAN AI</div>

          <div className="topbar-search">
            <input
              type="text"
              placeholder="Search projects..."
              aria-label="Global search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <div className="topbar-meta" style={{ position: "relative" }}>
            <button
              type="button"
              onClick={handleRefreshData}
              style={{
                background: "var(--surface-alt)",
                border: "1px solid var(--border-soft)",
                color: "var(--navy)",
                padding: "4px 10px",
                borderRadius: "6px",
                fontSize: "11px",
                fontWeight: 600,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "4px",
              }}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: 12, height: 12, transform: isRefreshing ? "rotate(180deg)" : "none", transition: "transform 0.4s ease" }}>
                <path d="M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
              </svg>
              <span className="refresh-btn-text">{isRefreshing ? "Refreshing..." : "Refresh"}</span>
            </button>

            <span className="topbar-date">PAIMANA Jun 2025</span>

            <div
              className="topbar-icon topbar-badge"
              aria-label="Notifications"
              onClick={() => {
                setShowNotifications(!showNotifications);
                setShowProfilePopover(false);
              }}
              style={{ cursor: "pointer" }}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.73 21a2 2 0 0 1-3.46 0" />
              </svg>
            </div>

            {showNotifications && (
              <div className="notification-popover">
                <div className="popover-header">
                  <span>System Alerts</span>
                  <span style={{ fontSize: "10px", color: "var(--accent)" }}>3 Unread</span>
                </div>
                <div className="popover-item">
                  <strong>3 Projects Stagnant</strong>
                  <small>PAIMANA June 2025 report flags progress stagnation in 3 major road corridors.</small>
                </div>
                <div className="popover-item">
                  <strong>Cost Overrun Audit Triggered</strong>
                  <small>N04000073 completed with +69.6% overrun; post-completion audit directive active.</small>
                </div>
                <div className="popover-item">
                  <strong>RF Model v1 Persisted</strong>
                  <small>RandomForest classifier validated on 8,180 canonical project-month observations.</small>
                </div>
              </div>
            )}

            <div
              className="topbar-avatar"
              onClick={() => {
                setShowProfilePopover(!showProfilePopover);
                setShowNotifications(false);
              }}
              style={{ cursor: "pointer" }}
              title="Official Profile"
            >
              AK
            </div>

            {showProfilePopover && (
              <div className="notification-popover" style={{ right: 0, width: 220 }}>
                <div className="popover-header">
                  <span>Official Profile</span>
                  <span style={{ fontSize: "10px", color: "var(--accent)" }}>Verified</span>
                </div>
                <div className="popover-item" style={{ borderBottom: "none" }}>
                  <strong>Ashok Kumar (AK)</strong>
                  <small>NIRMAN AI Administrator</small>
                  <div style={{ marginTop: "6px", fontSize: "10px", color: "var(--text-3)", fontWeight: 600 }}>
                    Status: Prototype Mode Active
                  </div>
                </div>
              </div>
            )}
          </div>
        </header>

        <div className="content">
          {/* Quick Mobile Horizontal Navigation Bar */}
          <div className="mobile-nav-scroll" aria-label="Mobile Navigation">
            {navItems.map((item) => (
              <button
                key={item.label}
                type="button"
                className={`mobile-nav-chip ${activeNav === item.label ? "active" : ""}`}
                onClick={() => setActiveNav(item.label)}
              >
                {item.label}
              </button>
            ))}
          </div>

          <div className="page-header">
            <h1>{activeNav}</h1>
            <span className="subtitle">PAIMANA real-time monitoring across {summaryData?.total_projects || 1723} projects</span>
          </div>

          {/* VIEW 1: COMMAND CENTER */}
          {activeNav === "Command Center" && (
            <div className="workspace-layout">
              <div className="main-workspace-content">
                <div className="kpi-row">
                  {kpis.map((item) => (
                    <div className="kpi-card" key={item.label}>
                      <div className="kpi-label">{item.label}</div>
                      <div className="kpi-value">{item.value}</div>
                      <div className={`kpi-trend ${item.tone}`}>{item.trend}</div>
                    </div>
                  ))}
                </div>

                <div className="ai-hero-card">
                  <div className="ai-hero-head">
                    <div className="ai-hero-title">
                      <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
                        <circle cx="8" cy="8" r="6" /><line x1="8" y1="5" x2="8" y2="8" /><line x1="8" y1="8" x2="10.5" y2="10" />
                      </svg>
                      AI Model Risk Evaluation & Interventions
                    </div>
                    <span>RandomForest Classifier • PAIMANA</span>
                  </div>

                  <HealthCheck />

                  {projectRisk ? (
                    <div className="risk-callout">
                      <div className={`risk-dot ${projectRisk.risk_category?.toLowerCase() || "high"}`} />
                      <div style={{ width: "100%" }}>
                        <div className="risk-project-header">
                          <div className="risk-project-name">
                            {selectedProjectObj?.name} <code className="risk-proj-id">{projectRisk.project_id}</code>
                          </div>
                          <div className="risk-badges-row">
                            <span className={`status-badge ${projectRisk.operational_status === "COMPLETED" ? "completed" : projectRisk.operational_status === "STAGNANT" ? "stagnant" : "high"}`}>
                              <span className={`status-dot ${projectRisk.operational_status === "COMPLETED" ? "completed" : projectRisk.operational_status === "STAGNANT" ? "stagnant" : "high"}`} />
                              {projectRisk.operational_status || "IN_PROGRESS"}
                            </span>
                            <span className={`status-badge ${projectRisk.risk_category?.toLowerCase() || "high"}`}>
                              Predictive Risk: {projectRisk.risk_category} ({(projectRisk.risk_probability * 100).toFixed(1)}%)
                            </span>
                          </div>
                        </div>

                        <div style={{ fontSize: "0.8rem", color: "var(--text-3)", marginTop: "0.4rem" }}>
                          Model: <code>{projectRisk.model_version}</code> • Cutoff: {projectRisk.data_cutoff}
                        </div>

                        <div className="risk-callout-grid">
                          {/* DRIVERS COLUMN */}
                          <div className="risk-column-card">
                            <div className="risk-column-title">
                              Top SHAP Risk Drivers:
                            </div>
                            {projectDrivers.length > 0 ? (
                              <ul style={{ margin: "0.5rem 0 0 0", paddingLeft: "1.1rem", fontSize: "0.85rem", lineHeight: 1.5 }}>
                                {projectDrivers.map((d: any) => (
                                  <li key={d.feature_name} style={{ marginBottom: "0.35rem" }}>
                                    <strong>{d.feature_name}</strong> ({d.feature_value}): {d.description}
                                  </li>
                                ))}
                              </ul>
                            ) : (
                              <div style={{ fontSize: "0.85rem", color: "var(--text-3)", marginTop: "0.4rem" }}>
                                No critical delay drivers detected for this period.
                              </div>
                            )}
                          </div>

                          {/* RECOMMENDATIONS COLUMN */}
                          <div className="risk-column-card">
                            <div className="risk-column-title">
                              Government Interventions:
                            </div>
                            {projectRecs?.recommendations?.length > 0 ? (
                              <div className="rec-grid">
                                {projectRecs.recommendations.map((r: any, idx: number) => (
                                  <div key={idx} className="rec-card">
                                    <div className="rec-header">
                                      <span className="rec-cat">{humanCategoryTitle(r.category)}</span>
                                      <span className={`status-badge ${r.priority === "HIGH" ? "critical" : r.priority === "MEDIUM" ? "high" : "completed"}`}>
                                        {r.priority}
                                      </span>
                                    </div>
                                    <div className="rec-body">
                                      <div className="rec-field">
                                        <span className="rec-field-label">Action:</span> {r.action}
                                      </div>
                                      <div className="rec-field">
                                        <span className="rec-field-label">Reason:</span> {r.rationale}
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div style={{ fontSize: "0.85rem", color: "var(--text-3)", marginTop: "0.4rem" }}>
                                No intervention required. Routine monthly monitoring active.
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="risk-callout" style={{ marginTop: "1rem" }}>
                      <div className="risk-dot high" />
                      <div>Loading PAIMANA risk analysis...</div>
                    </div>
                  )}
                </div>

                {/* MONITORED PROJECTS TABLE */}
                <div className="table-panel">
                  <div className="table-header">
                    <div>
                      <div className="table-title" style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                        <span>PAIMANA Monitored Projects</span>
                        <span className="mobile-scroll-hint" style={{ fontSize: "10px", color: "var(--text-3)", fontWeight: "normal" }}>(Scroll horizontally &rarr;)</span>
                      </div>
                      <div style={{ display: "flex", gap: "6px", marginTop: "6px", flexWrap: "wrap" }}>
                        {["ALL", "ACTIVE", "CRITICAL", "STAGNANT", "COMPLETED"].map((f) => (
                          <button
                            key={f}
                            type="button"
                            onClick={() => setStatusFilter(f)}
                            style={{
                              background: statusFilter === f ? "var(--navy)" : "var(--surface-alt)",
                              color: statusFilter === f ? "#fff" : "var(--text-2)",
                              border: "1px solid var(--border-soft)",
                              borderRadius: "4px",
                              padding: "3px 8px",
                              fontSize: "10px",
                              fontWeight: 600,
                              cursor: "pointer",
                            }}
                          >
                            {f}
                          </button>
                        ))}
                      </div>
                    </div>
                    <div className="table-badge">{filteredProjects.length} Projects</div>
                  </div>
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Rank</th>
                          <th>ID</th>
                          <th>Project Name</th>
                          <th>State</th>
                          <th>Sanctioned Budget</th>
                          <th>Physical Progress</th>
                          <th>Risk Score</th>
                          <th>Operational Status</th>
                          <th>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredProjects.map((row) => (
                          <tr
                            key={row.id || row.name}
                            onClick={() => fetchProjectDetailData(row.id)}
                            style={{
                              cursor: "pointer",
                              background: selectedProjectId === row.id ? "var(--accent-soft)" : "transparent",
                            }}
                          >
                            <td className="rank">{row.rank}</td>
                            <td><code>{row.id}</code></td>
                            <td className="project-name">{row.name}</td>
                            <td>{row.state}</td>
                            <td className="project-value">{row.value}</td>
                            <td className="progress-cell">
                              {row.progress !== null && row.progress !== undefined ? (
                                <>
                                  <span className="progress-mini"><span className="progress-mini-fill" style={{ width: `${Math.min(100, row.progress)}%` }} /></span>
                                  <span className="progress-pct">{row.progress}%</span>
                                </>
                              ) : (
                                <span className="progress-pct" style={{ color: "var(--text-3)" }}>N/A</span>
                              )}
                            </td>
                            <td className={`risk-score ${row.risk >= 80 ? "critical" : row.risk >= 60 ? "high" : "medium"}`}>{row.risk}</td>
                            <td>
                              <span className={`status-badge ${row.opStatus === "COMPLETED" ? "completed" : row.opStatus === "STAGNANT" ? "stagnant" : "high"}`}>
                                <span className={`status-dot ${row.opStatus === "COMPLETED" ? "completed" : row.opStatus === "STAGNANT" ? "stagnant" : "high"}`} />
                                {row.opStatus || "IN_PROGRESS"}
                              </span>
                            </td>
                            <td>
                              <button
                                type="button"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  fetchProjectDetailData(row.id);
                                }}
                                style={{
                                  background: selectedProjectId === row.id ? "var(--navy)" : "var(--accent)",
                                  color: "#fff",
                                  border: "none",
                                  padding: "4px 10px",
                                  borderRadius: "4px",
                                  cursor: "pointer",
                                  fontSize: "0.75rem",
                                  fontWeight: 600,
                                }}
                              >
                                {selectedProjectId === row.id ? "Selected" : "Inspect"}
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>

              {/* RIGHT SIDEBAR ASSISTANT PANEL */}
              <NirmanAiChat
                selectedProject={selectedProjectObj}
                projectRisk={projectRisk}
                projectDrivers={projectDrivers}
                projectRecs={projectRecs}
                onSelectView={setActiveNav}
              />
            </div>
          )}

          {/* VIEW 2: RISK RADAR */}
          {activeNav === "Risk Radar" && (
            <div className="table-panel">
              <div className="table-header">
                <div className="table-title">Infrastructure Risk Radar — High Probability Risk Projects</div>
                <div className="table-badge">Filtered View</div>
              </div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Project ID</th>
                      <th>Project Name</th>
                      <th>State</th>
                      <th>Sector</th>
                      <th>Physical Progress</th>
                      <th>Predicted Risk Level</th>
                      <th>Action Required</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredProjects.map((p) => (
                      <tr
                        key={p.id}
                        onClick={() => {
                          fetchProjectDetailData(p.id);
                          setActiveNav("Command Center");
                        }}
                        style={{ cursor: "pointer", background: selectedProjectId === p.id ? "var(--accent-soft)" : "transparent" }}
                      >
                        <td><code>{p.id}</code></td>
                        <td className="project-name">{p.name}</td>
                        <td>{p.state}</td>
                        <td>{p.sector}</td>
                        <td>{p.progress !== null && p.progress !== undefined ? `${p.progress}%` : "N/A"}</td>
                        <td>
                          <span className={`status-badge ${p.opStatus === "COMPLETED" ? "completed" : p.status === "Critical" ? "critical" : p.status === "High" ? "high" : "medium"}`}>
                            {p.opStatus === "COMPLETED" ? "COMPLETED (LOW RISK)" : `Predictive Risk: ${p.status} (${p.risk}%)`}
                          </span>
                        </td>
                        <td>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              fetchProjectDetailData(p.id);
                              setActiveNav("Command Center");
                            }}
                            style={{ background: "var(--accent)", color: "#fff", border: "none", padding: "4px 10px", borderRadius: "4px", cursor: "pointer", fontSize: "0.75rem", fontWeight: 600 }}
                          >
                            Inspect Drivers
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* VIEW 3: PROJECTS / PROJECT DETAIL */}
          {activeNav === "Projects" && (
            <div className="projects-split-view">
              <div className="table-panel">
                <div className="table-header">
                  <div className="table-title">Select Monitored Project</div>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>State</th>
                        <th>Progress</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredProjects.map((p) => (
                        <tr
                          key={p.id}
                          onClick={() => fetchProjectDetailData(p.id)}
                          style={{ cursor: "pointer", background: selectedProjectId === p.id ? "var(--accent-soft)" : "transparent" }}
                        >
                          <td><code>{p.id}</code></td>
                          <td className="project-name">{p.name}</td>
                          <td>{p.state}</td>
                          <td>{p.progress !== null && p.progress !== undefined ? `${p.progress}%` : "N/A"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="table-panel" style={{ padding: "1.25rem" }}>
                <h3 style={{ marginTop: 0, color: "var(--navy)" }}>Project Detail: {selectedProjectObj?.name}</h3>
                <div style={{ fontSize: "0.85rem", lineHeight: 1.8 }}>
                  <div><strong>Project ID:</strong> <code>{selectedProjectObj?.id}</code></div>
                  <div><strong>State:</strong> {selectedProjectObj?.state}</div>
                  <div><strong>Sector:</strong> {selectedProjectObj?.sector}</div>
                  <div><strong>Sanctioned Budget:</strong> {selectedProjectObj?.value}</div>
                  <div><strong>Physical Progress:</strong> {selectedProjectObj?.progress !== null && selectedProjectObj?.progress !== undefined ? `${selectedProjectObj?.progress}%` : "N/A"}</div>
                </div>

                {projectRisk && (
                  <div style={{ marginTop: "1rem", borderTop: "1px solid var(--border-soft)", paddingTop: "1rem" }}>
                    <h4 style={{ marginTop: 0, color: "var(--navy)" }}>Model Risk Assessment</h4>
                    <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", margin: "8px 0" }}>
                      <span className={`status-badge ${projectRisk.operational_status === "COMPLETED" ? "completed" : projectRisk.operational_status === "STAGNANT" ? "stagnant" : "high"}`}>
                        Operational Status: {projectRisk.operational_status || "IN_PROGRESS"}
                      </span>
                      <span className={`status-badge ${projectRisk.risk_category?.toLowerCase() || "high"}`}>
                        Predictive Risk: {projectRisk.risk_category} ({(projectRisk.risk_probability * 100).toFixed(1)}%)
                      </span>
                    </div>

                    <h5 style={{ marginTop: "1rem", marginBottom: "0.4rem", color: "var(--navy)" }}>Top SHAP Model Feature Contributions:</h5>
                    <ul style={{ paddingLeft: "1.2rem", fontSize: "0.85rem", lineHeight: 1.5 }}>
                      {projectDrivers.map((d: any) => (
                        <li key={d.feature_name} style={{ marginBottom: "4px" }}><strong>{d.feature_name}</strong> ({d.feature_value}): {d.description}</li>
                      ))}
                    </ul>

                    <h5 style={{ marginTop: "1rem", marginBottom: "0.4rem", color: "var(--navy)" }}>Government Interventions:</h5>
                    {projectRecs?.recommendations?.length > 0 ? (
                      <div className="rec-grid">
                        {projectRecs.recommendations.map((r: any, idx: number) => (
                          <div key={idx} className="rec-card">
                            <div className="rec-header">
                              <span className="rec-cat">{humanCategoryTitle(r.category)}</span>
                              <span className={`status-badge ${r.priority === "HIGH" ? "critical" : r.priority === "MEDIUM" ? "high" : "completed"}`}>
                                {r.priority}
                              </span>
                            </div>
                            <div className="rec-body">
                              <div className="rec-field">
                                <span className="rec-field-label">Action:</span> {r.action}
                              </div>
                              <div className="rec-field">
                                <span className="rec-field-label">Reason:</span> {r.rationale}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div style={{ fontSize: "0.85rem", color: "var(--text-3)" }}>No interventions required. Routine monitoring active.</div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* VIEW 4: STATE INTELLIGENCE */}
          {activeNav === "State Intelligence" && (
            <div className="table-panel">
              <div className="table-header">
                <div className="table-title">State & Union Territory Infrastructure Aggregates</div>
                <div className="table-badge">{stateIntel.length} States</div>
              </div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>State / UT</th>
                      <th>Monitored Projects</th>
                      <th>Total Sanctioned Budget</th>
                      <th>Average Physical Progress</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stateIntel.map((row) => (
                      <tr key={row.state}>
                        <td className="project-name">{row.state}</td>
                        <td>{row.project_count}</td>
                        <td>₹{row.total_original_cost_cr.toLocaleString()} Cr</td>
                        <td>
                          <span className="progress-pct">{row.avg_physical_progress_pct}%</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* VIEW 5: SECTOR INTELLIGENCE */}
          {activeNav === "Sector Intelligence" && (
            <div className="table-panel">
              <div className="table-header">
                <div className="table-title">Sectoral Infrastructure Aggregates</div>
                <div className="table-badge">{sectorIntel.length} Sectors</div>
              </div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Sector</th>
                      <th>Monitored Projects</th>
                      <th>Total Sanctioned Budget</th>
                      <th>Average Physical Progress</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sectorIntel.map((row) => (
                      <tr key={row.sector}>
                        <td className="project-name">{row.sector}</td>
                        <td>{row.project_count}</td>
                        <td>₹{row.total_original_cost_cr.toLocaleString()} Cr</td>
                        <td>
                          <span className="progress-pct">{row.avg_physical_progress_pct}%</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* VIEW 6: AI INSIGHTS */}
          {activeNav === "AI Insights" && (
            <div className="table-panel" style={{ padding: "1.5rem" }}>
              <h2 style={{ color: "var(--navy)", marginTop: 0 }}>NIRMAN AI Intelligence & Model Inspector</h2>
              <p style={{ fontSize: "0.9rem", color: "var(--text-3)" }}>
                Evaluating RandomForest classifier predictions, SHAP feature drivers, and transparent rule-engine interventions against PAIMANA ground truth.
              </p>
              <div style={{ marginTop: "1rem", background: "var(--surface-alt)", padding: "1rem", borderRadius: "8px", border: "1px solid var(--border-soft)" }}>
                <h4 style={{ margin: "0 0 8px 0", color: "var(--navy)" }}>Active Model Architecture:</h4>
                <ul style={{ fontSize: "0.85rem", lineHeight: 1.8, margin: 0, paddingLeft: "1.2rem" }}>
                  <li><strong>Classifier:</strong> RandomForest (200 estimators, max_depth=6)</li>
                  <li><strong>Feature Set:</strong> <code>paimana-temporal-v1</code> (12 safe historical features)</li>
                  <li><strong>Model Validation F1:</strong> 0.810 (ROC-AUC: 0.859, PR-AUC: 0.869)</li>
                  <li><strong>Recommendation Engine:</strong> <code>PROTOTYPE_RULE_ENGINE</code></li>
                </ul>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

"use client";

import React, { useState, useEffect, useRef } from "react";

interface AssistantChatProps {
  selectedProject: any | null;
  projectRisk: any | null;
  projectDrivers: any[];
  projectRecs: any | null;
  onSelectView?: (view: string) => void;
}

interface Message {
  id: string;
  sender: "user" | "assistant";
  text: string;
  timestamp: string;
  evidence?: string[];
  actions?: string[];
}

export function NirmanAiChat({
  selectedProject,
  projectRisk,
  projectDrivers,
  projectRecs,
}: AssistantChatProps) {
  const [inputQuery, setInputQuery] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const chatBodyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (selectedProject) {
      setMessages([
        {
          id: "init-1",
          sender: "assistant",
          text: `Selected Context: **${selectedProject.name}** (\`${selectedProject.id}\`). Ask NIRMAN AI about risk drivers, status, or intervention directives.`,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } else {
      setMessages([
        {
          id: "init-0",
          sender: "assistant",
          text: "Select a project to ask NIRMAN AI about its risk, progress, financials, or recommended actions.",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    }
  }, [selectedProject?.id]);

  useEffect(() => {
    if (chatBodyRef.current) {
      chatBodyRef.current.scrollTop = chatBodyRef.current.scrollHeight;
    }
  }, [messages]);

  const quickPrompts = [
    "Why is this risky?",
    "Top risk drivers",
    "What should we do?",
    "Current status",
    "Cost position",
  ];

  function handleSend(queryText?: string) {
    const text = (queryText || inputQuery).trim();
    if (!text) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      sender: "user",
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    const botResponse = generateDecisionResponse(text);
    const botMsg: Message = {
      id: `bot-${Date.now()}`,
      sender: "assistant",
      text: botResponse.text,
      evidence: botResponse.evidence,
      actions: botResponse.actions,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg, botMsg]);
    if (!queryText) setInputQuery("");
  }

  function generateDecisionResponse(query: string): { text: string; evidence?: string[]; actions?: string[] } {
    if (!selectedProject) {
      return {
        text: "Select a project from the command center table to analyze its risk factors.",
      };
    }

    const q = query.toLowerCase();
    const projName = selectedProject.name || selectedProject.id;
    const projId = selectedProject.id;
    const progress = projectRisk?.metrics?.physical_progress_pct ?? selectedProject.progress ?? 0;
    const riskCategory = projectRisk?.risk_category || selectedProject.status || "UNKNOWN";
    const riskProb = projectRisk?.risk_probability ? (projectRisk.risk_probability * 100).toFixed(1) : selectedProject.risk;
    const opStatus = projectRisk?.operational_status || selectedProject.opStatus || (progress >= 100 ? "COMPLETED" : "IN_PROGRESS");
    const overrun = projectRisk?.metrics?.cost_overrun_pct ?? 0;
    const stagnantMonths = projectRisk?.metrics?.stagnant_months_3m ?? 0;
    const reportingGap = projectRisk?.metrics?.reporting_gap_months ?? 0;
    const recList = projectRecs?.recommendations || [];

    // INTENT 1: Why is this project risky?
    if (q.includes("why") || q.includes("risky") || q.includes("risk")) {
      const evidenceList: string[] = [
        `Physical Progress: ${progress}% (${opStatus})`,
        `Cost Overrun Exposure: ${overrun > 0 ? `+${overrun}% budget escalation` : "0% (Within sanctioned budget)"}`,
      ];

      if (stagnantMonths > 0) {
        evidenceList.push(`Progress Stagnation: Stagnant for ${stagnantMonths} of past 3 reporting periods.`);
      }
      if (reportingGap > 0) {
        evidenceList.push(`Reporting Compliance Gap: ${reportingGap} month submission delay detected.`);
      }
      if (projectDrivers.length > 0) {
        projectDrivers.forEach((d: any) => {
          evidenceList.push(`Model Driver [${d.feature_name}]: ${d.description}`);
        });
      }

      const actionList = recList.length > 0
        ? recList.map((r: any) => `[${r.priority}] ${humanCategoryTitle(r.category)}: ${r.action}`)
        : ["Maintain routine monthly PAIMANA progress monitoring."];

      return {
        text: `Project **${projName}** (\`${projId}\`) is currently assessed at **${riskCategory}** implementation risk (${riskProb}% probability) with Operational Status **${opStatus}**.`,
        evidence: evidenceList,
        actions: actionList,
      };
    }

    // INTENT 2: Top risk drivers
    if (q.includes("driver") || q.includes("shap") || q.includes("factor") || q.includes("top")) {
      if (projectDrivers.length > 0) {
        const driversList = projectDrivers.map(
          (d: any) => `Rank ${d.rank}: ${d.feature_name} (${d.feature_value}) — ${d.description}`
        );
        return {
          text: `Top SHAP model feature contributions for **${projName}**:`,
          evidence: driversList,
          actions: recList.map((r: any) => `${humanCategoryTitle(r.category)}: ${r.action}`),
        };
      }
      return {
        text: `No critical risk drivers detected for **${projName}**. Progress is tracking normally at ${progress}%.`,
        evidence: [`Physical progress: ${progress}%`, `Cost overrun: ${overrun}%`],
        actions: ["Continue routine monthly PAIMANA progress monitoring."],
      };
    }

    // INTENT 3: What should we do? / Recommended action
    if (q.includes("action") || q.includes("do") || q.includes("recommend") || q.includes("should")) {
      if (recList.length > 0) {
        const actionBullets = recList.map(
          (r: any) => `[${r.priority} PRIORITY] ${humanCategoryTitle(r.category)}: ${r.action} (Reason: ${r.rationale})`
        );
        return {
          text: `Recommended government directives for **${projName}**:`,
          actions: actionBullets,
          evidence: [
            `Operational Status: ${opStatus}`,
            `Predictive Risk: ${riskCategory} (${riskProb}%)`,
            `Physical Progress: ${progress}%`,
          ],
        };
      }
      return {
        text: `No emergency interventions required for **${projName}**.`,
        evidence: [`Project progress tracking at ${progress}% within sanctioned budget.`],
        actions: ["Maintain routine monthly PAIMANA progress monitoring."],
      };
    }

    // INTENT 4: Current status / Progress
    if (q.includes("status") || q.includes("progress") || q.includes("period")) {
      return {
        text: `Current status summary for **${projName}**:`,
        evidence: [
          `Operational Status: ${opStatus}`,
          `Physical Progress: ${progress}%`,
          `PAIMANA Data Cutoff: Jun 2025`,
          `Predictive Implementation Risk: ${riskCategory} (${riskProb}%)`,
        ],
        actions: recList.slice(0, 2).map((r: any) => `${humanCategoryTitle(r.category)}: ${r.action}`),
      };
    }

    // INTENT 5: Cost / Budget / Financials
    if (q.includes("cost") || q.includes("budget") || q.includes("expenditure") || q.includes("financial")) {
      const orig = projectRisk?.metrics?.original_cost_cr || selectedProject.value || "N/A";
      const rev = projectRisk?.metrics?.revised_cost_cr || "N/A";
      return {
        text: `Financial position for **${projName}**:`,
        evidence: [
          `Original Sanctioned Budget: ₹${orig} Cr`,
          `Revised Cost Estimate: ₹${rev} Cr`,
          `Cost Overrun Variance: ${overrun > 0 ? `+${overrun}% escalation` : "0% (On Budget)"}`,
          `Physical Progress Utilized: ${progress}%`,
        ],
        actions: overrun > 5.0
          ? ["Trigger mandatory financial review and revised estimate audit by MoF committee."]
          : ["Maintain routine financial expenditure reconciliation."],
      };
    }

    // Default response fallback
    return {
      text: `Decision support summary for **${projName}** (\`${projId}\`):`,
      evidence: [
        `Operational Status: ${opStatus}`,
        `Predictive Risk: ${riskCategory} (${riskProb}%)`,
        `Physical Progress: ${progress}%`,
        `Cost Overrun: ${overrun > 0 ? `+${overrun}%` : "0%"}`,
      ],
      actions: recList.length > 0
        ? recList.map((r: any) => `${humanCategoryTitle(r.category)}: ${r.action}`)
        : ["Maintain routine monthly PAIMANA progress monitoring."],
    };
  }

  const opStatus = projectRisk?.operational_status || selectedProject?.opStatus || (selectedProject?.progress >= 100 ? "COMPLETED" : "IN_PROGRESS");
  const riskCat = projectRisk?.risk_category || selectedProject?.status || "LOW";
  const riskPct = projectRisk?.risk_probability ? (projectRisk.risk_probability * 100).toFixed(1) : selectedProject?.risk || "5";

  return (
    <div className="right-assistant-panel">
      <div className="assistant-card-header">
        <div className="assistant-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true" style={{ width: 16, height: 16, color: "var(--accent-light)" }}>
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
          NIRMAN AI ASSISTANT
        </div>
        <span className="assistant-subtitle">Government Decision Support</span>
      </div>

      {selectedProject && (
        <div className="assistant-context-box">
          <div className="context-proj-name">{selectedProject.name}</div>
          <div className="context-proj-id">ID: <code>{selectedProject.id}</code></div>
          <div className="context-badges-row">
            <span className={`status-badge ${opStatus === "COMPLETED" ? "completed" : opStatus === "STAGNANT" ? "stagnant" : "high"}`}>
              {opStatus}
            </span>
            <span className={`status-badge ${riskCat.toLowerCase()}`}>
              Risk: {riskCat} ({riskPct}%)
            </span>
          </div>
        </div>
      )}

      <div className="assistant-chat-body" ref={chatBodyRef}>
        {messages.map((m) => (
          <div key={m.id} className={`assistant-msg ${m.sender}`}>
            <div className="assistant-msg-meta">
              <span>{m.sender === "assistant" ? "NIRMAN AI" : "Official"}</span>
              <span className="msg-time">{m.timestamp}</span>
            </div>
            <div className="assistant-msg-content">
              <p dangerouslySetInnerHTML={{ __html: formatMarkdown(m.text) }} />

              {m.evidence && m.evidence.length > 0 && (
                <div className="msg-section">
                  <div className="msg-section-title">Key Evidence & Metrics:</div>
                  <ul className="msg-bullets">
                    {m.evidence.map((ev, idx) => (
                      <li key={idx} dangerouslySetInnerHTML={{ __html: formatMarkdown(ev) }} />
                    ))}
                  </ul>
                </div>
              )}

              {m.actions && m.actions.length > 0 && (
                <div className="msg-section">
                  <div className="msg-section-title">Recommended Directives:</div>
                  <ul className="msg-bullets actions">
                    {m.actions.map((act, idx) => (
                      <li key={idx} dangerouslySetInnerHTML={{ __html: formatMarkdown(act) }} />
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="assistant-quick-prompts">
        {quickPrompts.map((prompt) => (
          <button
            key={prompt}
            type="button"
            className="quick-chip"
            onClick={() => handleSend(prompt)}
            disabled={!selectedProject}
          >
            {prompt}
          </button>
        ))}
      </div>

      <form
        className="assistant-input-row"
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
      >
        <input
          type="text"
          placeholder={selectedProject ? `Ask about ${selectedProject.name}...` : "Select a project to enable AI..."}
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          disabled={!selectedProject}
        />
        <button type="submit" className="assistant-send-btn" disabled={!selectedProject || !inputQuery.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}

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
      return cat || "Government Action";
  }
}

function formatMarkdown(str: string): string {
  if (!str) return "";
  return str
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/`(.*?)`/g, "<code>$1</code>");
}

"use client";

import React, { useState, useEffect, useRef } from "react";
import { apiClient } from "@/lib/api/client";

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
  source?: string;
  model?: string;
}

export function NirmanAiChat({
  selectedProject,
  projectRisk,
  projectDrivers = [],
  projectRecs = null,
}: AssistantChatProps) {
  const [inputQuery, setInputQuery] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
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
  }, [messages, isLoading]);

  const quickPrompts = [
    "Why is this risky?",
    "Top risk drivers",
    "What should we do?",
    "Current status",
    "Cost position",
  ];

  async function handleSend(queryText?: string) {
    const text = (queryText || inputQuery).trim();
    if (!text || isLoading) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      sender: "user",
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!queryText) setInputQuery("");
    setIsLoading(true);

    let hasResponded = false;

    const generateLocalRag = (): string => {
      if (!selectedProject) {
        return (
          "**NIRMAN AI Assistant (PAIMANA Grounded Retrieval)**\n\n" +
          "Please select a project from the Monitored Projects list to analyze risk drivers, cost variance, physical progress, and government interventions."
        );
      }

      const pId = selectedProject.id || "N/A";
      const pName = selectedProject.name || "Selected Project";
      const state = selectedProject.state || "N/A";
      const sector = selectedProject.sector || "N/A";
      const opStatus = projectRisk?.operational_status || selectedProject.opStatus || (selectedProject.progress >= 100 ? "COMPLETED" : "IN_PROGRESS");
      const riskCat = projectRisk?.risk_category || selectedProject.status || "LOW";
      const riskPct = projectRisk?.risk_probability ? `${(projectRisk.risk_probability * 100).toFixed(1)}%` : `${selectedProject.risk || 5}%`;

      const qLower = text.toLowerCase();

      if (qLower.includes("why") || qLower.includes("risk") || qLower.includes("cause") || qLower.includes("reason")) {
        let lines = [
          `**Risk Analysis for ${pName} (\`${pId}\`)**\n`,
          `Assessed Risk Level: **${riskCat} RISK** (${riskPct} risk probability) | Operational Status: **${opStatus}**\n`,
          `**Key Risk Drivers (SHAP Feature Contributions):**`
        ];
        if (projectDrivers && projectDrivers.length > 0) {
          projectDrivers.slice(0, 4).forEach((d) => {
            lines.push(`• **${d.feature_name}** (${d.feature_value}): ${d.description}`);
          });
        } else {
          lines.push(`• Revised cost ratio exceeding original sanctioned budget.`);
          lines.push(`• Physical progress trajectory delay relative to project timeline.`);
        }
        lines.push(`\n**Source**\nPAIMANA Grounded Retrieval • Infrastructure Risk Model`);
        return lines.join("\n");
      } else if (qLower.includes("do") || qLower.includes("recommend") || qLower.includes("action") || qLower.includes("intervention")) {
        let lines = [
          `**Recommended Government Interventions for ${pName} (\`${pId}\`)**\n`,
          `Current Risk Status: **${riskCat}** | Operational Status: **${opStatus}**\n`,
          `**Action Plan Directives:**`
        ];
        if (projectRecs?.recommendations && projectRecs.recommendations.length > 0) {
          projectRecs.recommendations.slice(0, 3).forEach((r: any) => {
            lines.push(`• **[${r.priority || "HIGH"} PRIORITY] ${r.action}**\n  *Reason:* ${r.reason || "Standard monitoring protocol"}`);
          });
        } else {
          lines.push(`• **Financial Audit**: Review cumulative expenditure vs sanctioned budget.`);
          lines.push(`• **Site Inspection**: Verify physical progress milestones on ground.`);
        }
        lines.push(`\n**Source**\nNIRMAN Government Decision Engine`);
        return lines.join("\n");
      } else if (qLower.includes("cost") || qLower.includes("budget") || qLower.includes("financial") || qLower.includes("expenditure")) {
        const origCost = selectedProject.originalCost || selectedProject.cost || "N/A";
        const revCost = selectedProject.revisedCost || origCost;
        const exp = selectedProject.expenditure || "N/A";
        return [
          `**Financial Position for ${pName} (\`${pId}\`)**\n`,
          `• **State / UT:** ${state}`,
          `• **Sector:** ${sector}`,
          `• **Sanctioned Cost:** ₹${origCost} Cr`,
          `• **Revised Cost:** ₹${revCost} Cr`,
          `• **Expenditure to Date:** ₹${exp} Cr\n`,
          `**Financial Status:** Under continuous PAIMANA ledger monitoring. Risk category: **${riskCat}**.`,
          `\n**Source**\nPAIMANA Monitored Financial Ledger`
        ].join("\n");
      } else {
        return [
          `**Project Context Summary: ${pName} (\`${pId}\`)**\n`,
          `• **State:** ${state} | **Sector:** ${sector}`,
          `• **Operational Status:** ${opStatus}`,
          `• **Risk Category:** ${riskCat} (${riskPct})`,
          `\n**Operational Insights:**`,
          `Project metrics are monitored via MoSPI / DIID integrated database.`,
          `\n**Source**\nPAIMANA Grounded Retrieval System`
        ].join("\n");
      }
    };

    // Client-side exact 2000ms failover timer
    const failoverTimer = setTimeout(() => {
      if (!hasResponded) {
        hasResponded = true;
        setIsLoading(false);
        const ragText = generateLocalRag();
        const botMsg: Message = {
          id: `bot-rag-${Date.now()}`,
          sender: "assistant",
          text: ragText,
          source: "paimana_rag",
          model: "PAIMANA Grounded Retrieval",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        };
        setMessages((prev) => [...prev, botMsg]);
      }
    }, 2000);

    try {
      const res = await apiClient.postAssistantChat(text, selectedProject?.id);
      if (!hasResponded) {
        clearTimeout(failoverTimer);
        hasResponded = true;
        setIsLoading(false);
        if (res?.success && res?.data?.text) {
          const botMsg: Message = {
            id: `bot-${Date.now()}`,
            sender: "assistant",
            text: res.data.text,
            source: res.data.source,
            model: res.data.model,
            timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          };
          setMessages((prev) => [...prev, botMsg]);
        } else {
          // Fallback if res is not structured
          const ragText = generateLocalRag();
          const botMsg: Message = {
            id: `bot-rag-${Date.now()}`,
            sender: "assistant",
            text: ragText,
            source: "paimana_rag",
            model: "PAIMANA Grounded Retrieval",
            timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          };
          setMessages((prev) => [...prev, botMsg]);
        }
      }
    } catch (err) {
      if (!hasResponded) {
        clearTimeout(failoverTimer);
        hasResponded = true;
        setIsLoading(false);
        console.warn("Groq request failed, invoking instant RAG failover:", err);
        const ragText = generateLocalRag();
        const botMsg: Message = {
          id: `bot-rag-${Date.now()}`,
          sender: "assistant",
          text: ragText,
          source: "paimana_rag",
          model: "PAIMANA Grounded Retrieval",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        };
        setMessages((prev) => [...prev, botMsg]);
      }
    }
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
        <span className="assistant-subtitle">Government Decision Support • Groq LLM</span>
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
              <SafeFormattedText content={m.text} />
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="assistant-msg assistant typing">
            <div className="assistant-msg-meta">
              <span>NIRMAN AI</span>
              <span className="msg-time">Thinking...</span>
            </div>
            <div className="assistant-msg-content" style={{ display: "flex", gap: "6px", alignItems: "center", padding: "8px 12px" }}>
              <span className="typing-dot" style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--accent)", animation: "pulse 1s infinite alternate" }} />
              <span className="typing-dot" style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--accent)", animation: "pulse 1s infinite alternate 0.2s" }} />
              <span className="typing-dot" style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--accent)", animation: "pulse 1s infinite alternate 0.4s" }} />
              <span style={{ fontSize: "11px", color: "var(--text-3)", marginLeft: "4px" }}>Analyzing risk drivers & querying Groq model...</span>
            </div>
          </div>
        )}
      </div>

      <div className="assistant-quick-prompts">
        {quickPrompts.map((prompt) => (
          <button
            key={prompt}
            type="button"
            className="quick-chip"
            onClick={() => handleSend(prompt)}
            disabled={!selectedProject || isLoading}
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
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          disabled={!selectedProject || isLoading}
        />
        <button type="submit" className="assistant-send-btn" disabled={!selectedProject || !inputQuery.trim() || isLoading}>
          {isLoading ? "..." : "Send"}
        </button>
      </form>
    </div>
  );
}

function SafeFormattedText({ content }: { content: string }) {
  if (!content) return null;

  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];
  let inTable = false;
  let tableRows: string[][] = [];

  const renderInline = (text: string): React.ReactNode[] => {
    const parts: React.ReactNode[] = [];
    const regex = /(\*\*.*?\*\*|`.*?`)/g;
    let lastIndex = 0;
    let match: RegExpExecArray | null;

    while ((match = regex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push(text.substring(lastIndex, match.index));
      }
      const token = match[0];
      if (token.startsWith("**") && token.endsWith("**")) {
        parts.push(<strong key={match.index}>{token.slice(2, -2)}</strong>);
      } else if (token.startsWith("`") && token.endsWith("`")) {
        parts.push(<code key={match.index}>{token.slice(1, -1)}</code>);
      }
      lastIndex = regex.lastIndex;
    }
    if (lastIndex < text.length) {
      parts.push(text.substring(lastIndex));
    }
    return parts;
  };

  const flushTable = () => {
    if (tableRows.length > 0) {
      const validRows = tableRows.filter(
        (row) => !row.every((cell) => /^[\s\-:]+$/.test(cell))
      );
      if (validRows.length > 0) {
        const header = validRows[0];
        const body = validRows.slice(1);
        elements.push(
          <div key={`tbl-${elements.length}`} style={{ overflowX: "auto", margin: "8px 0" }}>
            <table style={{ width: "100%", fontSize: "0.8rem", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  {header.map((cell, idx) => (
                    <th key={idx} style={{ borderBottom: "1px solid var(--border)", padding: "4px 8px", textAlign: "left", background: "var(--surface-alt)" }}>
                      {renderInline(cell.trim())}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {body.map((row, rIdx) => (
                  <tr key={rIdx}>
                    {row.map((cell, cIdx) => (
                      <td key={cIdx} style={{ borderBottom: "1px solid var(--border-soft)", padding: "4px 8px" }}>
                        {renderInline(cell.trim())}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      }
      tableRows = [];
      inTable = false;
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
      inTable = true;
      const cells = trimmed.split("|").slice(1, -1);
      tableRows.push(cells);
      continue;
    } else if (inTable) {
      flushTable();
    }

    if (!trimmed) {
      continue;
    }

    if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
      elements.push(
        <li key={i} style={{ marginLeft: "1rem", marginBottom: "2px" }}>
          {renderInline(trimmed.substring(2))}
        </li>
      );
    } else {
      elements.push(
        <p key={i} style={{ margin: "4px 0" }}>
          {renderInline(line)}
        </p>
      );
    }
  }

  if (inTable) {
    flushTable();
  }

  return <>{elements}</>;
}

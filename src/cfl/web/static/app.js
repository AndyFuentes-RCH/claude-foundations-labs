"use strict";

const $ = (id) => document.getElementById(id);
const state = { labs: [], providers: {}, current: null };

function setMode(mode) {
  const el = $("meta-mode");
  el.textContent = mode || "—";
  el.className = "badge" + (mode ? ` mode-${mode}` : "");
}

function setMeta({ provider, model, mode }) {
  $("meta-provider").textContent = provider || "—";
  $("meta-model").textContent = model || "—";
  setMode(mode);
}

function resetResult(query) {
  $("out-query").textContent = query ?? "—";
  $("out-answer").textContent = "";
  $("out-alerts").innerHTML = "";
  $("out-tools").innerHTML = '<tr><td colspan="4" class="muted">—</td></tr>';
  $("out-footer").textContent = "";
}

function alertBox(kind, text) {
  const div = document.createElement("div");
  div.className = `alert ${kind}`;
  div.textContent = text;
  $("out-alerts").appendChild(div);
}

function addToolRow(index, name, input, resultText) {
  const body = $("out-tools");
  if (body.querySelector("td.muted")) body.innerHTML = "";
  const tr = document.createElement("tr");
  for (const value of [index, name, JSON.stringify(input), resultText]) {
    const td = document.createElement("td");
    td.textContent = value;
    tr.appendChild(td);
  }
  body.appendChild(tr);
}

function providerOption(key) {
  const p = state.providers[key];
  const opt = document.createElement("option");
  opt.value = key;
  opt.textContent = p ? `${p.label} — ${p.mode}` : key;
  return opt;
}

function renderNav() {
  const list = $("lab-list");
  const select = $("lab-select");
  list.innerHTML = "";
  select.innerHTML = "";
  for (const lab of state.labs) {
    const li = document.createElement("li");
    const btn = document.createElement("button");
    btn.type = "button";
    btn.dataset.key = lab.key;
    btn.innerHTML = `<span class="num">${lab.key}</span>`;
    btn.append(lab.title);
    const st = document.createElement("span");
    st.className = "st";
    st.textContent = lab.status;
    btn.appendChild(st);
    btn.addEventListener("click", () => selectLab(lab.key));
    li.appendChild(btn);
    list.appendChild(li);
    const opt = document.createElement("option");
    opt.value = lab.key;
    opt.textContent = `${lab.key} · ${lab.title}`;
    select.appendChild(opt);
  }
  select.addEventListener("change", (e) => selectLab(e.target.value));
}

function chips(container, values, onPick) {
  container.innerHTML = "";
  for (const v of values) {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = v;
    b.addEventListener("click", () => onPick(v));
    container.appendChild(b);
  }
}

async function selectLab(key) {
  const lab = state.labs.find((l) => l.key === key);
  state.current = lab;
  history.replaceState(null, "", `#lab-${key}`);
  document.querySelectorAll("#lab-list button").forEach((b) => b.setAttribute("aria-current", String(b.dataset.key === key)));
  $("lab-select").value = key;
  $("lab-title").textContent = `Proyecto ${lab.key} · ${lab.title}`;
  $("lab-status").textContent = lab.status;
  $("lab-courses").textContent = "Cursos: " + lab.courses.join(" · ");
  $("lab-note").textContent = lab.status_note;
  $("lab-readme").textContent = lab.readme;
  for (const id of ["panel-assistant", "panel-mcp", "panel-prompt"]) $(id).hidden = true;
  resetResult();

  if (lab.kind === "assistant" || lab.kind === "cache") {
    $("panel-assistant").hidden = false;
    const sel = $("provider-select");
    sel.innerHTML = "";
    lab.providers.forEach((p) => sel.appendChild(providerOption(p)));
    const first = state.providers[lab.providers[0]];
    setMeta({ provider: first?.label, model: first?.model, mode: first?.mode });
    sel.onchange = () => {
      const p = state.providers[sel.value];
      setMeta({ provider: p.label, model: p.model, mode: p.mode });
    };
    chips($("examples"), lab.examples, (v) => { $("query").value = v; });
    if (!$("query").value) $("query").value = lab.examples[0] || "";
  } else if (lab.kind === "mcp") {
    $("panel-mcp").hidden = false;
    setMeta({ provider: "Cliente MCP local (sin Claude)", model: "—", mode: "MOCK" });
    chips($("mcp-examples"), lab.examples, (v) => { $("mcp-id").value = v; });
    $("mcp-id").value = lab.examples[0];
  } else {
    $("panel-prompt").hidden = false;
    await loadPromptLab(lab);
  }
}

async function loadPromptLab(lab) {
  const res = await fetch(`/api/labs/${lab.key}`);
  const data = await res.json();
  const p = data.providers[0];
  setMeta({ provider: p?.label, model: p?.model, mode: lab.kind === "manual" ? "PENDIENTE" : p?.mode });
  $("prompt-intro").textContent = lab.kind === "manual"
    ? "Práctica manual en Claude.ai. Opcionalmente puede ejecutarse por API; ambas ejecuciones se registran por separado."
    : "Compara el prompt inicial con el mejorado. La ejecución por API guarda ambas salidas con sus metadatos reales.";
  const sel = $("prompt-provider");
  sel.innerHTML = "";
  lab.providers.forEach((k) => sel.appendChild(providerOption(k)));
  $("prompt-outputs").textContent = data.outputs.length
    ? `Salidas guardadas: ${data.outputs.join(", ")}`
    : "Aún no hay salidas guardadas de una ejecución LIVE.";
  const mat = $("materials");
  mat.innerHTML = "";
  for (const m of data.materials) {
    const d = document.createElement("details");
    const s = document.createElement("summary");
    s.textContent = m.path;
    const pre = document.createElement("pre");
    pre.className = "box";
    pre.textContent = m.content;
    d.append(s, pre);
    mat.appendChild(d);
  }
}

async function runAssistant(ev) {
  ev.preventDefault();
  const lab = state.current;
  const query = $("query").value.trim();
  if (!query) return;
  const provider = $("provider-select").value;
  resetResult(query);
  $("run-btn").disabled = true;
  let toolIndex = 0;
  const pendingCalls = {};
  try {
    const res = await fetch("/api/assistant/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lab: lab.key, provider, query }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let idx;
      while ((idx = buffer.indexOf("\n\n")) >= 0) {
        const chunk = buffer.slice(0, idx);
        buffer = buffer.slice(idx + 2);
        if (!chunk.startsWith("data: ")) continue;
        const e = JSON.parse(chunk.slice(6));
        handleEvent(e, pendingCalls, () => ++toolIndex);
      }
    }
  } catch (err) {
    alertBox("error", String(err));
  } finally {
    $("run-btn").disabled = false;
  }
}

function handleEvent(e, pendingCalls, nextIndex) {
  switch (e.type) {
    case "meta": setMeta(e); break;
    case "pending":
      alertBox("pending", "PENDIENTE — no se realizó ninguna llamada. Falta: " + e.missing.join(" · "));
      $("out-answer").textContent = "(sin respuesta: proveedor pendiente)";
      break;
    case "text": $("out-answer").textContent += e.text; break;
    case "tool_call": pendingCalls[e.id] = e; break;
    case "tool_result": {
      const res = e.is_error ? `error: ${e.error_code}` : (e.found === false ? "no encontrada" : "ok");
      addToolRow(nextIndex(), e.name, e.input, res);
      // texto intermedio entre herramientas: la respuesta final llegará después
      $("out-answer").textContent = "";
      break;
    }
    case "warning": alertBox("warn", e.message); break;
    case "error": alertBox("error", `${e.kind}: ${e.message}`); break;
    case "done": {
      $("out-answer").textContent = e.answer || $("out-answer").textContent || "(sin texto)";
      if (e.model) $("meta-model").textContent = e.model;
      const parts = [`run_id ${e.run_id}`, `iteraciones ${e.iterations}`, `stop_reason ${e.stop_reason}`, `${e.duration_ms} ms`];
      parts.push(e.request_ids.length ? `request_id ${e.request_ids.join(", ")}` : "request_id: no disponible");
      parts.push(Object.keys(e.usage).length ? `tokens ${JSON.stringify(e.usage)}` : "tokens: no disponible");
      if (e.extra && e.extra.cache) parts.push(`caché ${JSON.stringify(e.extra.cache)}`);
      $("out-footer").textContent = parts.join(" · ");
      break;
    }
  }
}

async function runMcp(ev) {
  ev.preventDefault();
  const raw = $("mcp-id").value.trim();
  resetResult(`get_transaction_status(${JSON.stringify({ transaction_id: raw })})`);
  const res = await fetch("/api/mcp/call", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ transaction_id: raw || null }),
  });
  const data = await res.json();
  setMeta(data);
  $("out-answer").textContent = data.structured ? JSON.stringify(data.structured, null, 2) : data.text;
  if (data.is_error) alertBox("error", "La herramienta devolvió is_error=true (entrada inválida).");
  addToolRow(1, "get_transaction_status", data.query, data.is_error ? "is_error" : (data.structured?.found ? "ok" : "no encontrada"));
  $("out-footer").textContent = `run_id ${data.run_id} · prueba de cliente MCP local, sin Claude`;
}

async function runPromptLab() {
  const lab = state.current;
  const provider = $("prompt-provider").value;
  resetResult(`Ejecutar prompts del Proyecto ${lab.key} por API`);
  const res = await fetch(`/api/prompt-labs/${lab.key}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ provider }),
  });
  const data = await res.json();
  setMeta(data);
  if (data.mode !== "LIVE") {
    alertBox("pending", "PENDIENTE — no se realizó ninguna llamada. Falta: " + data.missing.join(" · "));
    $("out-answer").textContent = "(sin respuesta)";
  } else {
    $("out-answer").textContent = "Salidas guardadas:\n" + data.outputs.join("\n");
  }
}

async function init() {
  const res = await fetch("/api/labs");
  const data = await res.json();
  state.labs = data.labs;
  data.providers.forEach((p) => { state.providers[p.provider] = p; });
  renderNav();
  $("assistant-form").addEventListener("submit", runAssistant);
  $("mcp-form").addEventListener("submit", runMcp);
  $("prompt-run").addEventListener("click", runPromptLab);
  // Enlaces de demostración: ?lab=02&provider=mock&q=...&run=1 (o #lab-02)
  const params = new URLSearchParams(location.search);
  const fromHash = location.hash.match(/^#lab-(\d{2})$/);
  const key = params.get("lab") || (fromHash ? fromHash[1] : "02");
  await selectLab(state.labs.some((l) => l.key === key) ? key : "02");
  if (params.get("provider") && state.current.providers.includes(params.get("provider"))) {
    $("provider-select").value = params.get("provider");
    $("provider-select").dispatchEvent(new Event("change"));
  }
  if (params.get("q")) {
    $("query").value = params.get("q");
    $("mcp-id").value = params.get("q");
  }
  if (params.get("run") === "1") {
    const kind = state.current.kind;
    if (kind === "assistant" || kind === "cache") $("assistant-form").requestSubmit();
    else if (kind === "mcp") $("mcp-form").requestSubmit();
    else $("prompt-run").click();
  }
}

init();

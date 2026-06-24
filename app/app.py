from flask import Flask, jsonify, request, Response
import json
from datetime import datetime

app = Flask(__name__)

# ── In-memory store ──────────────────────────────────────────────────────────

PRODUCTS = [
    {"id": 1, "name": "Mechanical Keyboard",  "price": 149.99, "stock": 12, "category": "peripherals"},
    {"id": 2, "name": "4K Webcam",            "price": 89.95,  "stock": 34, "category": "peripherals"},
    {"id": 3, "name": "Ergonomic Mouse",       "price": 59.00,  "stock": 8,  "category": "peripherals"},
    {"id": 4, "name": "USB-C Hub (7-port)",    "price": 44.50,  "stock": 55, "category": "accessories"},
    {"id": 5, "name": "Monitor Light Bar",     "price": 39.99,  "stock": 20, "category": "accessories"},
    {"id": 6, "name": "Desk Mat (XL)",         "price": 29.00,  "stock": 100,"category": "accessories"},
]

cart = []   # list of { product_id, quantity, name, unit_price }

# ── Helpers ──────────────────────────────────────────────────────────────────

def json_response(data, status=200):
    return Response(
        json.dumps(data, indent=2),
        status=status,
        mimetype="application/json",
        headers={"Access-Control-Allow-Origin": "*"},
    )


# ── Routes ───────────────────────────────────────────────────────────────────

WELCOME_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Store API</title>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet"/>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg:       #080A12;
      --surface:  #111827;
      --card:     #161B2E;
      --border:   #1E2740;
      --violet:   #7C3AED;
      --violet-d: #5B21B6;
      --cyan:     #22D3EE;
      --green:    #34D399;
      --red:      #F87171;
      --text:     #E2E8F0;
      --muted:    #64748B;
      --sub:      #94A3B8;
      --mono:     'JetBrains Mono', 'Courier New', monospace;
      --sans:     'Inter', system-ui, sans-serif;
    }

    html { scroll-behavior: smooth; }

    body {
      background: var(--bg);
      color: var(--text);
      font-family: var(--sans);
      min-height: 100vh;
      line-height: 1.6;
    }

    /* ── Top bar ── */
    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 18px 40px;
      border-bottom: 1px solid var(--border);
      background: rgba(8,10,18,.85);
      backdrop-filter: blur(12px);
      position: sticky;
      top: 0;
      z-index: 10;
    }
    .logo {
      font-family: var(--mono);
      font-size: 15px;
      font-weight: 700;
      color: var(--text);
      letter-spacing: -.5px;
    }
    .logo span { color: var(--violet); }
    .badge {
      font-family: var(--mono);
      font-size: 11px;
      color: var(--green);
      background: rgba(52,211,153,.1);
      border: 1px solid rgba(52,211,153,.25);
      border-radius: 20px;
      padding: 3px 12px;
      letter-spacing: .5px;
    }

    /* ── Hero terminal ── */
    .hero {
      padding: 72px 40px 56px;
      max-width: 900px;
      margin: 0 auto;
    }
    .eyebrow {
      font-family: var(--mono);
      font-size: 11px;
      color: var(--violet);
      letter-spacing: 2px;
      text-transform: uppercase;
      margin-bottom: 20px;
    }
    h1 {
      font-family: var(--mono);
      font-size: clamp(28px, 4vw, 46px);
      font-weight: 700;
      line-height: 1.15;
      color: var(--text);
      margin-bottom: 16px;
    }
    h1 em {
      font-style: normal;
      color: var(--cyan);
    }
    .hero-sub {
      font-size: 15px;
      color: var(--sub);
      max-width: 520px;
      margin-bottom: 36px;
    }

    /* ── Terminal block ── */
    .terminal {
      background: #0D1117;
      border: 1px solid var(--border);
      border-radius: 12px;
      overflow: hidden;
      font-family: var(--mono);
    }
    .terminal-bar {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 12px 16px;
      background: #161B2E;
      border-bottom: 1px solid var(--border);
    }
    .dot { width: 12px; height: 12px; border-radius: 50%; }
    .dot.r { background: #FF5F56; }
    .dot.y { background: #FFBD2E; }
    .dot.g { background: #27C93F; }
    .terminal-title {
      font-size: 11px;
      color: var(--muted);
      margin-left: 6px;
    }
    .terminal-body {
      padding: 20px 24px;
      font-size: 13px;
      line-height: 1.9;
    }
    .t-prompt { color: var(--violet); }
    .t-cmd    { color: var(--text); }
    .t-out    { color: var(--green); }
    .t-cmt    { color: var(--muted); }

    /* ── Endpoints grid ── */
    .section {
      max-width: 900px;
      margin: 0 auto;
      padding: 0 40px 80px;
    }
    .section-label {
      font-family: var(--mono);
      font-size: 11px;
      color: var(--muted);
      letter-spacing: 2px;
      text-transform: uppercase;
      border-top: 1px solid var(--border);
      padding-top: 40px;
      margin-bottom: 24px;
    }
    .endpoints { display: grid; gap: 12px; }

    .ep-card {
      display: grid;
      grid-template-columns: 68px 1fr auto;
      align-items: start;
      gap: 16px;
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 18px 22px;
      cursor: pointer;
      transition: border-color .18s, background .18s;
      text-align: left;
      width: 100%;
      font-family: inherit;
    }
    .ep-card:hover {
      border-color: var(--violet);
      background: #1A1F35;
    }
    .ep-card:active { transform: scale(.995); }

    .method {
      font-family: var(--mono);
      font-size: 11px;
      font-weight: 700;
      border-radius: 5px;
      padding: 3px 8px;
      text-align: center;
      letter-spacing: .5px;
    }
    .GET  { background: rgba(34,211,238,.12); color: var(--cyan); border: 1px solid rgba(34,211,238,.25); }
    .POST { background: rgba(124,58,237,.15); color: #A78BFA;     border: 1px solid rgba(124,58,237,.3); }

    .ep-meta { display: flex; flex-direction: column; gap: 4px; }
    .ep-path {
      font-family: var(--mono);
      font-size: 14px;
      font-weight: 600;
      color: var(--text);
    }
    .ep-desc { font-size: 13px; color: var(--sub); }

    .run-btn {
      font-family: var(--mono);
      font-size: 11px;
      color: var(--violet);
      background: rgba(124,58,237,.12);
      border: 1px solid rgba(124,58,237,.3);
      border-radius: 6px;
      padding: 5px 14px;
      cursor: pointer;
      transition: background .15s;
      white-space: nowrap;
      align-self: center;
    }
    .run-btn:hover { background: rgba(124,58,237,.25); }

    /* ── Response panel ── */
    .response-panel {
      background: #0D1117;
      border: 1px solid var(--border);
      border-top: 0;
      border-radius: 0 0 10px 10px;
      font-family: var(--mono);
      font-size: 12.5px;
      line-height: 1.7;
      display: none;
      overflow: hidden;
    }
    .response-panel.open { display: block; }
    .resp-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 22px;
      background: #161B2E;
      border-bottom: 1px solid var(--border);
      font-size: 11px;
    }
    .status-ok   { color: var(--green); }
    .status-err  { color: var(--red);   }
    .resp-time   { color: var(--muted); }
    pre.resp-body {
      padding: 16px 22px;
      white-space: pre-wrap;
      word-break: break-all;
      color: var(--sub);
      max-height: 340px;
      overflow-y: auto;
    }
    pre.resp-body .json-key   { color: #93C5FD; }
    pre.resp-body .json-str   { color: var(--green); }
    pre.resp-body .json-num   { color: #FCA5A5; }
    pre.resp-body .json-bool  { color: #FBBF24; }
    pre.resp-body .json-null  { color: var(--muted); }

    /* ── Footer ── */
    footer {
      border-top: 1px solid var(--border);
      padding: 24px 40px;
      text-align: center;
      font-family: var(--mono);
      font-size: 11px;
      color: var(--muted);
    }
    footer span { color: var(--violet); }
  </style>
</head>
<body>

<header>
  <div class="logo"><span>//</span> store-api</div>
  <div class="badge">● LIVE</div>
</header>

<div class="hero">
  <div class="eyebrow">REST API v1.0</div>
  <h1>Your store,<br/><em>one endpoint away.</em></h1>
  <p class="hero-sub">
    A minimal Flask-powered store API. Browse products, manage a cart, 
    and monitor health — all from clean JSON responses. Click any route below to fire a live request.
  </p>

  <div class="terminal">
    <div class="terminal-bar">
      <div class="dot r"></div><div class="dot y"></div><div class="dot g"></div>
      <span class="terminal-title">store-api — bash</span>
    </div>
    <div class="terminal-body">
      <div><span class="t-prompt">$</span> <span class="t-cmd">curl http://localhost:5000/products | python3 -m json.tool</span></div>
      <div><span class="t-out">{</span></div>
      <div><span class="t-out">&nbsp;&nbsp;"count": 6,</span></div>
      <div><span class="t-out">&nbsp;&nbsp;"products": [ ... ]</span></div>
      <div><span class="t-out">}</span></div>
      <br/>
      <div><span class="t-cmt"># Or just click the route cards below ↓</span></div>
    </div>
  </div>
</div>

<div class="section">
  <div class="section-label">Endpoints</div>
  <div class="endpoints" id="endpoints"></div>
</div>

<footer>
  Built with <span>Flask</span> · Running on Python · All data in-memory
</footer>

<script>
const endpoints = [
  {
    method: "GET",
    path: "/",
    desc: "Welcome message and API overview",
    body: null,
  },
  {
    method: "GET",
    path: "/products",
    desc: "Returns the full product catalogue as JSON",
    body: null,
  },
  {
    method: "GET",
    path: "/cart",
    desc: "Returns current cart contents and subtotal",
    body: null,
  },
  {
    method: "POST",
    path: "/cart/add",
    desc: "Adds an item to the cart — sends { product_id, quantity }",
    body: { product_id: 1, quantity: 2 },
  },
  {
    method: "GET",
    path: "/health",
    desc: "Health check — returns uptime and status",
    body: null,
  },
];

function highlight(json) {
  return JSON.stringify(json, null, 2)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"(\\\\.|[^"\\\\])*"(?=\\s*:)/g, m => `<span class="json-key">${m}</span>`)
    .replace(/: "(\\\\.|[^"\\\\])*"/g, m => `: <span class="json-str">${m.slice(2)}</span>`)
    .replace(/: (\\d+\\.?\\d*)/g, m => `: <span class="json-num">${m.slice(2)}</span>`)
    .replace(/: (true|false)/g, m => `: <span class="json-bool">${m.slice(2)}</span>`)
    .replace(/: null/g, m => `: <span class="json-null">null</span>`);
}

const container = document.getElementById("endpoints");

endpoints.forEach((ep, i) => {
  const wrapper = document.createElement("div");

  const card = document.createElement("button");
  card.className = "ep-card";
  card.innerHTML = `
    <span class="method ${ep.method}">${ep.method}</span>
    <div class="ep-meta">
      <span class="ep-path">${ep.path}</span>
      <span class="ep-desc">${ep.desc}</span>
    </div>
    <span class="run-btn">Run →</span>
  `;

  const panel = document.createElement("div");
  panel.className = "response-panel";
  panel.innerHTML = `
    <div class="resp-header">
      <span class="resp-status"></span>
      <span class="resp-time"></span>
    </div>
    <pre class="resp-body">Waiting for response…</pre>
  `;

  card.addEventListener("click", async () => {
    const wasOpen = panel.classList.contains("open");
    panel.classList.toggle("open", !wasOpen);
    if (wasOpen) return;

    const t0 = performance.now();
    try {
      const opts = ep.body
        ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(ep.body) }
        : { method: ep.method };

      const res = await fetch(ep.path, opts);
      const ms  = Math.round(performance.now() - t0);
      const json = await res.json();

      panel.querySelector(".resp-status").className = "resp-status " + (res.ok ? "status-ok" : "status-err");
      panel.querySelector(".resp-status").textContent = res.ok ? `● ${res.status} OK` : `● ${res.status} ERROR`;
      panel.querySelector(".resp-time").textContent = `${ms} ms`;
      panel.querySelector(".resp-body").innerHTML = highlight(json);
    } catch (err) {
      panel.querySelector(".resp-status").textContent = "● NETWORK ERROR";
      panel.querySelector(".resp-status").className = "resp-status status-err";
      panel.querySelector(".resp-body").textContent = err.message;
    }
  });

  // Round top corners for card when panel is open
  const obs = new MutationObserver(() => {
    const open = panel.classList.contains("open");
    card.style.borderBottomLeftRadius  = open ? "0" : "";
    card.style.borderBottomRightRadius = open ? "0" : "";
    card.style.borderBottom = open ? "0" : "";
  });
  obs.observe(panel, { attributes: true, attributeFilter: ["class"] });

  wrapper.appendChild(card);
  wrapper.appendChild(panel);
  container.appendChild(wrapper);
});
</script>
</body>
</html>
"""


@app.route("/")
def welcome():
    accept = request.headers.get("Accept", "")
    if "text/html" in accept or accept == "*/*":
        return WELCOME_HTML, 200, {"Content-Type": "text/html"}
    return json_response({
        "service": "store-api",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            {"method": "GET",  "path": "/"},
            {"method": "GET",  "path": "/products"},
            {"method": "GET",  "path": "/cart"},
            {"method": "POST", "path": "/cart/add"},
            {"method": "GET",  "path": "/health"},
        ],
    })


@app.route("/products")
def get_products():
    category = request.args.get("category")
    results = PRODUCTS
    if category:
        results = [p for p in PRODUCTS if p["category"] == category]
    return json_response({
        "count": len(results),
        "products": results,
    })


@app.route("/cart")
def get_cart():
    subtotal = sum(item["unit_price"] * item["quantity"] for item in cart)
    return json_response({
        "item_count": len(cart),
        "items": cart,
        "subtotal": round(subtotal, 2),
        "currency": "USD",
    })


@app.route("/cart/add", methods=["POST"])
def add_to_cart():
    data = request.get_json(silent=True)
    if not data:
        return json_response({"error": "Request body must be JSON."}, 400)

    product_id = data.get("product_id")
    quantity   = data.get("quantity", 1)

    if product_id is None:
        return json_response({"error": "Missing required field: product_id"}, 400)
    if not isinstance(quantity, int) or quantity < 1:
        return json_response({"error": "quantity must be a positive integer."}, 400)

    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        return json_response({"error": f"No product found with id={product_id}"}, 404)

    existing = next((i for i in cart if i["product_id"] == product_id), None)
    if existing:
        existing["quantity"] += quantity
    else:
        cart.append({
            "product_id": product["id"],
            "name":       product["name"],
            "unit_price": product["price"],
            "quantity":   quantity,
        })

    subtotal = sum(i["unit_price"] * i["quantity"] for i in cart)
    return json_response({
        "message": f'Added {quantity}× "{product["name"]}" to cart.',
        "cart_item_count": len(cart),
        "subtotal": round(subtotal, 2),
    }, 201)


@app.route("/health")
def health():
    return json_response({
        "status": "ok",
        "service": "store-api",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checks": {
            "products_loaded": len(PRODUCTS),
            "cart_items":      len(cart),
        },
    })


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

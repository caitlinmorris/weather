/**
 * we.ather relay — Cloudflare Worker + Durable Object implementation.
 *
 * Implements the EXACT same HTTP contract as presence/relay/app.py (the
 * FastAPI/Fly implementation); the two are interchangeable and the Python
 * relay's test suite defines the contract. Free-tier hostable: no card,
 * no server, no cost at this load. One deployment = one board, owned by
 * a member of that room (host-per-board; see docs/social-topology.md).
 *
 * Security properties mirrored from docs/security-model.md:
 * - field whitelist: unknown fields rejected (422), never ignored —
 *   except `openness`, deprecated: accepted-and-ignored, never stored;
 * - tokens held only as SHA-256 hashes (RELAY_TOKENS secret);
 * - a token writes/deletes only its own person;
 * - bounded ring per person (max 40, 7-day TTL), no long-term archive;
 * - state bodies never logged.
 */

const RING_MAX = 40;
const RING_TTL_S = 7 * 24 * 3600;

const ALLOWED_FIELDS = new Set([
  "person_id", "updated_at", "presence", "topic_gist", "topic_micro",
  "topic_tags", "phase", "staleness_hours", "last_active", "openness",
]);
const PHASE_VALUES = new Set(["exploring", "shaping", "building",
  "debugging", "polishing", "writing", "unknown"]);
const PRESENCE_VALUES = new Set(["active", "recently_active", "away"]);

function bad(status, msg) {
  return new Response(JSON.stringify({ detail: msg }), {
    status, headers: { "content-type": "application/json" },
  });
}

function ok(obj, status = 200) {
  return new Response(obj === null ? null : JSON.stringify(obj), {
    status, headers: { "content-type": "application/json" },
  });
}

async function sha256hex(text) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, "0")).join("");
}

function validate(state) {
  if (typeof state !== "object" || state === null) return "not an object";
  for (const key of Object.keys(state)) {
    if (!ALLOWED_FIELDS.has(key)) return `unknown field: ${key}`;
  }
  if (typeof state.person_id !== "string" || state.person_id.length > 40)
    return "bad person_id";
  if (typeof state.updated_at !== "string" || isNaN(Date.parse(state.updated_at)))
    return "bad updated_at";
  if (state.presence !== undefined && !PRESENCE_VALUES.has(state.presence))
    return "bad presence";
  if (state.phase !== undefined && !PHASE_VALUES.has(state.phase))
    return "bad phase";
  if ((state.topic_gist || "").length > 240) return "gist too long";
  if ((state.topic_micro || "").length > 80) return "micro too long";
  if (state.topic_tags !== undefined
      && (!Array.isArray(state.topic_tags) || state.topic_tags.length > 7))
    return "bad tags";
  return null;
}

export class Board {
  constructor(state, env) {
    this.state = state;
    this.env = env;
    this.rings = null;
  }

  async load() {
    if (this.rings === null) {
      this.rings = (await this.state.storage.get("rings")) || {};
    }
  }

  async save() {
    await this.state.storage.put("rings", this.rings);
  }

  prune(ring) {
    const cutoff = Date.now() / 1000 - RING_TTL_S;
    while (ring.length && ring[0][0] < cutoff) ring.shift();
  }

  async authedPerson(request) {
    const header = request.headers.get("authorization") || "";
    const token = header.replace(/^Bearer\s+/i, "").trim();
    const digest = await sha256hex(token);
    const hashes = JSON.parse(this.env.RELAY_TOKENS || "{}");
    for (const [person, stored] of Object.entries(hashes)) {
      if (digest === stored) return person;
    }
    return null;
  }

  async fetch(request) {
    const url = new URL(request.url);
    const person = await this.authedPerson(request);
    if (person === null) return bad(401, "unknown token");
    await this.load();

    if (request.method === "POST" && url.pathname === "/state") {
      let payload;
      try { payload = await request.json(); } catch { return bad(422, "not json"); }
      const problem = validate(payload);
      if (problem) return bad(422, problem);
      if (payload.person_id !== person)
        return bad(403, "token may only write its own state");
      delete payload.openness; // deprecated: never stored
      const ring = this.rings[person] || (this.rings[person] = []);
      this.prune(ring);
      // Idempotent by timestamp, latest-write-wins (contract parity).
      const existing = ring.findIndex(([, s]) => s.updated_at === payload.updated_at);
      if (existing >= 0) ring[existing] = [ring[existing][0], payload];
      else {
        ring.push([Date.now() / 1000, payload]);
        while (ring.length > RING_MAX) ring.shift();
      }
      await this.save();
      return ok(null, 204);
    }

    if (request.method === "GET" && url.pathname === "/group") {
      const per_person = [];
      for (const [member, ring] of Object.entries(this.rings)) {
        this.prune(ring);
        if (ring.length)
          per_person.push({ person_id: member, states: ring.map(([, s]) => s) });
      }
      return ok({ generated_at: new Date().toISOString(), per_person });
    }

    if (request.method === "DELETE" && url.pathname.startsWith("/state/")) {
      const target = decodeURIComponent(url.pathname.slice("/state/".length));
      if (target !== person)
        return bad(403, "token may only revoke its own state");
      delete this.rings[person]; // idempotent
      await this.save();
      return ok(null, 204);
    }

    if (request.method === "GET" && url.pathname === "/whoami") {
      return ok({ person_id: person });
    }

    if (request.method === "GET" && url.pathname === "/health") {
      const present = Object.values(this.rings).filter(r => r.length).length;
      return ok({ ok: true, people_present: present });
    }

    return bad(404, "no such route");
  }
}

export default {
  async fetch(request, env) {
    // /health is the only unauthenticated route (parity with app.py).
    const url = new URL(request.url);
    const id = env.BOARD.idFromName("board"); // one deployment = one board
    const board = env.BOARD.get(id);
    if (url.pathname === "/health" && !(request.headers.get("authorization"))) {
      // allow unauthenticated health: patch through with a synthetic check
      const stub = await board.fetch(new Request(request.url, {
        headers: { authorization: "Bearer __health__" },
      }));
      if (stub.status === 401) {
        // no valid token needed for liveness; report reachable, hide count
        return ok({ ok: true });
      }
      return stub;
    }
    return board.fetch(request);
  },
};

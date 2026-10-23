"""ReRoute core (sandbox, synthetic data).

Run offline self-test (no API key needed):   python reroute.py
Run live with Gemini:                        python reroute.py --live
Needs: Python 3.10+. Live mode also needs `pip install google-genai` and a GEMINI_API_KEY
(free key from Google AI Studio). Optional: set GEMINI_MODEL to a model your key can use.
"""
import copy, json, sqlite3, sys, time


# ---------- time helpers (minutes since midnight) ----------
def hm(s):
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def fmt(t):
    return f"{t // 60:02d}:{t % 60:02d}"


NOW = hm("14:05")

# ---------- synthetic fixtures ----------
CASES = {
    "C1": {"boxes": 24, "donor": "Dining Hall", "deadline": hm("14:30"), "version": 0},
}
RECIPIENTS = {  # travel = minutes donor -> recipient
    "A": {"capacity": 8,  "closes": hm("17:00"), "handling_ok": True, "travel": 6},
    "B": {"capacity": 24, "closes": hm("14:45"), "handling_ok": True, "travel": 10},
    "C": {"capacity": 30, "closes": hm("14:15"), "handling_ok": True, "travel": 8},
    "D": {"capacity": 24, "closes": hm("16:00"), "handling_ok": None, "travel": 9},  # evidence missing
}
VOLUNTEERS = {  # eta = minutes from now to reach the donor
    "V1": {"capacity": 30, "eta": 7},
    "V2": {"capacity": 30, "eta": 20},   # too slow
    "V3": {"capacity": 10, "eta": 5},    # too small
}


class World:
    def __init__(self):
        self.cases = copy.deepcopy(CASES)
        self.recipients = copy.deepcopy(RECIPIENTS)
        self.volunteers = copy.deepcopy(VOLUNTEERS)
        self.replies = {"driver": "yes", "recipient": "yes"}  # simulated; set "no"/None to test failures
        self.db = sqlite3.connect(":memory:")
        self.db.executescript("""
            CREATE TABLE holds(id INTEGER PRIMARY KEY, case_id TEXT, version INT,
                               volunteer TEXT, recipient TEXT, boxes INT, status TEXT);
            CREATE TABLE bookings(booking_key TEXT PRIMARY KEY, hold_id INT, status TEXT);
        """)


# ---------- deterministic validation (Python decides, never the LLM) ----------
def _active(w, where, args, ignore_case):
    q = f"SELECT COALESCE(SUM(boxes),0), COUNT(*) FROM holds WHERE status='held' AND {where}"
    if ignore_case:
        q += " AND case_id != ?"
        args = args + (ignore_case,)
    return w.db.execute(q, args).fetchone()


def validate_plan(w, case_id, vol_id, rec_id, ignore_case=None):
    case = w.cases.get(case_id)
    v, r = w.volunteers.get(vol_id), w.recipients.get(rec_id)
    if not (case and v and r):
        return {"ok": False, "reasons": ["unknown case, volunteer or recipient"]}
    boxes = case["boxes"]
    reasons = []
    held_boxes, _ = _active(w, "recipient=?", (rec_id,), ignore_case)
    _, vol_busy = _active(w, "volunteer=?", (vol_id,), ignore_case)
    free = r["capacity"] - held_boxes
    arrival = NOW + v["eta"] + r["travel"]
    if boxes > v["capacity"]:
        reasons.append(f"volunteer {vol_id} can carry {v['capacity']}, needs {boxes}")
    if boxes > free:
        reasons.append(f"recipient {rec_id} has room for {free}, needs {boxes}")
    if arrival > case["deadline"]:
        reasons.append(f"arrival {fmt(arrival)} is after deadline {fmt(case['deadline'])}")
    if arrival > r["closes"]:
        reasons.append(f"arrival {fmt(arrival)} is after recipient {rec_id} closes {fmt(r['closes'])}")
    if r["handling_ok"] is None:
        reasons.append(f"recipient {rec_id}: handling evidence missing")
    elif r["handling_ok"] is False:
        reasons.append(f"recipient {rec_id} cannot handle this food")
    if vol_busy:
        reasons.append(f"volunteer {vol_id} is already holding another plan")
    return {"ok": not reasons, "reasons": reasons, "arrival": fmt(arrival)}


# ---------- tools the LLM may call (it can propose/hold, never book) ----------
def tool_get_case(w, case_id):
    c = w.cases[case_id]
    return {"boxes": c["boxes"], "donor": c["donor"], "deadline": fmt(c["deadline"]), "version": c["version"]}


def tool_list_recipients(w):
    return {k: {"capacity": r["capacity"], "closes": fmt(r["closes"]),
                "handling_ok": r["handling_ok"], "travel_min": r["travel"]}
            for k, r in w.recipients.items()}


def tool_list_volunteers(w):
    return {k: {"capacity": v["capacity"], "eta_min": v["eta"]} for k, v in w.volunteers.items()}


def tool_check_plan(w, case_id, volunteer_id, recipient_id):
    return validate_plan(w, case_id, volunteer_id, recipient_id, ignore_case=case_id)


def tool_propose_plan(w, case_id, volunteer_id, recipient_id):
    chk = validate_plan(w, case_id, volunteer_id, recipient_id, ignore_case=case_id)
    if not chk["ok"]:
        return {"ok": False, "reasons": chk["reasons"]}
    w.db.execute("UPDATE holds SET status='released' WHERE case_id=? AND status='held'", (case_id,))
    version = w.cases[case_id]["version"] + 1
    w.cases[case_id]["version"] = version
    cur = w.db.execute(
        "INSERT INTO holds(case_id,version,volunteer,recipient,boxes,status) VALUES(?,?,?,?,?,'held')",
        (case_id, version, volunteer_id, recipient_id, w.cases[case_id]["boxes"]))
    return {"ok": True, "plan_id": cur.lastrowid, "version": version, "arrival": chk["arrival"],
            "note": "Hold placed. Waiting for dispatcher approval; you cannot book."}


TOOL_IMPL = {
    "get_case": lambda w, a: tool_get_case(w, a["case_id"]),
    "list_recipients": lambda w, a: tool_list_recipients(w),
    "list_volunteers": lambda w, a: tool_list_volunteers(w),
    "check_plan": lambda w, a: tool_check_plan(w, a["case_id"], a["volunteer_id"], a["recipient_id"]),
    "propose_plan": lambda w, a: tool_propose_plan(w, a["case_id"], a["volunteer_id"], a["recipient_id"]),
}

_PLAN_PROPS = {"case_id": {"type": "string"}, "volunteer_id": {"type": "string"},
               "recipient_id": {"type": "string"}}
TOOL_SCHEMAS = [
    {"name": "get_case", "description": "Load the case (boxes, deadline, version).",
     "input_schema": {"type": "object", "properties": {"case_id": {"type": "string"}}, "required": ["case_id"]}},
    {"name": "list_recipients", "description": "List recipients with capacity, closing time, handling evidence, travel minutes.",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "list_volunteers", "description": "List volunteers with capacity and ETA to the donor.",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "check_plan", "description": "Validate a volunteer+recipient pair. Returns ok and reasons.",
     "input_schema": {"type": "object", "properties": _PLAN_PROPS, "required": list(_PLAN_PROPS)}},
    {"name": "propose_plan", "description": "Place a hold on a validated plan for dispatcher approval.",
     "input_schema": {"type": "object", "properties": _PLAN_PROPS, "required": list(_PLAN_PROPS)}},
]

SYSTEM = (
    "You are ReRoute, a food-rescue replanning agent. A pickup was cancelled. Find a replacement "
    "volunteer and recipient for ALL boxes before the deadline. Use tools to read facts you lack. "
    "Always check_plan before propose_plan. If a check fails, read the reasons and try a different "
    "option. If recipient data is missing, do not guess. If nothing feasible exists, reply with "
    "ESCALATE and the reasons. You cannot book; a human approves."
)


# ---------- agent loop ----------
def run_agent(w, llm, user_msg, max_calls=10, budget_s=30):
    t0, calls, log = time.time(), 0, []
    step = llm.start(user_msg)
    proposal = None
    while True:
        if not step["tool_calls"]:
            break
        if calls + len(step["tool_calls"]) > max_calls or time.time() - t0 > budget_s:
            return {"status": "escalate", "reason": "tool-call or time limit", "log": log}
        results = []
        for tc in step["tool_calls"]:
            calls += 1
            try:
                out = TOOL_IMPL[tc["name"]](w, tc["input"])
            except Exception as e:  # bad tool args etc. go back to the model as evidence
                out = {"error": str(e)}
            log.append((tc["name"], tc["input"], out))
            if tc["name"] == "propose_plan" and out.get("ok"):
                proposal = out
            results.append((tc["id"], out))
        step = llm.step(results)
    if proposal:
        return {"status": "awaiting_approval", "proposal": proposal, "log": log,
                "seconds": round(time.time() - t0, 2)}
    return {"status": "escalate", "reason": step.get("text", "no feasible plan"), "log": log}


# ---------- approval + versioned, idempotent booking + verification ----------
def approve_and_book(w, hold_id, approved_version):
    h = w.db.execute("SELECT case_id,version,volunteer,recipient,status FROM holds WHERE id=?",
                     (hold_id,)).fetchone()
    if not h:
        return {"status": "error", "reason": "unknown plan"}
    case_id, version, vol, rec, status = h
    key = f"{case_id}:v{version}"
    done = w.db.execute("SELECT status FROM bookings WHERE booking_key=?", (key,)).fetchone()
    if done:  # replay of the same approval: no second write
        return {"status": done[0], "duplicate": True}
    if status != "held" or version != approved_version or w.cases[case_id]["version"] != version:
        return {"status": "stale", "reason": "plan version no longer current; needs fresh approval"}
    chk = validate_plan(w, case_id, vol, rec, ignore_case=case_id)  # facts may have changed since proposal
    if not chk["ok"]:
        w.db.execute("UPDATE holds SET status='released' WHERE id=?", (hold_id,))
        return {"status": "stale", "reason": "revalidation failed: " + "; ".join(chk["reasons"])}
    w.db.execute("INSERT INTO bookings VALUES(?,?, 'pending')", (key, hold_id))
    if w.replies["driver"] == "yes" and w.replies["recipient"] == "yes":
        w.db.execute("UPDATE bookings SET status='confirmed' WHERE booking_key=?", (key,))
        w.db.execute("UPDATE holds SET status='booked' WHERE id=?", (hold_id,))
        return {"status": "confirmed", "arrival": chk["arrival"]}
    w.db.execute("UPDATE bookings SET status='failed' WHERE booking_key=?", (key,))
    w.db.execute("UPDATE holds SET status='released' WHERE id=?", (hold_id,))
    return {"status": "failed", "reason": f"replies: {w.replies}; hold released, escalate to dispatcher"}


# ---------- baseline rule-based matcher (for the LLM-vs-rules comparison slide) ----------
def baseline_match(w, case_id):
    for rec in sorted(w.recipients, key=lambda k: w.recipients[k]["travel"]):
        for vol in sorted(w.volunteers, key=lambda k: w.volunteers[k]["eta"]):
            if validate_plan(w, case_id, vol, rec)["ok"]:
                return vol, rec
    return None  # needs structured input, cannot read free text, cannot ask for missing data


# ---------- LLM adapters ----------
class ScriptedLLM:
    """Offline stand-in that plays the 'reject A, accept B' story so you can test everything else."""
    def __init__(self):
        self.script = [
            ("get_case", {"case_id": "C1"}),
            ("list_recipients", {}),
            ("check_plan", {"case_id": "C1", "volunteer_id": "V1", "recipient_id": "A"}),
            ("check_plan", {"case_id": "C1", "volunteer_id": "V1", "recipient_id": "B"}),
            ("propose_plan", {"case_id": "C1", "volunteer_id": "V1", "recipient_id": "B"}),
        ]
        self.i = 0

    def _next(self):
        if self.i >= len(self.script):
            return {"text": "Proposed plan ready for approval.", "tool_calls": []}
        name, args = self.script[self.i]
        self.i += 1
        return {"text": "", "tool_calls": [{"id": f"t{self.i}", "name": name, "input": args}]}

    def start(self, user_msg):
        return self._next()

    def step(self, results):
        return self._next()


def gemini_declarations():
    """Convert TOOL_SCHEMAS to Gemini function declarations (plain dicts, uppercase types).
    Tools with no parameters omit 'parameters' entirely: Gemini rejects an empty OBJECT schema."""
    decls = []
    for t in TOOL_SCHEMAS:
        props = t["input_schema"]["properties"]
        d = {"name": t["name"], "description": t["description"]}
        if props:
            d["parameters"] = {
                "type": "OBJECT",
                "properties": {k: {"type": v["type"].upper()} for k, v in props.items()},
                "required": t["input_schema"].get("required", []),
            }
        decls.append(d)
    return decls


def with_retry(fn, tries=4):
    """Retry on rate-limit errors (429 / RESOURCE_EXHAUSTED) with 2s, 4s, 8s waits."""
    for attempt in range(tries):
        try:
            return fn()
        except Exception as e:
            limited = "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)
            if not limited or attempt == tries - 1:
                raise
            time.sleep(2 ** (attempt + 1))


class GeminiLLM:
    def __init__(self, model=None):
        import os
        from google import genai
        from google.genai import types
        self.types = types
        self.client = genai.Client()  # reads GEMINI_API_KEY from the environment
        self.model = model or os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        self.config = types.GenerateContentConfig(
            system_instruction=SYSTEM,
            tools=[types.Tool(function_declarations=gemini_declarations())],
            # we run the tool loop ourselves so every call is logged and capped
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        self.contents, self.names = [], {}

    def _call(self):
        resp = with_retry(lambda: self.client.models.generate_content(
            model=self.model, contents=self.contents, config=self.config))
        content = resp.candidates[0].content
        self.contents.append(content)  # append the model turn as returned (keeps any thought signatures)
        parts = content.parts or []
        calls = []
        for i, p in enumerate(parts):
            fc = getattr(p, "function_call", None)
            if fc:
                cid = fc.id or f"{fc.name}#{len(self.names)}"
                self.names[cid] = fc.name
                calls.append({"id": cid, "name": fc.name, "input": dict(fc.args or {})})
        text = "".join(p.text for p in parts if getattr(p, "text", None))
        return {"text": text, "tool_calls": calls}

    def start(self, user_msg):
        t = self.types
        self.contents = [t.Content(role="user", parts=[t.Part(text=user_msg)])]
        return self._call()

    def step(self, results):
        t = self.types
        parts = [t.Part.from_function_response(name=self.names[i], response={"result": out})
                 for i, out in results]
        self.contents.append(t.Content(role="user", parts=parts))
        return self._call()


CANCEL_MSG = ("Ravi (14:00 volunteer) just texted: can't make it, car broke down. "
              "Case C1: 24 boxes of prepared meals at the Dining Hall must reach a recipient by 14:30.")


# ---------- self-test / stress harness ----------
def selftest():
    ok = True

    def check(name, cond):
        nonlocal ok
        ok &= bool(cond)
        print(("PASS " if cond else "FAIL ") + name)

    # 1. five invalid fixtures must all be rejected
    w = World()
    invalid = [("V1", "A"), ("V2", "B"), ("V1", "C"), ("V1", "D"), ("V3", "B")]
    check("rejects all 5 invalid fixtures", all(not validate_plan(w, "C1", v, r)["ok"] for v, r in invalid))

    # 2. agent run: reject A, find B
    w = World()
    res = run_agent(w, ScriptedLLM(), CANCEL_MSG)
    p = res.get("proposal", {})
    check("agent proposes V1 -> B, arrival 14:22", res["status"] == "awaiting_approval" and p.get("arrival") == "14:22")
    print(f"     agent loop took {res['seconds']}s (excludes approval; scripted LLM, so not a real latency)")

    # 3. approval books and verifies
    out = approve_and_book(w, p["plan_id"], p["version"])
    check("approved plan confirmed", out["status"] == "confirmed")

    # 4. replaying approval 10 times never duplicates
    for _ in range(10):
        approve_and_book(w, p["plan_id"], p["version"])
    n = w.db.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
    check("0 duplicate bookings across 10 replays", n == 1)

    # 5. capacity changes before approval -> stale, hold released
    w = World()
    p = run_agent(w, ScriptedLLM(), CANCEL_MSG)["proposal"]
    w.recipients["B"]["capacity"] = 10
    out = approve_and_book(w, p["plan_id"], p["version"])
    st = w.db.execute("SELECT status FROM holds WHERE id=?", (p["plan_id"],)).fetchone()[0]
    check("capacity change before approval -> stale + hold released", out["status"] == "stale" and st == "released")

    # 6. old approval of a superseded version is refused
    w = World()
    p1 = run_agent(w, ScriptedLLM(), CANCEL_MSG)["proposal"]
    tool_propose_plan(w, "C1", "V1", "B")  # revision -> version 2
    out = approve_and_book(w, p1["plan_id"], p1["version"])
    check("approval of an old version is refused", out["status"] == "stale")

    # 7. rejected confirmation -> no confirmed booking, hold released
    w = World()
    p = run_agent(w, ScriptedLLM(), CANCEL_MSG)["proposal"]
    w.replies["recipient"] = "no"
    out = approve_and_book(w, p["plan_id"], p["version"])
    check("recipient says no -> failed, escalate", out["status"] == "failed")

    # 8. simultaneous cancellations compete for the same capacity
    w = World()
    w.cases["C2"] = {"boxes": 24, "donor": "Cafe", "deadline": hm("14:30"), "version": 0}
    w.volunteers["V4"] = {"capacity": 30, "eta": 6}
    r1 = tool_propose_plan(w, "C1", "V1", "B")
    r2 = tool_propose_plan(w, "C2", "V4", "B")
    check("two cases cannot both hold recipient B", r1["ok"] and not r2["ok"])

    # 9. baseline comparison
    w = World()
    print("     baseline matcher picks:", baseline_match(w, "C1"), "(needs structured input; cannot read the text message)")
    print("\nALL PASS" if ok else "\nSOME FAILED")


def live():
    w = World()
    res = run_agent(w, GeminiLLM(), CANCEL_MSG)
    for name, args, out in res["log"]:
        print(f"{name}{args} -> {out}")
    print(res["status"], res.get("proposal") or res.get("reason"))
    if res["status"] == "awaiting_approval" and input("Approve? [y/N] ").lower() == "y":
        p = res["proposal"]
        print(approve_and_book(w, p["plan_id"], p["version"]))


if __name__ == "__main__":
    live() if "--live" in sys.argv else selftest()
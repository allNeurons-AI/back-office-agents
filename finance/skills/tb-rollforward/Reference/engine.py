"""engine.py - baseline + new months -> trial balance by entity, translated to the reporting currency.

Model (plain English):
  * A BASELINE is a saved snapshot of every entity's balances at the end of the last CLOSED month.
  * Each run adds the months after it (closed months -> a new baseline; open months -> preliminary only).
  * Per entity and account we keep three running numbers:
        local    balance in the entity's own currency
        avg_add  every month's movement x that month's AVERAGE rate, added up   (profit & loss accounts)
        hist_add every month's movement x that month's HISTORICAL rate, added up (equity accounts)
    Asset / liability accounts are translated at read time: local balance x closing rate.
  * At the start of each fiscal year, last year's profit & loss is moved into retained earnings.
  * The leftover from translating at different rates is shown as 'Cumulative translation adjustment'
    so every entity's translated trial balance still adds up to zero.
Sign convention inside the engine: debit = positive, credit = negative.
"""
import copy, glob, hashlib, json, os, shutil, datetime as dt
from sources import classify_account, group_fp

CTA_ID = "CTA"
EPS = 1e-9


class RunError(Exception):
    def __init__(self, step, msg, details=None):
        super().__init__(msg)
        self.step, self.msg, self.details = step, msg, details or []


# ------------------------------------------------------------------ periods
def pnext(p):
    y, m = int(p[:4]), int(p[5:7])
    m += 1
    if m > 12:
        y, m = y + 1, 1
    return "%04d-%02d" % (y, m)


def pprev(p):
    y, m = int(p[:4]), int(p[5:7])
    m -= 1
    if m < 1:
        y, m = y - 1, 12
    return "%04d-%02d" % (y, m)


def prange(a, b):
    out, x = [], a
    while x <= b:
        out.append(x)
        x = pnext(x)
    return out


def month_label(p):
    return dt.date(int(p[:4]), int(p[5:7]), 1).strftime("%b_%Y")


# ------------------------------------------------------------------ baseline io
def bal_sha(bal):
    return hashlib.sha256(json.dumps(bal, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def baseline_files(store):
    return sorted(glob.glob(os.path.join(store, "Baseline", "baseline_????-??.json")))


def load_baseline(store):
    """Highest cutoff wins. Returns (baseline|None, path|None)."""
    files = baseline_files(store)
    if not files:
        return None, None
    path = files[-1]
    try:
        b = json.load(open(path))
    except Exception as e:
        raise RunError("baseline", "Baseline file %s is unreadable (%s). Restore the previous one with "
                       "'tbr.py restore-previous'." % (os.path.basename(path), e))
    if bal_sha(b["bal"]) != b.get("bal_sha"):
        raise RunError("baseline", "Baseline file %s fails its integrity check (edited or damaged). "
                       "Restore the previous one with 'tbr.py restore-previous'." % os.path.basename(path))
    return b, path


def save_baseline(store, b, keep_previous=1):
    """Write new baseline safely: temp file -> verify -> rename -> move older ones to _previous."""
    d = os.path.join(store, "Baseline")
    os.makedirs(d, exist_ok=True)
    b["bal_sha"] = bal_sha(b["bal"])
    final = os.path.join(d, "baseline_%s.json" % b["cutoff"])
    tmp = final + ".tmp"
    with open(tmp, "w") as f:
        json.dump(b, f, separators=(",", ":"))
    chk = json.load(open(tmp))
    if bal_sha(chk["bal"]) != b["bal_sha"]:
        os.remove(tmp)
        raise RunError("baseline", "Baseline verification after write failed; old baseline left untouched.")
    os.replace(tmp, final)
    notes = []
    prev = os.path.join(d, "_previous")
    for old in baseline_files(store):
        if os.path.abspath(old) == os.path.abspath(final):
            continue
        if keep_previous > 0:
            os.makedirs(prev, exist_ok=True)
            try:
                shutil.move(old, os.path.join(prev, os.path.basename(old)))
            except Exception as e:
                notes.append("could not move %s to _previous (%s)" % (os.path.basename(old), e))
        else:
            try:
                os.remove(old)
            except Exception as e:
                notes.append("OLD_BASELINE_NOT_DELETED %s (%s)" % (os.path.basename(old), e))
    if os.path.isdir(prev):
        olds = sorted(glob.glob(os.path.join(prev, "baseline_*.json")))
        for extra in olds[:max(0, len(olds) - max(keep_previous, 0))]:
            try:
                os.remove(extra)
            except Exception as e:
                notes.append("could not delete old %s (%s) - harmless" % (os.path.basename(extra), e))
    return final, notes


# ------------------------------------------------------------------ context from reference data
class FX:
    def __init__(self, rows, reporting):
        self.rep, self.d, self.notes = reporting, {}, set()
        for r in rows:
            cl = r["closing"]
            av, hs = r.get("average"), r.get("historical")
            if av is None:
                self.notes.add("average rate missing for some rows: closing rate used")
            if hs is None:
                self.notes.add("historical rate missing for some rows: closing rate used")
            self.d[(r["currency"], r["period"])] = (cl, av or cl, hs or cl)

    def get(self, ccy, per):
        if ccy == self.rep:
            return (1.0, 1.0, 1.0)
        return self.d.get((ccy, per))


def build_ctx(cfg, ref):
    errs, warns = [], []
    tm = {k.lower().strip(): v for k, v in (cfg["sources"]["accounts"].get("type_map") or {}).items()}
    accts = {}
    unknown = []
    unknown_ids = {}
    for a in ref["accounts"]:
        cls = tm.get(a["type_raw"].lower().strip()) or classify_account(a["type_raw"], a["name"])
        if cls is None:
            unknown.append("%s (%s)" % (a["account"], a["type_raw"]))
            unknown_ids[a["account"]] = a["type_raw"]
            continue
        rc = a.get("rate_class") or ""
        rate = {"current": "closing", "closing": "closing", "average": "avg", "avg": "avg",
                "historical": "hist", "hist": "hist"}.get(rc)
        if rate is None:
            rate = {"asset": "closing", "liability": "closing", "income": "avg", "expense": "avg",
                    "equity": "hist", "retained_earnings": "hist"}[cls]
        accts[a["account"]] = {"name": a["name"], "cls": cls, "rate": rate}
    if unknown:
        warns.append({"code": "unknown_account_type", "file": "accounts",
                      "detail": "account types not recognised (fine while unused): %s" % ", ".join(unknown[:8])})
    ents = {e["entity"]: e for e in ref["entities"]}
    rep = cfg["reporting_currency"]
    ent_ccy = {e: (v["currency"] or rep) for e, v in ents.items()}
    # hierarchy checks
    parent = {e: v["parent"] for e, v in ents.items() if v["parent"] and v["parent"] != e}
    for e in ents:
        seen, x = set(), e
        while x in parent:
            if x in seen:
                errs.append({"code": "hierarchy_cycle", "file": "entities", "detail": "parent loop involving %s" % e})
                break
            seen.add(x)
            x = parent[x]
    re_acct = str(cfg.get("retained_earnings_account") or "").strip()
    if not re_acct:
        res = [a for a, v in accts.items() if v["cls"] == "retained_earnings"]
        re_acct = res[0] if len(res) == 1 else ""
        if len(res) > 1:
            warns.append({"code": "several_retained_earnings", "file": "accounts",
                          "detail": "several retained-earnings accounts; set retained_earnings_account in config"})
    closed = {p["period"] for p in ref["periods"] if p["status"] == "closed"}
    if cfg.get("closed_through"):
        ct = cfg["closed_through"]
        periods_seen = {p["period"] for p in ref["periods"]}
        closed |= {p for p in periods_seen if p <= ct}
        closed.add(ct)
    fx = FX(ref["fx"], rep)
    return {"cfg": cfg, "accounts": accts, "unknown_ids": unknown_ids, "ents": ents, "ent_ccy": ent_ccy, "parent": parent, "rep": rep,
            "fx": fx, "closed": closed, "periods_known": {p["period"] for p in ref["periods"]},
            "fy": int(cfg["fiscal_year_start_month"]), "re": re_acct, "errs": errs, "warns": warns}


def check_ledger_refs(ctx, ledger, after):
    """Entities / accounts used in new ledger data must exist in the reference tables."""
    errs = []
    bad_e, bad_a, bad_t = set(), set(), set()
    for gk, g in ledger["groups"].items():
        per, ent = gk.split("|", 1)
        if after and per <= after:
            continue
        if ent not in ctx["ent_ccy"]:
            bad_e.add(ent)
        for a in g["rows"]:
            if a not in ctx["accounts"]:
                (bad_t if a in ctx["unknown_ids"] else bad_a).add(a)
    if bad_e:
        errs.append({"code": "unknown_entity", "file": "ledger",
                     "detail": "not in the entities list: %s" % ", ".join(sorted(bad_e)[:15])})
    if bad_t:
        errs.append({"code": "unknown_account_type", "file": "accounts",
                     "detail": "cannot tell if these are asset/liability/equity/income/expense: %s. Fix their Type "
                               "or add a type_map in config." % ", ".join("%s (%s)" % (a, ctx["unknown_ids"][a]) for a in sorted(bad_t)[:12])})
    if bad_a:
        errs.append({"code": "unknown_account", "file": "ledger",
                     "detail": "not in the accounts list: %s" % ", ".join(sorted(bad_a)[:15])})
    return errs


# ------------------------------------------------------------------ plan
def plan_legs(ctx, baseline, ledger):
    cutoff = baseline["cutoff"] if baseline else None
    per_data = sorted({k.split("|")[0] for k in ledger["groups"] if not cutoff or k.split("|")[0] > cutoff})
    out = {"cutoff": cutoff, "final": [], "prelim": [], "warnings": []}
    if not per_data:
        return out
    maxd = per_data[-1]
    m = pnext(cutoff) if cutoff else per_data[0]
    while m <= maxd and m in ctx["closed"]:
        if m in per_data:
            out["final"].append(m)
        else:
            out["warnings"].append("%s is closed in the periods list but has no ledger rows; baseline not advanced past it." % m)
            break
        m = pnext(m)
    x = m
    while x <= maxd:
        out["prelim"].append(x)
        x = pnext(x)
    if out["prelim"] and out["final"] is not None and out["warnings"]:
        pass
    return out


def input_fp(ctx, baseline, ledger, months, ref):
    h = hashlib.sha256()
    h.update((baseline["bal_sha"] if baseline else "none").encode())
    h.update(json.dumps(ref, sort_keys=True).encode())
    for k in sorted(ledger["groups"]):
        if k.split("|")[0] in months:
            h.update(k.encode())
            h.update(json.dumps(ledger["groups"][k]["fp"]).encode())
    h.update(json.dumps([sorted(ctx["closed"])]).encode())
    return h.hexdigest()


# ------------------------------------------------------------------ merge
def new_baseline_shell(ctx):
    return {"schema": 1, "cutoff": None, "reporting_currency": ctx["rep"], "fy_start": ctx["fy"],
            "bal": {}, "period_controls": {}, "fx_controls": {}}


def _rollover(bal, ctx, month):
    pl = [a for a, v in ctx["accounts"].items() if v["cls"] in ("income", "expense")]
    for ent, accts in bal.items():
        sl = sa = 0.0
        for a in pl:
            if a in accts:
                sl += accts[a][0]
                sa += accts[a][1]
                del accts[a]
        if abs(sl) < EPS and abs(sa) < EPS:
            continue
        if not ctx["re"]:
            raise RunError("rollover", "Fiscal year starts at %s but no retained-earnings account is defined "
                           "(add one with Type 'Retained Earnings' or set retained_earnings_account)." % month)
        rec = accts.setdefault(ctx["re"], [0.0, 0.0, 0.0])
        rec[0] += sl
        rec[1] += sa
        rec[2] += sa     # last year's profit enters equity at the average rates it was earned at


def apply_months(bal, months, ctx, ledger):
    for m in months:
        if int(m[5:7]) == ctx["fy"] and any(bal.values()):
            _rollover(bal, ctx, m)
        for gk, g in ledger["groups"].items():
            per, ent = gk.split("|", 1)
            if per != m:
                continue
            r = ctx["fx"].get(ctx["ent_ccy"][ent], m)
            if r is None:
                raise RunError("fx", "No exchange rate for %s in %s (entity %s)." % (ctx["ent_ccy"][ent], m, ent))
            tgt = bal.setdefault(ent, {})
            for a, amt in g["rows"].items():
                rec = tgt.setdefault(a, [0.0, 0.0, 0.0])
                rec[0] += amt
                rec[1] += amt * r[1]
                rec[2] += amt * r[2]
    return bal


# ------------------------------------------------------------------ translate
def translate(bal, ctx, asof):
    """-> {entity: [rows]}; each row dict(account,name,cls,local,tr,basis,rate). CTA row appended."""
    out, errs = {}, []
    for ent in sorted(bal):
        accts = bal[ent]
        ccy = ctx["ent_ccy"].get(ent, ctx["rep"])
        r = ctx["fx"].get(ccy, asof)
        rows = []
        for a in sorted(accts, key=lambda s: (len(s), s)):
            loc, avg, hist = accts[a]
            if abs(loc) < EPS and abs(avg) < EPS and abs(hist) < EPS:
                continue
            info = ctx["accounts"][a]
            if info["rate"] == "closing":
                if r is None:
                    errs.append("No closing rate for %s in %s (entity %s)" % (ccy, asof, ent))
                    continue
                tr, basis, rate = loc * r[0], "closing rate", r[0]
            elif info["rate"] == "avg":
                tr, basis, rate = avg, "average rates (added up monthly)", None
            else:
                tr, basis, rate = hist, "historical rates (added up monthly)", None
            rows.append({"account": a, "name": info["name"], "cls": info["cls"], "local": loc, "tr": tr,
                         "basis": basis, "rate": rate})
        cta = -sum(x["tr"] for x in rows)
        if ccy == ctx["rep"] or abs(cta) < 1e-6:
            cta = 0.0 if abs(cta) < 1e-6 else cta
        if abs(cta) >= 1e-6:
            rows.append({"account": CTA_ID, "name": "Cumulative translation adjustment", "cls": "equity",
                         "local": 0.0, "tr": cta, "basis": "balancing item", "rate": None})
        out[ent] = rows
    if errs:
        raise RunError("fx", "; ".join(sorted(set(errs))[:6]))
    return out


# ------------------------------------------------------------------ hierarchy + totals
def hierarchy(ctx, ledger_entities):
    parent, ents = ctx["parent"], ctx["ents"]
    nodes = set(ents) | set(parent.values())
    children = {}
    for c, p in parent.items():
        children.setdefault(p, []).append(c)

    def leaves(n):
        if n in ledger_entities and n not in children:
            return [n]
        res = [n] if n in ledger_entities else []
        for c in children.get(n, []):
            res += leaves(c)
        return res
    roll = {}
    for n in sorted(nodes):
        if n in children:
            ls = sorted(set(leaves(n)))
            if ls:
                roll[n] = ls
    return roll


def totals(rows):
    t = {"asset": 0.0, "liability": 0.0, "equity": 0.0, "pl": 0.0}
    for r in rows:
        c = r["cls"]
        if c == "asset":
            t["asset"] += r["tr"]
        elif c == "liability":
            t["liability"] += r["tr"]
        elif c in ("equity", "retained_earnings"):
            t["equity"] += r["tr"]
        else:
            t["pl"] += r["tr"]
    return {"assets": t["asset"], "liabilities": -t["liability"], "equity": -t["equity"],
            "net_income": -t["pl"], "check": sum(r["tr"] for r in rows)}


def integrity_checks(bal, tr, ctx, tol, strict):
    checks, warns = [], []
    for ent in sorted(bal):
        s = sum(v[0] for v in bal[ent].values())
        ok = abs(s) <= tol
        checks.append({"name": "Local books balance (debits = credits)", "scope": ent,
                       "status": "ok" if ok else ("fail" if strict else "warn"),
                       "detail": "difference %.2f in %s" % (s, ctx["ent_ccy"].get(ent, ""))})
        if not ok:
            warns.append("Entity %s: local balances are off by %.2f (debits do not equal credits)." % (ent, s))
    allsum = sum(r["tr"] for rows in tr.values() for r in rows)
    checks.append({"name": "Translated trial balance adds to zero", "scope": "all",
                   "status": "ok" if abs(allsum) < 0.01 else "fail", "detail": "difference %.4f" % allsum})
    return checks, warns

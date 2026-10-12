#!/usr/bin/env python3
"""tbr.py - command line for the tb-rollforward skill. Every command prints ONE JSON object.

  init            --store S                       create folders, copy engine + email template
  config-write    --store S --json file           merge answers from the setup forms into config.json (validated)
  apply-answers   --store S --form NAME --answers file [--store-host PATH]   form answers (keyed by data-name) -> config.json
  schedule-info   --store S                       cron + exact prompt for the scheduled task
  config-show     --store S
  map-path        --store S --host H --sandbox P  remember where a mounted host folder lives in this session
  inspect         --store S [--config file]       read the user's real files; report headers, proposed column mapping,
                                                  unmatched columns + guesses, account types, entities, FX coverage
  bootstrap       --store S --through YYYY-MM [--force]   build the first baseline from the history
  run             --store S --mode manual|scheduled [--force] [--accept-removed]
  ns-diff         --store S --controls controls.csv        (NetSuite source) which entity-periods need re-pulling
  email-sent      --store S --status sent|failed [--error TEXT]
  email-add-link  --store S --url URL [--label TEXT] [--folder-url URL]   add the workbook / drive-folder link to the pending email
  drive-plan      --store S                       dated folder name + every file of the latest run to upload (save-to-drive)
  preflight       --store S [--need a,b,c]        which connectors this setup/run needs (agent must verify each one)
  restore-previous --store S
  status          --store S
Exit code 0 = ok / nothing to do, 2 = failed (details in JSON).
"""
import argparse, copy, csv, datetime as dt, glob, html, json, os, re, shutil, sys, time, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import engine as E
import sources as S
import report as R
from engine import RunError

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None

DONE = {"SUCCESS", "SUCCESS_WITH_WARNINGS", "NO_CHANGE", "UP_TO_DATE"}
DEFAULT_SUBJECT = "[{{status_word}}] {{company}} trial balance by entity - {{period}} ({{run_type}})"

DEFAULT_CFG = {
    "schema_version": 1,
    "company_name": "",
    "reporting_currency": "USD",
    "fiscal_year_start_month": 1,
    "sign_convention": "debit_positive",
    "decimal_separator": ".",
    "timezone": "UTC",
    "consolidated_name": "Consolidated",
    "retained_earnings_account": "",
    "closed_through": "",
    "balance_tolerance": 1.0,
    "strict_balance": False,
    "settle_seconds": 120,
    "store_host_path": "",
    "sources": {
        "ledger": {"type": "files", "paths": [], "pattern": [], "columns": {}, "file_columns": {}},
        "accounts": {"type": "files", "paths": [], "pattern": [], "columns": {}, "type_map": {}},
        "entities": {"type": "files", "paths": [], "pattern": [], "columns": {}},
        "fx": {"type": "files", "paths": [], "pattern": [], "columns": {}},
        "periods": {"type": "files", "paths": [], "pattern": [], "columns": {}, "status_map": {}},
    },
    "email": {"provider": "gmail", "to": [], "cc": [], "attach_workbook": False, "include_numbers": True,
              "notify_no_change": True, "subject": DEFAULT_SUBJECT},
    "drive": {"provider": "none", "parent": "", "folder_pattern": "TB Rollforward {date}"},
    "schedule": {"time": "08:00", "days": "weekdays", "task_id": "tb-rollforward-daily", "created": False},
    "baseline": {"keep_previous": 1},
    "netsuite": {"subsidiaries": [], "accounting_book": 1, "root_subsidiary": 1},
}


# ------------------------------------------------------------------ helpers
def out(obj, code=0):
    print(json.dumps(obj, indent=1, default=str))
    sys.exit(code)


def deep_merge(base, over):
    r = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(r.get(k), dict):
            r[k] = deep_merge(r[k], v)
        else:
            r[k] = v
    return r


def now_local(cfg):
    tz = None
    if ZoneInfo:
        try:
            tz = ZoneInfo(cfg.get("timezone") or "UTC")
        except Exception:
            tz = ZoneInfo("UTC")
    return dt.datetime.now(tz) if tz else dt.datetime.now()


def validate_config(cfg):
    errs = []
    if cfg.get("schema_version") != 1:
        errs.append("schema_version must be 1")
    if not re.match(r"^[A-Za-z]{3}$", str(cfg.get("reporting_currency", ""))):
        errs.append("reporting_currency must be a 3-letter code")
    if not (isinstance(cfg.get("fiscal_year_start_month"), int) and 1 <= cfg["fiscal_year_start_month"] <= 12):
        errs.append("fiscal_year_start_month must be 1-12")
    if cfg.get("sign_convention") not in ("debit_positive", "credit_positive"):
        errs.append("sign_convention must be debit_positive or credit_positive")
    if cfg.get("decimal_separator") not in (".", ","):
        errs.append("decimal_separator must be . or ,")
    for ds in ("ledger", "accounts", "entities", "fx"):
        if cfg["sources"][ds].get("type") not in ("files", "netsuite"):
            errs.append("sources.%s.type must be files or netsuite" % ds)
    pt = cfg["sources"]["periods"].get("type")
    if pt not in ("files", "netsuite", "none"):
        errs.append("sources.periods.type must be files, netsuite or none")
    if pt == "none" and not cfg.get("closed_through"):
        errs.append("with no periods list you must set closed_through (last closed month, YYYY-MM)")
    if cfg.get("closed_through") and not re.match(r"^\d{4}-\d{2}$", cfg["closed_through"]):
        errs.append("closed_through must look like 2026-08")
    em = cfg["email"]
    if em.get("provider") not in ("gmail", "outlook", "none"):
        errs.append("email.provider must be gmail, outlook or none")
    if em.get("provider") != "none":
        if not em.get("to"):
            errs.append("email.to needs at least one address")
        for a in em.get("to", []) + em.get("cc", []):
            if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", a):
                errs.append("invalid email address: %s" % a)
    dv = cfg.get("drive", {})
    if dv.get("provider", "none") not in ("none", "sharepoint", "onedrive", "gdrive"):
        errs.append("drive.provider must be none, sharepoint, onedrive or gdrive")
    return errs


def load_config(store):
    p = os.path.join(store, "config.json")
    if not os.path.exists(p):
        raise RunError("config", "config.json not found in the folder. Run first-time setup (interactive) first.")
    try:
        raw = json.load(open(p))
    except Exception as e:
        raise RunError("config", "config.json is not valid JSON: %s" % e)
    cfg = deep_merge(DEFAULT_CFG, raw)
    errs = validate_config(cfg)
    if errs:
        raise RunError("config", "config.json has problems", [{"code": "config", "file": "config.json", "detail": x} for x in errs])
    return cfg


def load_pathmap(store):
    p = os.path.join(store, ".state", "pathmap.json")
    return json.load(open(p)) if os.path.exists(p) else {}


def log(store, cfg, status, mode, msg):
    os.makedirs(os.path.join(store, "Logs"), exist_ok=True)
    ts = now_local(cfg).isoformat(timespec="seconds")
    with open(os.path.join(store, "Logs", "run_log.txt"), "a") as f:
        f.write("%s | %s | %s | %s\n" % (ts, status, mode, msg.replace("\n", " ")))


def read_log(store):
    p = os.path.join(store, "Logs", "run_log.txt")
    rows = []
    if os.path.exists(p):
        for ln in open(p):
            parts = [x.strip() for x in ln.rstrip("\n").split(" | ", 3)]
            if len(parts) == 4:
                rows.append(parts)
    return rows


def last_success(store):
    for ts, st, mode, msg in reversed(read_log(store)):
        if st in ("SUCCESS", "SUCCESS_WITH_WARNINGS"):
            return ts[:16].replace("T", " ")
    return "never"


# ------------------------------------------------------------------ lock
def acquire_lock(store, mode, max_age=5400):
    p = os.path.join(store, ".lock")
    if os.path.exists(p):
        try:
            d = json.load(open(p))
            age = time.time() - d.get("started", 0)
        except Exception:
            d, age = {}, max_age + 1
        if age < max_age:
            raise RunError("lock", "Another run (%s) started %d minutes ago and is still in progress." % (
                d.get("mode", "?"), age // 60))
    json.dump({"mode": mode, "started": time.time()}, open(p, "w"))


def release_lock(store):
    try:
        os.remove(os.path.join(store, ".lock"))
    except Exception:
        pass


# ------------------------------------------------------------------ email
FALLBACK_TEMPLATE = """<div style="font-family:Arial,Helvetica,sans-serif;max-width:640px;color:#222">
<div style="background:{{status_color}};color:#fff;padding:14px 18px;font-size:16px"><b>{{status_word}}</b> - {{company}} trial balance by entity</div>
<div style="padding:14px 18px;border:1px solid #ddd;border-top:0">
<p style="margin:0 0 8px 0">{{headline_text}}</p>
{{{numbers_html}}}{{{warnings_html}}}{{{error_html}}}
<table style="font-size:13px;margin-top:10px"><tr><td style="color:#666;padding-right:12px">Run</td><td>{{run_type}} - {{run_time}}</td></tr>
<tr><td style="color:#666">Period</td><td>{{period}} ({{basis}})</td></tr>
<tr><td style="color:#666">Output</td><td>{{output_path}}</td></tr>
<tr><td style="color:#666">Last good run</td><td>{{last_success}}</td></tr>
<tr><td style="color:#666">Next scheduled run</td><td>{{next_run}}</td></tr></table>
</div></div>"""


def render(tpl, vals):
    tpl = re.sub(r"\{\{\{(\w+)\}\}\}", lambda m: str(vals.get(m.group(1), "")), tpl)
    return re.sub(r"\{\{(\w+)\}\}", lambda m: html.escape(str(vals.get(m.group(1), ""))), tpl)


def outlook_safe_html(vals, info, cfg):
    """Plain HTML that survives Outlook's sanitiser (allowed: p, br, b, ul, li, a, table/tr/td, h-tags; stripped: style, span, img, div)."""
    e = html.escape
    parts = ["<p><b>%s</b> - %s trial balance by entity</p>" % (e(vals["status_word"]), e(vals["company"])),
             "<p>%s</p>" % e(vals["headline_text"])]
    t = info.get("totals")
    if t and cfg["email"].get("include_numbers", True):
        rep = cfg["reporting_currency"]
        parts.append("<table>" + "".join('<tr><td>%s</td><td align="right"><b>%s %s</b></td></tr>' % (k, num(v), rep) for k, v in (
            ("Total assets", t["assets"]), ("Total liabilities", t["liabilities"]),
            ("Total equity", t["equity"]), ("Net income (profit +)", t["net_income"]))) + "</table>")
    if info.get("warnings"):
        parts.append("<p><b>Please check</b></p><ul>" + "".join("<li>%s</li>" % e(w) for w in info["warnings"][:10]) + "</ul>")
    if info["status"] == "FAILED":
        det = "".join("<li>%s</li>" % e(("%s: %s" % (d.get("file", ""), d.get("detail", ""))) if isinstance(d, dict) else str(d))
                      for d in info.get("details", [])[:12])
        parts.append("<p><b>What went wrong (step: %s)</b><br>%s</p><ul>%s</ul><p>Nothing was overwritten. The next run will try again.</p>" % (
            e(info.get("step", "") or ""), e(info.get("message", "") or ""), det))
    parts.append("<p>Run: %s - %s<br>Period: %s (%s)<br>Saved to: %s<br>Last good run: %s<br>Next scheduled run: %s</p>" % (
        e(vals["run_type"]), e(vals["run_time"]), e(vals["period"]), e(vals["basis"]), e(vals["output_path"]),
        e(vals["last_success"]), e(vals["next_run"])))
    parts.append("<!--LINKS-->")
    return "\n".join(parts)


def num(x):
    return "{:,.0f}".format(x)


def build_email(store, cfg, info):
    em = cfg["email"]
    if em.get("provider") == "none" and info["status"] != "FAILED":
        return None
    if info["status"] in ("NO_CHANGE", "UP_TO_DATE") and not em.get("notify_no_change", True):
        return None
    word = {"SUCCESS": "OK", "SUCCESS_WITH_WARNINGS": "CHECK", "NO_CHANGE": "NO CHANGE",
            "UP_TO_DATE": "NO CHANGE", "FAILED": "FAILED"}[info["status"]]
    color = {"OK": "#2E7D32", "CHECK": "#B26A00", "NO CHANGE": "#546E7A", "FAILED": "#C62828"}[word]
    numbers = ""
    t = info.get("totals")
    if t and em.get("include_numbers", True):
        rep = cfg["reporting_currency"]
        numbers = ('<table style="border-collapse:collapse;font-size:14px;margin:8px 0 4px 0">'
                   + "".join('<tr><td style="padding:3px 18px 3px 0;color:#555">%s</td><td style="text-align:right"><b>%s %s</b></td></tr>' % (
                       k, num(v), rep) for k, v in (("Total assets", t["assets"]), ("Total liabilities", t["liabilities"]),
                                                      ("Total equity", t["equity"]), ("Net income (profit +)", t["net_income"])))
                   + "</table>")
    warn = ""
    if info.get("warnings"):
        warn = ('<div style="background:#FFF4D6;border-left:4px solid #E0A100;padding:8px 12px;margin:10px 0;font-size:13px"><b>Please check</b><ul style="margin:6px 0 0 18px;padding:0">'
                + "".join("<li>%s</li>" % html.escape(w) for w in info["warnings"][:10]) + "</ul></div>")
    err = ""
    if info["status"] == "FAILED":
        det = "".join("<li>%s</li>" % html.escape(("%s: %s" % (d.get("file", ""), d.get("detail", ""))) if isinstance(d, dict) else str(d))
                      for d in info.get("details", [])[:12])
        err = ('<div style="background:#FDE7E7;border-left:4px solid #C62828;padding:8px 12px;margin:10px 0;font-size:13px">'
               "<b>What went wrong (step: %s)</b><br>%s<ul style=\"margin:6px 0 0 18px;padding:0\">%s</ul>"
               "Nothing was overwritten. The next run will try again.</div>" % (
                   html.escape(info.get("step", "")), html.escape(info.get("message", "")), det))
    sched = cfg["schedule"]
    vals = {
        "status_word": word, "status_color": color, "company": cfg.get("company_name") or "Company",
        "run_type": info["run_type"], "run_time": info["run_time"], "period": info.get("period") or "-",
        "basis": info.get("basis") or "-", "output_path": info.get("output_path") or "-",
        "last_success": last_success(store), "headline_text": info["headline"],
        "next_run": "%s at %s" % (sched.get("days", "daily"), sched.get("time", "")) if sched.get("created") else "not scheduled",
        "numbers_html": numbers, "warnings_html": warn, "error_html": err,
    }
    tp = os.path.join(store, "Templates", "email.html")
    tpl = open(tp).read() if os.path.exists(tp) else FALLBACK_TEMPLATE
    subj = render(em.get("subject") or DEFAULT_SUBJECT, vals)
    text = "%s\n%s\nPeriod: %s (%s)\nOutput: %s\nLast good run: %s\n" % (
        subj, info["headline"], vals["period"], vals["basis"], vals["output_path"], vals["last_success"])
    if info.get("warnings"):
        text += "Check: " + "; ".join(info["warnings"][:6]) + "\n"
    if info["status"] == "FAILED":
        text += "Error (%s): %s\n" % (info.get("step"), info.get("message"))
    payload = {"provider": em.get("provider"), "to": em.get("to", []), "cc": em.get("cc", []), "subject": subj,
               "html": render(tpl, vals), "text": text, "attach": [], "payload_file": os.path.join(store, ".state", "email_payload.json")}
    payload["outlook_html"] = outlook_safe_html(vals, info, cfg)
    payload["outlook_body_type"] = "html"
    payload["links"] = []
    if em.get("attach_workbook") and info.get("output_file") and os.path.getsize(info["output_file"]) < 15 * 1024 * 1024:
        payload["attach"] = [info["output_file"]]
    json.dump(payload, open(payload["payload_file"], "w"))
    return payload


# ------------------------------------------------------------------ store
def cmd_init(a):
    store = a.store
    for d in ("Baseline", "Results", "Templates", "Logs", ".state", ".engine"):
        os.makedirs(os.path.join(store, d), exist_ok=True)
    for f in glob.glob(os.path.join(HERE, "*.py")):
        shutil.copy(f, os.path.join(store, ".engine", os.path.basename(f)))
    tpl = os.path.join(HERE, "..", "templates", "email.html")
    dst = os.path.join(store, "Templates", "email.html")
    if not os.path.exists(dst):
        if os.path.exists(tpl):
            shutil.copy(tpl, dst)
        else:
            open(dst, "w").write(FALLBACK_TEMPLATE)
    open(os.path.join(store, "README.txt"), "w").write(
        "tb-rollforward store folder\n  config.json  settings (edit via the skill, or by hand)\n  Baseline/    the saved month-end snapshot "
        "(previous one kept in _previous/)\n  Results/     one folder per day with the Excel files\n  Templates/   email.html - edit the look of the email\n"
        "  Logs/        run_log.txt\n  .state/      caches; safe to delete (forces a full re-read)\n")
    out({"status": "ok", "store": store})


def cmd_config_write(a):
    store = a.store
    p = os.path.join(store, "config.json")
    cur = json.load(open(p)) if os.path.exists(p) else {}
    new = json.load(open(a.json))
    cfg = deep_merge(deep_merge(DEFAULT_CFG, cur), new)
    errs = validate_config(cfg)
    if errs:
        out({"status": "invalid", "errors": errs}, 2)
    tmp = p + ".tmp"
    json.dump(cfg, open(tmp, "w"), indent=2)
    os.replace(tmp, p)
    out({"status": "ok", "path": p})


MONTHS_ = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]


def _lines(v):
    return [x.strip().strip('"').strip("'") for x in re.split(r"[\n;]+", str(v or "")) if x.strip()]


def _emails(v):
    return [x for x in re.split(r"[,;\s]+", str(v or "")) if x]


def answers_to_cfg(form, a):
    """Form answers (keys = the form's data-name attributes) -> partial config."""
    g = lambda k, d="": (a.get(k) if a.get(k) not in (None, "") else d)
    new = {}
    if form == "setup":
        new["company_name"] = str(g("company")).strip()
        cur = str(g("reporting_currency", "USD")).strip().upper()
        new["reporting_currency"] = cur[:3]
        fy = str(g("fy_start", "January")).strip().lower()
        new["fiscal_year_start_month"] = (MONTHS_.index(fy) + 1) if fy in MONTHS_ else (int(fy) if fy.isdigit() else 1)
        led = "netsuite" if "netsuite" in str(g("ledger_source")).lower() else "files"
        rs = str(g("reference_source", "Same as ledger")).lower()
        ref = led if rs.startswith("same") else ("netsuite" if "netsuite" in rs else "files")
        new["sources"] = {"ledger": {"type": led}, **{d: {"type": ref} for d in ("accounts", "entities", "fx", "periods")}}
    elif form == "paths_files":
        mode = "connector" if "connector" in str(g("access_mode")).lower() else "synced"
        src = {}
        for ds, key in (("ledger", "ledger_paths"), ("accounts", "accounts_paths"), ("entities", "entities_paths"),
                        ("fx", "fx_paths"), ("periods", "periods_paths")):
            src[ds] = {"paths": _lines(g(key)), "mode": mode}
        new["sources"] = src
        ct = str(g("closed_through")).strip()
        if ct:
            new["closed_through"] = ct
        if not src["periods"]["paths"] and ct:
            src["periods"]["type"] = "none"
        new["sign_convention"] = "credit_positive" if "credits positive" in str(g("sign")).lower() and "debits" not in str(g("sign")).lower() else "debit_positive"
        new["decimal_separator"] = "," if str(g("decimal")).startswith("1.234") else "."
    elif form == "paths_netsuite":
        subs = str(g("subsidiaries", "all")).strip().lower()
        ns = {"subsidiaries": [] if subs in ("", "all") else [x for x in re.split(r"[,\s]+", subs) if x]}
        for k, f in (("accounting_book", "accounting_book"), ("root_subsidiary", "root_subsidiary")):
            m = re.match(r"\s*(\d+)", str(g(f, "1")))
            ns[k] = int(m.group(1)) if m else 1
        hs = str(g("history_start")).strip()
        if hs:
            ns["history_start"] = hs
        new["netsuite"] = ns
    elif form == "delivery":
        pv = str(g("email_provider", "Gmail")).lower()
        new["email"] = {"provider": "none" if pv.startswith("no") else ("outlook" if "outlook" in pv else "gmail"),
                        "to": _emails(g("email_to")), "cc": _emails(g("email_cc")),
                        "include_numbers": str(g("include_numbers", "Yes")).lower().startswith("y"),
                        "attach_workbook": str(g("attach", "No")).lower().startswith("y"),
                        "notify_no_change": str(g("notify_no_change", "Yes")).lower().startswith("y")}
        sd = str(g("save_to_drive", "No")).lower()
        prov = "gdrive" if "google" in sd else ("sharepoint" if ("sharepoint" in sd or "onedrive" in sd) else "none")
        new["drive"] = {"provider": prov, "parent": str(g("drive_parent", "")).strip(), "folder_pattern": "TB Rollforward {date}"}
        rt = str(g("run_time", "08:00")).strip()
        m = re.match(r"^(\d{1,2})[:.]?(\d{2})?", rt)
        hh, mm = (int(m.group(1)), int(m.group(2) or 0)) if m else (8, 0)
        new["schedule"] = {"time": "%02d:%02d" % (hh, mm), "days": "daily" if "every" in str(g("run_days")).lower() else "weekdays"}
    elif form == "mapping":
        src = {}
        for k, v in a.items():
            m = re.match(r"^map__(\w+?)__(\w+)$", k)
            if m and str(v).strip() and str(v).strip().lower() != "not in my file":
                src.setdefault(m.group(1), {"columns": {}})["columns"][m.group(2)] = str(v).strip()
        new["sources"] = src
    else:
        raise RunError("config", "unknown form %s" % form)
    return new


def cmd_apply_answers(a):
    p = os.path.join(a.store, "config.json")
    cur = json.load(open(p)) if os.path.exists(p) else {}
    new = answers_to_cfg(a.form, json.load(open(a.answers)))
    if a.store_host:
        new["store_host_path"] = a.store_host
    cfg = deep_merge(deep_merge(DEFAULT_CFG, cur), new)
    # email may be incomplete until the delivery form has been answered: validate only what is present
    errs = [e for e in validate_config(cfg) if not (a.form != "delivery" and ("email" in e))]
    if errs:
        out({"status": "invalid", "errors": errs}, 2)
    tmp = p + ".tmp"
    json.dump(deep_merge(cur, new), open(tmp, "w"), indent=2)
    os.replace(tmp, p)
    out({"status": "ok", "applied": new})


def cmd_schedule_info(a):
    cfg = load_config(a.store)
    sc = cfg["schedule"]
    hh, mm = sc["time"].split(":")
    cron = "%d %d * * %s" % (int(mm), int(hh), "1-5" if sc["days"] == "weekdays" else "*")
    host = cfg.get("store_host_path") or ""
    if not host:
        raise RunError("config", "store_host_path is empty: pass --store-host to apply-answers (the folder's real path on the computer).")
    prompt = ("mode: scheduled. config: %s/config.json. recipient: %s. Run the tb-rollforward skill end to end in scheduled mode: "
              "never ask any question; follow the skill's scheduled-run steps exactly; if anything blocks before the engine can run, "
              "email the recipient a short failure notice." % (host, ", ".join(cfg["email"]["to"]) or "none"))
    out({"taskId": sc["task_id"], "cron": cron, "title": "Trial balance by entity (%s at %s)" % (sc["days"], sc["time"]),
         "description": "Daily trial-balance roll-forward for %s: read sources, build workbook, email result." % (cfg.get("company_name") or "company"),
         "prompt": prompt})


def cmd_config_show(a):
    out(load_config(a.store))


def cmd_map_path(a):
    pm = load_pathmap(a.store)
    pm[a.host] = a.sandbox
    os.makedirs(os.path.join(a.store, ".state"), exist_ok=True)
    json.dump(pm, open(os.path.join(a.store, ".state", "pathmap.json"), "w"), indent=1)
    out({"status": "ok", "map": pm})


# ------------------------------------------------------------------ inspect
def cmd_inspect(a):
    store = a.store
    if a.config:
        cfg = deep_merge(DEFAULT_CFG, json.load(open(a.config)))
    else:
        cfg = load_config(store)
    pm = load_pathmap(store)
    res = {"datasets": {}, "problems": []}
    errs = []
    for ds in ("ledger", "accounts", "entities", "fx", "periods"):
        if cfg["sources"][ds].get("type") == "none":
            continue
        files = S.list_files(ds, cfg, store, pm, errs)
        res["datasets"][ds] = {"files": [S.inspect_file(ds, full, key, cfg) for key, full in files]}
    res["problems"] = errs
    # content summaries (only when the headers map cleanly)
    e2, w2 = [], []
    try:
        ing = S.ingest.__wrapped__ if hasattr(S.ingest, "__wrapped__") else None
    except Exception:
        ing = None
    summ = {}
    for ds in ("accounts", "entities", "fx", "periods"):
        rows = []
        for key, full in S.list_files(ds, cfg, store, pm, []):
            r = S.parse_reference(ds, full, key, cfg, e2, w2)
            if r:
                rows += r
        summ[ds] = rows
    if summ["accounts"]:
        tm = {k.lower().strip(): v for k, v in cfg["sources"]["accounts"].get("type_map", {}).items()}
        types = {}
        for r in summ["accounts"]:
            cls = tm.get(r["type_raw"].lower().strip()) or S.classify_account(r["type_raw"], r["name"])
            types.setdefault(r["type_raw"], cls)
        res["account_types"] = types
        res["accounts_unclassified"] = [t for t, c in types.items() if c is None]
    if summ["entities"]:
        res["entities"] = [{"entity": r["entity"], "currency": r["currency"], "parent": r["parent"]} for r in summ["entities"]]
    if summ["fx"]:
        res["fx_summary"] = {"currencies": sorted({r["currency"] for r in summ["fx"]}),
                             "periods": [min(r["period"] for r in summ["fx"]), max(r["period"] for r in summ["fx"])]}
    if summ["periods"]:
        res["periods_summary"] = {"closed": sorted(r["period"] for r in summ["periods"] if r["status"] == "closed")[-3:],
                                  "open": sorted(r["period"] for r in summ["periods"] if r["status"] == "open")}
    lg = {}
    for key, full in S.list_files("ledger", cfg, store, pm, []):
        g = S.parse_ledger_file(full, key, cfg, e2, w2)
        for (per, ent), acc in (g or {}).items():
            lg.setdefault("entities", set()).add(ent)
            lg.setdefault("periods", set()).add(per)
            lg.setdefault("accounts", set()).update(acc)
    if lg:
        res["ledger_summary"] = {"entities": sorted(lg["entities"]), "periods": sorted(lg["periods"]),
                                 "accounts": len(lg["accounts"])}
        ents = {r["entity"] for r in summ["entities"]}
        accs = {r["account"] for r in summ["accounts"]}
        if ents:
            res["ledger_entities_not_in_entities_list"] = sorted(lg["entities"] - ents)
        if accs:
            res["ledger_accounts_not_in_accounts_list"] = sorted(lg["accounts"] - accs)[:30]
        if summ["fx"] and summ["entities"]:
            have = {(r["currency"], r["period"]) for r in summ["fx"]}
            ccy = {r["entity"]: (r["currency"] or cfg["reporting_currency"]) for r in summ["entities"]}
            miss = sorted({"%s %s" % (ccy.get(e, "?"), p) for p in lg["periods"] for e in lg["entities"]
                           if ccy.get(e, cfg["reporting_currency"]) != cfg["reporting_currency"]
                           and (ccy.get(e), p) not in have})
            res["fx_missing"] = miss[:30]
    res["parse_errors"] = e2
    res["parse_warnings"] = w2
    out(res)


# ------------------------------------------------------------------ core pipeline
def prune_cache(store, cutoff):
    lp = os.path.join(store, ".state", "ledger_cache.json")
    if not os.path.exists(lp):
        return
    c = json.load(open(lp))
    for gk in [g for g in c["groups"] if g.split("|")[0] <= cutoff]:
        del c["groups"][gk]
    inbox = os.path.join(store, ".state", "inbox", "ledger")
    for key in list(c["files"]):
        if key.startswith("inbox:ns_") and not [g for g in c["files"][key]["groups"] if g in c["groups"]]:
            try:
                os.remove(os.path.join(inbox, key.split(":", 1)[1]))
                del c["files"][key]
            except Exception:
                pass
    json.dump(c, open(lp, "w"))


def make_baseline(ctx, base, months, bal, ledger):
    nb = E.new_baseline_shell(ctx)
    nb["cutoff"] = months[-1] if months else base["cutoff"]
    nb["bal"] = bal
    nb["created_at"] = dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    pc = copy.deepcopy(base.get("period_controls", {})) if base else {}
    fc = copy.deepcopy(base.get("fx_controls", {})) if base else {}
    for gk, g in ledger["groups"].items():
        per, ent = gk.split("|", 1)
        if per in months:
            pc.setdefault(per, {})[ent] = g["fp"]
    for (ccy, per), r in ctx["fx"].d.items():
        if per in months:
            fc.setdefault(per, {})[ccy] = [r[0], r[1], r[2]]
    for dct in (pc, fc):
        for k in sorted(dct)[:-36]:
            del dct[k]
    nb["period_controls"], nb["fx_controls"] = pc, fc
    return nb


def out_name(asof, now, prelim):
    return "TB_by_entity_%s_%s%s.xlsx" % (E.month_label(asof), now.strftime("%Y-%m-%d_%H%M"), "_PRELIMINARY" if prelim else "")


def run_pipeline(store, cfg, mode, force, accept_removed, info):
    now = now_local(cfg)
    ts = time.time()
    pm = load_pathmap(store)
    base, _ = E.load_baseline(store)
    if base is None:
        raise RunError("baseline", "No baseline found in Baseline/. First-time setup must create one "
                       "(interactive: 'bootstrap').")
    if accept_removed:
        cfg["_accept_removed"] = True
    ing = S.ingest(store, cfg, pm, ts, base)
    info["ingest"] = {k: ing[k] for k in ("ledger_files", "ledger_files_changed", "ledger_files_unsettled", "groups", "reference_changed", "counts")}
    if ing["errors"]:
        raise RunError("read data", "The source data has problems; nothing was changed.", ing["errors"])
    warnings = [w["detail"] if not w.get("file") else "%s: %s" % (w["file"], w["detail"]) for w in ing["warnings"]]
    ref = json.load(open(os.path.join(store, ".state", "ref_cache.json")))
    ledger = json.load(open(os.path.join(store, ".state", "ledger_cache.json")))
    ctx = E.build_ctx(cfg, ref)
    if ctx["errs"]:
        raise RunError("reference data", "Reference data problems", ctx["errs"])
    warnings += [w["detail"] for w in ctx["warns"] if w["code"] != "unknown_account_type"] + sorted(ctx["fx"].notes)
    refs = E.check_ledger_refs(ctx, ledger, base["cutoff"])
    if refs:
        raise RunError("read data", "Ledger rows use entities/accounts that are not in your lists.", refs)
    plan = E.plan_legs(ctx, base, ledger)
    warnings += plan["warnings"]
    drift = ing["drift"]
    if drift:
        warnings.append("%d closed-month figure(s) changed in the source since the baseline was saved. "
                        "Re-run first-time setup with 'rebuild baseline' if this is unexpected." % len(drift))
    fin, pre = plan["final"], plan["prelim"]
    if not fin and not pre:
        info.update(status="UP_TO_DATE", headline="No new months since the baseline (%s). Nothing to do." % base["cutoff"],
                    period=base["cutoff"], basis="FINAL", warnings=warnings)
        return
    ls_path = os.path.join(store, ".state", "last_success.json")
    last = json.load(open(ls_path)) if os.path.exists(ls_path) else {}
    fps = {"final": E.input_fp(ctx, base, ledger, fin, ref) if fin else None,
           "prelim": E.input_fp(ctx, base, ledger, pre, ref) if pre else None}
    if not force and last.get("fps") == fps:
        info.update(status="NO_CHANGE", headline="Source data unchanged since the last run. No new workbook.",
                    period=(pre or fin)[-1], basis="PRELIMINARY" if pre else "FINAL",
                    warnings=last.get("warnings", []), output_path=last.get("output_path"))
        return
    day = os.path.join(store, "Results", now.strftime("%Y-%m-%d"))
    os.makedirs(day, exist_ok=True)
    tmpdir = os.path.join(store, ".state", "out")
    os.makedirs(tmpdir, exist_ok=True)
    bal = copy.deepcopy(base["bal"])
    outputs, notes, head_tr = [], [], None
    details_common = [("Baseline month", base["cutoff"]), ("Source files changed", len(ing["ledger_files_changed"])),
                      ("Reference tables changed", ", ".join(ing["reference_changed"]) or "none")]

    def do_leg(months, prelim):
        nonlocal bal, head_tr
        E.apply_months(bal, months, ctx, ledger)
        asof = months[-1]
        tr = E.translate(bal, ctx, asof)
        checks, w = E.integrity_checks(bal, tr, ctx, cfg["balance_tolerance"], cfg["strict_balance"])
        if any(c["status"] == "fail" for c in checks):
            raise RunError("validation", "Integrity check failed; nothing published.",
                           [{"file": c["scope"], "detail": "%s: %s" % (c["name"], c["detail"])} for c in checks if c["status"] == "fail"])
        ents = sorted(tr)
        roll = E.hierarchy(ctx, set(ents))
        meta = {"company": cfg.get("company_name"), "asof": asof, "basis": "PRELIMINARY" if prelim else "FINAL",
                "run_time": now.strftime("%Y-%m-%d %H:%M %Z").strip(), "run_type": mode.capitalize(),
                "details": details_common + [("Months added to baseline", ", ".join(months)),
                                             ("Entities", len(ents))]}
        fname = out_name(asof, now, prelim)
        tmp = os.path.join(tmpdir, fname)
        R.write_workbook(tmp, meta, tr, ctx, roll, checks, warnings + w, drift)
        final = os.path.join(day, fname)
        os.replace(tmp, final)
        outputs.append({"file": final, "asof": asof, "prelim": prelim})
        head_tr = tr
        return w

    nbal = None
    if fin:
        ws = do_leg(fin, False)
        warnings += ws
        nb = make_baseline(ctx, base, fin, copy.deepcopy(bal), ledger)
        newpath, bn = E.save_baseline(store, nb, cfg["baseline"]["keep_previous"])
        prune_cache(store, fin[-1])
        notes += bn
        notes.append("Baseline advanced to %s" % fin[-1])
    if pre:
        try:
            ws = do_leg(pre, True)
            warnings += ws
        except RunError as e:
            if not fin:
                raise
            warnings.append("The preliminary (open-month) workbook failed: %s" % e.msg)
    if notes:
        warnings += [n for n in notes if "advanced" not in n]
    t = E.totals([r for rows in head_tr.values() for r in rows])
    last_out = outputs[-1]
    info.update(status="SUCCESS_WITH_WARNINGS" if warnings or drift else "SUCCESS", warnings=warnings,
                totals=t, period=last_out["asof"], basis="PRELIMINARY" if last_out["prelim"] else "FINAL",
                output_path=", ".join(os.path.relpath(o["file"], store) for o in outputs), output_file=last_out["file"],
                headline="Trial balance for %d entities is ready%s." % (len(head_tr), " (includes open months: preliminary)" if last_out["prelim"] else ""),
                outputs=[o["file"] for o in outputs], notes=notes)
    if fin:   # baseline moved: fingerprints for what is left (open months) must use the NEW baseline
        fps = {"final": None, "prelim": E.input_fp(ctx, nb, ledger, pre, ref) if pre else None}
    json.dump({"fps": fps, "time": now.isoformat(), "output_path": info["output_path"], "warnings": warnings},
              open(ls_path, "w"))


def write_failure(store, cfg, e, mode, info):
    now = now_local(cfg)
    day = os.path.join(store, "Results", now.strftime("%Y-%m-%d"))
    try:
        os.makedirs(day, exist_ok=True)
        with open(os.path.join(day, "RUN_FAILED_%s.txt" % now.strftime("%H%M")), "w") as f:
            f.write("Step: %s\nMessage: %s\n" % (e.step, e.msg))
            for d in e.details:
                f.write("  - %s\n" % (("%s: %s" % (d.get("file", ""), d.get("detail", ""))) if isinstance(d, dict) else d))
    except Exception:
        pass


def cmd_run(a):
    store = a.store
    mode = a.mode
    info = {"run_type": mode.capitalize(), "status": None, "warnings": []}
    cfg = None
    locked = False
    try:
        cfg = load_config(store)
        info["run_time"] = now_local(cfg).strftime("%Y-%m-%d %H:%M %Z").strip()
        if mode == "scheduled" and not a.force:
            today = now_local(cfg).strftime("%Y-%m-%d")
            if any(r[0].startswith(today) and r[1] in DONE for r in read_log(store)):
                out({"status": "SKIPPED", "reason": "already completed today", "email": None})
        try:
            acquire_lock(store, mode)
            locked = True
        except RunError as e:
            out({"status": "SKIPPED", "reason": e.msg, "email": None})
        run_pipeline(store, cfg, mode, a.force, a.accept_removed, info)
    except RunError as e:
        info.update(status="FAILED", step=e.step, message=e.msg, details=e.details, headline="The run did not complete.")
        if cfg:
            write_failure(store, cfg, e, mode, info)
    except Exception as e:
        tb = traceback.format_exc().splitlines()[-4:]
        info.update(status="FAILED", step="unexpected", message="%s: %s" % (type(e).__name__, e), details=tb,
                    headline="The run did not complete (unexpected error).")
        if cfg:
            write_failure(store, cfg, RunError("unexpected", info["message"], tb), mode, info)
    finally:
        if locked:
            release_lock(store)
    code = 0
    if cfg is None:   # config unreadable: still return something the agent can email from the task prompt
        info.setdefault("run_time", dt.datetime.now().strftime("%Y-%m-%d %H:%M"))
        out({"status": "FAILED", "step": info.get("step"), "message": info.get("message"), "details": info.get("details"), "email": None}, 2)
    log(store, cfg, info["status"], mode, info.get("message") or "%s | %s" % (info.get("period"), info.get("output_path")))
    payload = build_email(store, cfg, info)
    pend = os.path.join(store, ".state", "pending_email.json")
    res = {k: v for k, v in info.items() if k not in ("totals", "ingest")}
    res["totals"] = info.get("totals")
    res["ingest"] = info.get("ingest")
    res["email"] = payload
    res["pending_email"] = json.load(open(pend)) if os.path.exists(pend) else None
    out(res, 2 if info["status"] == "FAILED" else 0)


# ------------------------------------------------------------------ bootstrap
def cmd_bootstrap(a):
    store = a.store
    cfg = load_config(store)
    info = {}
    try:
        existing, _ = E.load_baseline(store)
        if existing and not a.force:
            raise RunError("bootstrap", "A baseline already exists (%s). Use --force to rebuild it." % existing["cutoff"])
        pm = load_pathmap(store)
        ing = S.ingest(store, cfg, pm, time.time(), None)
        if ing["errors"]:
            raise RunError("read data", "The source data has problems.", ing["errors"])
        ref = json.load(open(os.path.join(store, ".state", "ref_cache.json")))
        ledger = json.load(open(os.path.join(store, ".state", "ledger_cache.json")))
        ctx = E.build_ctx(cfg, ref)
        if ctx["errs"]:
            raise RunError("reference data", "Reference data problems", ctx["errs"])
        refs = E.check_ledger_refs(ctx, ledger, None)
        if refs:
            raise RunError("read data", "Ledger rows use entities/accounts that are not in your lists.", refs)
        pers = sorted({k.split("|")[0] for k in ledger["groups"]})
        if not pers:
            raise RunError("bootstrap", "No ledger rows found.")
        if a.through < pers[0]:
            raise RunError("bootstrap", "--through %s is before the first month of data (%s)." % (a.through, pers[0]))
        months = E.prange(pers[0], a.through)
        bal = {}
        E.apply_months(bal, months, ctx, ledger)
        tr = E.translate(bal, ctx, a.through)
        checks, w = E.integrity_checks(bal, tr, ctx, cfg["balance_tolerance"], cfg["strict_balance"])
        if any(c["status"] == "fail" for c in checks):
            raise RunError("validation", "Opening history does not balance.",
                           [{"file": c["scope"], "detail": c["detail"]} for c in checks if c["status"] == "fail"])
        nb = make_baseline(ctx, None, months, bal, ledger)
        path, notes = E.save_baseline(store, nb, cfg["baseline"]["keep_previous"])
        prune_cache(store, a.through)
        log(store, cfg, "BASELINE_CREATED", "interactive", "cutoff %s, %d entities, %d months" % (a.through, len(bal), len(months)))
        t = E.totals([r for rows in tr.values() for r in rows])
        out({"status": "ok", "baseline": path, "cutoff": a.through, "months": len(months), "entities": len(bal),
             "warnings": w + [x["detail"] for x in ing["warnings"]] + sorted(ctx["fx"].notes), "notes": notes,
             "unbalanced_entities": [c["scope"] for c in checks if c["status"] != "ok"], "consolidated": t})
    except RunError as e:
        out({"status": "FAILED", "step": e.step, "message": e.msg, "details": e.details}, 2)


# ------------------------------------------------------------------ NetSuite helpers
def cmd_ns_diff(a):
    store = a.store
    lp = os.path.join(store, ".state", "ledger_cache.json")
    c = json.load(open(lp)) if os.path.exists(lp) else {"files": {}, "groups": {}}
    base, _ = E.load_baseline(store)
    cutoff = base["cutoff"] if base else ""
    remote = {}
    for r in csv.DictReader(open(a.controls)):
        remote["%s|%s" % (S.norm_period(r["period"]) or r["period"], r["entity"])] = [int(float(r["n"])), float(r["sum"]), float(r["abs"])]
    pull, stale = [], []
    for gk, fp in remote.items():
        if gk.split("|")[0] <= cutoff:
            continue
        g = c["groups"].get(gk)
        if not g or g["fp"][0] != fp[0] or abs(g["fp"][1] - fp[1]) > 0.01 or abs(g["fp"][2] - fp[2]) > 0.01:
            pull.append(gk)
    for gk in list(c["groups"]):
        if gk.split("|")[0] > cutoff and gk not in remote:
            stale.append(gk)
            f = c["groups"].pop(gk)["file"]
            c["files"].pop(f, None)
            try:
                os.remove(os.path.join(store, ".state", "inbox", "ledger", f.split(":", 1)[1]))
            except Exception:
                pass
    json.dump(c, open(lp, "w"))
    out({"pull": [{"period": g.split("|")[0], "entity": g.split("|", 1)[1],
                   "file": "ns_%s_%s.csv" % (g.split("|")[0], re.sub(r"[^A-Za-z0-9_.-]", "_", g.split("|", 1)[1]))} for g in sorted(pull)],
         "removed_from_cache": stale, "unchanged": len(remote) - len(pull)})


# ------------------------------------------------------------------ misc
def cmd_email_sent(a):
    cfg = load_config(a.store)
    pend = os.path.join(a.store, ".state", "pending_email.json")
    payload_file = os.path.join(a.store, ".state", "email_payload.json")
    if a.status == "sent":
        if os.path.exists(pend):
            os.remove(pend)
        log(a.store, cfg, "EMAIL_SENT", "-", "")
    else:
        if os.path.exists(payload_file):
            shutil.copy(payload_file, pend)
            day = os.path.join(a.store, "Results", now_local(cfg).strftime("%Y-%m-%d"))
            os.makedirs(day, exist_ok=True)
            p = json.load(open(payload_file))
            open(os.path.join(day, "EMAIL_FAILED_%s.txt" % now_local(cfg).strftime("%H%M")), "w").write(
                "The email could not be sent (%s).\n\n%s\n\n%s\n" % (a.error or "unknown error", p["subject"], p["text"]))
        log(a.store, cfg, "EMAIL_FAILED", "-", a.error or "")
    out({"status": "ok"})


def cmd_email_add_link(a):
    """Insert the workbook / drive-folder link(s) into the pending email (all body variants), before it is sent."""
    pf = os.path.join(a.store, ".state", "email_payload.json")
    if not os.path.exists(pf):
        raise RunError("email", "no email payload to add a link to (run first)")
    p = json.load(open(pf))
    label = a.label or "Trial balance workbook"
    e = html.escape
    link_html = '<p>%s: <a href="%s">%s</a></p>' % (e(label), e(a.url, quote=True), e(a.url))
    link_text = "%s: %s\n" % (label, a.url)
    if a.folder_url:
        link_html += '<p>All files (folder): <a href="%s">%s</a></p>' % (e(a.folder_url, quote=True), e(a.folder_url))
        link_text += "All files (folder): %s\n" % a.folder_url
    p["links"] = p.get("links", []) + [{"label": label, "url": a.url, "folder_url": a.folder_url}]
    for k in ("html", "outlook_html"):
        if "<!--LINKS-->" in p.get(k, ""):
            p[k] = p[k].replace("<!--LINKS-->", link_html + "<!--LINKS-->")
        else:
            p[k] = p.get(k, "") + link_html
    p["text"] = p["text"] + link_text
    json.dump(p, open(pf, "w"))
    out({"status": "ok", "email": p})


def cmd_drive_plan(a):
    cfg = load_config(a.store)
    dv = cfg.get("drive", {})
    ls = os.path.join(a.store, ".state", "last_success.json")
    if not os.path.exists(ls):
        raise RunError("drive", "no successful run yet - nothing to save")
    last = json.load(open(ls))
    day_dir = os.path.dirname(os.path.join(a.store, last["output_path"]))
    day = os.path.basename(day_dir)
    name = (dv.get("folder_pattern") or "TB Rollforward {date}").replace("{date}", day).replace("{company}", cfg.get("company_name", ""))
    files = [os.path.abspath(os.path.join(day_dir, f)) for f in sorted(os.listdir(day_dir)) if f.lower().endswith(".xlsx") and not f.startswith("~")]
    out({"status": "ok", "provider": dv.get("provider", "none"), "parent": dv.get("parent", ""), "folder_name": name,
         "files": files, "mime": {"xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
         "steps": ["1 create the folder first (parent above)", "2 upload every file into that folder", "3 get the folder link and the workbook link",
                   "4 tbr.py email-add-link --url <workbook link> --folder-url <folder link>", "5 send the email"]})


CONNECTOR_PROBES = {
    "microsoft365": {"name": "Microsoft 365 (SharePoint / OneDrive / Outlook)", "probe": "get_me, then read_resource drive:///users/me", "search": ["microsoft 365", "outlook", "sharepoint"]},
    "gmail": {"name": "Gmail", "probe": "list labels", "search": ["gmail", "google mail"]},
    "gdrive": {"name": "Google Drive", "probe": "list_recent_files (limit 1)", "search": ["google drive", "drive"]},
    "netsuite": {"name": "NetSuite", "probe": "SuiteQL: SELECT id FROM subsidiary WHERE id = 1", "search": ["netsuite"]},
}


def cmd_preflight(a):
    need = set(x.strip() for x in (a.need or "").split(",") if x.strip())
    p = os.path.join(a.store, "config.json")
    if os.path.exists(p):
        cfg = json.load(open(p))
        src = cfg.get("sources", {})
        for ds, v in src.items():
            if v.get("type") == "netsuite":
                need.add("netsuite")
            if v.get("type", "files") == "files" and v.get("mode") == "connector":
                need.add("microsoft365")
        pv = cfg.get("email", {}).get("provider")
        if pv == "outlook":
            need.add("microsoft365")
        if pv == "gmail":
            need.add("gmail")
        dp = cfg.get("drive", {}).get("provider", "none")
        if dp in ("sharepoint", "onedrive"):
            need.add("microsoft365")
        if dp == "gdrive":
            need.add("gdrive")
    bad = [n for n in need if n not in CONNECTOR_PROBES]
    if bad:
        raise RunError("preflight", "unknown connector key(s): %s" % ", ".join(bad))
    out({"status": "ok", "required": [dict(key=k, **CONNECTOR_PROBES[k]) for k in sorted(need)],
         "rule": "every required connector must answer its probe with real data; otherwise stop, search the registry, suggest_connectors and wait"})


def cmd_restore_previous(a):
    d = os.path.join(a.store, "Baseline")
    prev = sorted(glob.glob(os.path.join(d, "_previous", "baseline_????-??.json")))
    if not prev:
        out({"status": "FAILED", "message": "No previous baseline available."}, 2)
    cur = E.baseline_files(a.store)
    for c in cur:
        shutil.move(c, os.path.join(d, "_previous", os.path.basename(c) + ".rejected"))
    shutil.move(prev[-1], os.path.join(d, os.path.basename(prev[-1])))
    for f in ("ledger_cache.json", "last_success.json"):
        p = os.path.join(a.store, ".state", f)
        if os.path.exists(p):
            os.remove(p)
    out({"status": "ok", "restored": os.path.basename(prev[-1]), "note": "Cache cleared: the next run re-reads all source files."})


def cmd_status(a):
    cfg = load_config(a.store)
    b, _ = E.load_baseline(a.store)
    rows = read_log(a.store)
    out({"baseline_cutoff": b["cutoff"] if b else None, "last_success": last_success(a.store),
         "last_log": rows[-3:], "pending_email": os.path.exists(os.path.join(a.store, ".state", "pending_email.json")),
         "schedule": cfg["schedule"], "email_to": cfg["email"]["to"]})


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)

    def add(name, fn, *args):
        p = sp.add_parser(name)
        p.add_argument("--store", required=True)
        for ar, kw in args:
            p.add_argument(ar, **kw)
        p.set_defaults(fn=fn)
    add("init", cmd_init)
    add("config-write", cmd_config_write, ("--json", dict(required=True)))
    add("apply-answers", cmd_apply_answers, ("--form", dict(required=True)), ("--answers", dict(required=True)), ("--store-host", dict(default="")))
    add("schedule-info", cmd_schedule_info)
    add("config-show", cmd_config_show)
    add("map-path", cmd_map_path, ("--host", dict(required=True)), ("--sandbox", dict(required=True)))
    add("inspect", cmd_inspect, ("--config", dict(default=None)))
    add("bootstrap", cmd_bootstrap, ("--through", dict(required=True)), ("--force", dict(action="store_true")))
    add("run", cmd_run, ("--mode", dict(default="manual", choices=["manual", "scheduled"])),
        ("--force", dict(action="store_true")), ("--accept-removed", dict(action="store_true")))
    add("ns-diff", cmd_ns_diff, ("--controls", dict(required=True)))
    add("email-sent", cmd_email_sent, ("--status", dict(required=True, choices=["sent", "failed"])), ("--error", dict(default="")))
    add("email-add-link", cmd_email_add_link, ("--url", dict(required=True)), ("--label", dict(default="")), ("--folder-url", dict(default="")))
    add("drive-plan", cmd_drive_plan)
    add("preflight", cmd_preflight, ("--need", dict(default="")))
    add("restore-previous", cmd_restore_previous)
    add("status", cmd_status)
    a = ap.parse_args()
    try:
        a.fn(a)
    except RunError as e:
        out({"status": "FAILED", "step": e.step, "message": e.msg, "details": e.details}, 2)


if __name__ == "__main__":
    main()

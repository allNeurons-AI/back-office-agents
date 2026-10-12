"""sources.py - read ledger / reference data from CSV or Excel files, map columns, detect changes.

Every data source (SharePoint synced folder, connector download, NetSuite CSV export) ends up as
files. This module turns those files into one canonical shape:

  ledger   rows: (period YYYY-MM, entity, account, amount in the entity's own currency)
  accounts account -> name, type, optional rate_class
  entities entity -> currency, parent
  fx       (currency, period) -> closing, average, historical  (reporting-currency per 1 local unit)
  periods  period -> open / closed
"""
import csv, datetime as dt, fnmatch, hashlib, io, json, os, re
from collections import defaultdict

ALIASES = {
    "ledger": {
        "entity": ["entity", "subsidiary", "legalentity", "company", "entityname", "subsidiaryname",
                   "entitycode", "businessunit", "sub", "subid"],
        "account": ["account", "accountnumber", "accountid", "acct", "acctid", "glaccount",
                    "accountcode", "accountno", "accountnum", "gl", "glcode", "glnumber", "ledgeraccount",
                    "naturalaccount"],
        "period": ["period", "postingperiod", "accountingperiod", "periodname", "month", "yearmonth",
                   "ym", "fiscalperiod"],
        "date": ["date", "trandate", "postingdate", "transactiondate", "bookingdate"],
        "amount": ["amount", "netamount", "net", "activity", "localamount", "amountlocal", "amountlc",
                   "netactivity", "periodactivity", "movement", "amt"],
        "debit": ["debit", "debits", "dr", "debitamount"],
        "credit": ["credit", "credits", "cr", "creditamount"],
    },
    "accounts": {
        "account": ["account", "accountnumber", "accountid", "acct", "acctid", "glaccount",
                    "accountcode", "accountno", "accountnum", "number"],
        "name": ["name", "accountname", "description", "accountdescription", "accountsearchdisplayname"],
        "type": ["type", "accounttype", "accttype", "category", "class", "accountcategory"],
        "rate_class": ["rateclass", "ratetype", "translationrate", "generalrate", "translationtype"],
    },
    "entities": {
        "entity": ["entity", "subsidiary", "legalentity", "company", "entityname", "subsidiaryname",
                   "entitycode", "name", "sub", "subid"],
        "name": ["displayname", "fullname", "entitydescription"],
        "parent": ["parent", "parententity", "rollupto", "consolidatesinto", "parentcompany", "parentid"],
        "currency": ["currency", "ccy", "functionalcurrency", "localcurrency", "entitycurrency",
                     "currencycode", "basecurrency"],
        "is_elim": ["iselimination", "elimination", "iselim", "eliminationentity"],
    },
    "fx": {
        "currency": ["currency", "ccy", "fromcurrency", "from", "currencycode"],
        "period": ["period", "postingperiod", "month", "yearmonth", "accountingperiod", "periodname"],
        "closing": ["closing", "closingrate", "currentrate", "current", "endrate", "spotrate",
                    "balancesheetrate", "endofperiodrate", "periodendrate"],
        "average": ["average", "averagerate", "avg", "avgrate", "averageperiodrate"],
        "historical": ["historical", "historicalrate", "hist", "histrate"],
    },
    "periods": {
        "period": ["period", "postingperiod", "month", "yearmonth", "accountingperiod", "periodname"],
        "status": ["status", "state", "closed", "isclosed", "periodstatus"],
    },
}
REQUIRED_REF = {"accounts": ["account", "type"], "entities": ["entity", "currency"],
                "fx": ["currency", "period", "closing"], "periods": ["period", "status"]}
FILE_EXT = (".xlsx", ".xlsm", ".csv", ".tsv", ".txt")
MONTHS = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}


def nh(s):
    return re.sub(r"[^a-z0-9]", "", str(s if s is not None else "").lower())


# ------------------------------------------------------------------ value parsing
def norm_period(v):
    """Return 'YYYY-MM' or None."""
    if v is None or v == "":
        return None
    if isinstance(v, (dt.datetime, dt.date)):
        return "%04d-%02d" % (v.year, v.month)
    s = str(v).strip()
    m = re.match(r"^(\d{4})[-/.](\d{1,2})(?:[-/.]\d{1,2})?(?:[ T].*)?$", s)
    if m and 1 <= int(m.group(2)) <= 12:
        return "%s-%02d" % (m.group(1), int(m.group(2)))
    m = re.match(r"^(\d{4})(\d{2})$", s)
    if m and 1 <= int(m.group(2)) <= 12:
        return "%s-%s" % (m.group(1), m.group(2))
    m = re.match(r"^(\d{1,2})[-/.](\d{4})$", s)
    if m and 1 <= int(m.group(1)) <= 12:
        return "%s-%02d" % (m.group(2), int(m.group(1)))
    m = re.match(r"^([A-Za-z]{3})[a-z]*[\s\-_/.,']*(\d{4}|\d{2})$", s)
    if m and m.group(1).lower() in MONTHS:
        y = m.group(2)
        y = y if len(y) == 4 else "20" + y
        return "%s-%02d" % (y, MONTHS[m.group(1).lower()])
    m = re.match(r"^(\d{4})[-\s]*[A-Za-z]{3}", s)
    if m and s[5:8].lower() in MONTHS:
        return "%s-%02d" % (m.group(1), MONTHS[s[5:8].lower()])
    return None


def parse_num(v, dec="."):
    if v is None:
        return 0.0
    if isinstance(v, bool):
        raise ValueError("bool")
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if s in ("", "-", "null", "None", "NULL"):
        return 0.0
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg, s = True, s[1:-1]
    if s.endswith("-"):
        neg, s = True, s[:-1]
    s = re.sub(r"[^\d,.\-eE+]", "", s)
    if dec == ",":
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", "")
    x = float(s)
    return -x if neg else x


def norm_id(v):
    if v is None:
        return ""
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    s = str(v).strip()
    if re.match(r"^\d+\.0+$", s):
        s = s.split(".")[0]
    return s


def norm_status(v):
    s = nh(v)
    if s in ("closed", "close", "locked", "lock", "yes", "true", "1", "c", "y", "final", "done"):
        return "closed"
    if s in ("open", "opened", "no", "false", "0", "o", "n", "pending", "inprogress", ""):
        return "open"
    return None


ACCT_CLASSES = ("asset", "liability", "equity", "retained_earnings", "income", "expense")


NS_TYPES = {"acctrec": "asset", "acctpay": "liability", "credcard": "liability", "deferexpense": "asset",
            "deferrevenue": "liability", "unbilledrec": "asset", "longtermliab": "liability",
            "othcurrliab": "liability", "othcurrasset": "asset", "othasset": "asset", "fixedasset": "asset",
            "othincome": "income", "othexpense": "expense", "cogs": "expense", "bank": "asset",
            "equity": "equity", "income": "income", "expense": "expense"}


def classify_account(type_text, name=""):
    t = nh(type_text)
    n = nh(name)
    if t in ACCT_CLASSES:
        return t
    if t in NS_TYPES:
        return NS_TYPES[t]
    if "retainedearning" in t or "retainedearning" in n:
        return "retained_earnings"
    if any(k in t for k in ("liab", "payable", "accrued", "creditcard", "debt", "loan", "deferredrevenue")):
        return "liability"
    if any(k in t for k in ("equity", "capital", "sharecap", "stock", "reserve", "ownersdraw")):
        return "equity"
    if any(k in t for k in ("asset", "bank", "cash", "receivable", "inventory", "prepaid", "fixed",
                            "deposit", "intangible", "deferredexpense")):
        return "asset"
    if any(k in t for k in ("income", "revenue", "sales", "gain")):
        return "income"
    if any(k in t for k in ("expense", "cost", "cogs", "loss", "depreciation", "amortization", "tax")):
        return "expense"
    return None


# ------------------------------------------------------------------ file reading
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_sheets(path):
    """-> list of (sheet_name, rows) with rows = list of lists of raw cell values."""
    ext = os.path.splitext(path)[1].lower()
    if ext in (".xlsx", ".xlsm"):
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        out = []
        for ws in wb.worksheets:
            if getattr(ws, "sheet_state", "visible") != "visible":
                continue
            out.append((ws.title, [list(r) for r in ws.iter_rows(values_only=True)]))
        wb.close()
        return out
    raw = open(path, "rb").read()
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    sample = text[:4096]
    delim = ","
    try:
        delim = csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
    except Exception:
        if sample.count(";") > sample.count(","):
            delim = ";"
    rows = [r for r in csv.reader(io.StringIO(text), delimiter=delim)]
    return [(os.path.basename(path), rows)]


def find_header(rows, dataset, explicit, scan=30):
    """Find the header row. Returns (row_index, colmap) or (None, diag).
    `explicit` maps canonical field -> the user's exact header text (from config / the setup form);
    anything not given falls back to the built-in aliases. A ledger laid out with one column per
    month (Jan-26, Feb-26, ...) is detected too: colmap["wide"] = {column index: 'YYYY-MM'}."""
    aliases = ALIASES[dataset]
    diag = []
    for i, row in enumerate(rows[:scan]):
        cells = [nh(c) for c in row]
        if not any(cells):
            continue
        colmap = {}
        for field, names in aliases.items():
            cand = ([nh(explicit[field])] if explicit.get(field) else []) + list(names)
            for nm in cand:
                if nm and nm in cells:
                    colmap[field] = cells.index(nm)
                    break
        if len(diag) < 1:
            diag = [str(c) for c in row if c not in (None, "")][:12]
        if dataset == "ledger":
            ok = ("entity" in colmap and "account" in colmap and ("period" in colmap or "date" in colmap)
                  and ("amount" in colmap or ("debit" in colmap and "credit" in colmap)))
            if not ok and "entity" in colmap and "account" in colmap and not explicit.get("amount"):
                wide = {}
                for ci, raw in enumerate(row):
                    if ci in (colmap["entity"], colmap["account"]):
                        continue
                    p = norm_period(raw)
                    if p:
                        wide[ci] = p
                if len(wide) >= 1:
                    colmap["wide"] = wide
                    ok = True
        else:
            ok = all(f in colmap for f in REQUIRED_REF[dataset])
        if ok:
            return i, colmap
    return None, diag


def merged_columns(ds_cfg, relname):
    """Global column overrides, then any per-file override whose pattern matches this file."""
    out = dict(ds_cfg.get("columns") or {})
    for pat, m in (ds_cfg.get("file_columns") or {}).items():
        if fnmatch.fnmatch(os.path.basename(relname.split(":", 1)[-1]).lower(), pat.lower()):
            out.update(m)
    return out


def suggest_mapping(dataset, headers):
    """For each canonical field: the header we matched, or ranked guesses from the user's own headers."""
    import difflib
    out = {}
    nhs = [(h, nh(h)) for h in headers if str(h or "").strip()]
    taken = set()
    for field, names in ALIASES[dataset].items():
        hit = next((h for nm in names for h, n in nhs if n == nm), None)
        if hit is not None:
            out[field] = {"match": hit, "guesses": []}
            taken.add(hit)
    for field, names in ALIASES[dataset].items():
        if field in out:
            continue
        scored = []
        for h, n in nhs:
            if h in taken:
                continue
            best = max([difflib.SequenceMatcher(None, n, nm).ratio() for nm in names] +
                       [0.95 if nm in n and len(nm) > 2 else 0 for nm in names] +
                       [0.7 if n in nm and len(n) > 2 else 0 for nm in names])
            if best >= 0.5:
                scored.append((best, h))
        scored.sort(key=lambda x: -x[0])
        out[field] = {"match": None, "guesses": [h for _, h in scored[:3]]}
    return out


def inspect_file(dataset, path, relname, cfg):
    """Describe a file as the user will see it: headers, sample rows, proposed mapping, what is unmatched."""
    explicit = merged_columns(cfg["sources"][dataset], relname)
    info = {"file": relname, "sheets": []}
    try:
        sheets = read_sheets(path)
    except Exception as e:
        return {"file": relname, "error": "%s: %s" % (type(e).__name__, e)}
    for sname, rows in sheets:
        hi, colmap = find_header(rows, dataset, explicit)
        if hi is None:
            # best guess header row = first row with >=3 non-empty text cells
            gi = next((i for i, r in enumerate(rows[:30]) if sum(1 for x in r if str(x or "").strip()) >= 3), 0)
            headers = [str(x) for x in (rows[gi] if rows else []) if str(x or "").strip()]
            sm = suggest_mapping(dataset, headers)
            req = (["entity", "account", "period", "amount"] if dataset == "ledger" else REQUIRED_REF[dataset])
            unmatched = [f for f in req if not sm.get(f, {}).get("match")
                         and not (f == "period" and sm.get("date", {}).get("match"))
                         and not (f == "amount" and sm.get("debit", {}).get("match") and sm.get("credit", {}).get("match"))]
            info["sheets"].append({"sheet": sname, "usable": False, "header_row": gi + 1, "headers": headers,
                                   "sample": [[str(x) for x in r[:len(headers) + 2]] for r in rows[gi + 1:gi + 4]],
                                   "unmatched_required": unmatched,
                                   "suggestions": {f: sm[f]["guesses"] for f in unmatched if f in sm}})
        else:
            hdr = rows[hi]
            m = {f: str(hdr[i]) for f, i in colmap.items() if f != "wide"}
            if "wide" in colmap:
                m["wide_periods"] = sorted(colmap["wide"].values())
            info["sheets"].append({"sheet": sname, "usable": True, "header_row": hi + 1, "mapping": m,
                                   "rows": max(0, len(rows) - hi - 1),
                                   "sample": [[str(x) for x in r[:12]] for r in rows[hi + 1:hi + 3]]})
    return info


def expected_text(dataset):
    if dataset == "ledger":
        return "entity, account, period (or date), and amount (or debit + credit)"
    return ", ".join(REQUIRED_REF[dataset])


def cell(row, idx):
    return row[idx] if idx is not None and idx < len(row) else None


def is_total_row(*vals):
    for v in vals:
        s = str(v or "").strip().lower()
        if s.startswith("total") or s.startswith("grand total") or s == "sum":
            return True
    return False


# ------------------------------------------------------------------ ledger parse
def parse_ledger_file(path, relname, cfg, errs, warns):
    ds = cfg["sources"]["ledger"]
    explicit = merged_columns(ds, relname)
    dec, sign = cfg["decimal_separator"], cfg["sign_convention"]
    groups = defaultdict(lambda: defaultdict(float))
    used, diag, bad = 0, None, 0
    try:
        sheets = read_sheets(path)
    except Exception as e:
        errs.append({"code": "unreadable_file", "file": relname,
                     "detail": "%s: %s (password-protected, corrupt or unsupported .xls?)" % (type(e).__name__, e)})
        return None
    wanted_sheet = ds.get("sheet")
    for sname, rows in sheets:
        if wanted_sheet and nh(sname) != nh(wanted_sheet):
            continue
        hi, colmap = find_header(rows, "ledger", explicit)
        if hi is None:
            diag = diag or (sname, colmap)
            continue
        used += 1
        c = colmap
        missing_key, first_bad = 0, None
        for ri, row in enumerate(rows[hi + 1:], start=hi + 2):
            if not any(x not in (None, "") for x in row):
                continue
            ent, acc = cell(row, c["entity"]), cell(row, c["account"])
            if is_total_row(ent, acc):
                continue
            ent, acc = norm_id(ent), norm_id(acc)
            if "wide" in c:   # one column per month
                if not ent or not acc:
                    missing_key += 1
                    first_bad = first_bad or ri
                    continue
                for ci, wper in c["wide"].items():
                    v = cell(row, ci)
                    if v in (None, ""):
                        continue
                    try:
                        a = parse_num(v, dec)
                    except Exception:
                        bad += 1
                        if bad <= 3:
                            errs.append({"code": "bad_number", "file": relname,
                                         "detail": "sheet %s row %d col %d: %r" % (sname, ri, ci + 1, v)})
                        continue
                    groups[(wper, ent)][acc] += (-a if sign == "credit_positive" else a)
                continue
            per = norm_period(cell(row, c["period"])) if "period" in c else None
            if per is None and "date" in c:
                dv = cell(row, c["date"])
                per = norm_period(dv)
            if not ent or not acc or not per:
                missing_key += 1
                first_bad = first_bad or ri
                continue
            try:
                if "amount" in c:
                    amt = parse_num(cell(row, c["amount"]), dec)
                    if sign == "credit_positive":
                        amt = -amt
                else:
                    amt = parse_num(cell(row, c["debit"]), dec) - parse_num(cell(row, c["credit"]), dec)
            except Exception:
                bad += 1
                if bad <= 3:
                    errs.append({"code": "bad_number", "file": relname, "detail": "sheet %s row %d: %r" % (
                        sname, ri, cell(row, c.get("amount", c.get("debit"))))})
                continue
            groups[(per, ent)][acc] += amt
        if missing_key:
            errs.append({"code": "missing_key_fields", "file": relname,
                         "detail": "sheet %s: %d rows lack entity/account/period (first at row %s)" % (
                             sname, missing_key, first_bad)})
    if used == 0:
        errs.append({"code": "columns_not_found", "file": relname,
                     "detail": "no sheet has the needed columns (%s). First header row seen: %s" % (
                         expected_text("ledger"), (diag[1] if diag else "none"))})
        return None
    out = {}
    for k, accts in groups.items():
        accts = {a: round(v, 6) for a, v in accts.items() if abs(v) > 1e-9}
        out[k] = accts
    return out


def group_fp(accts):
    return [len(accts), round(sum(accts.values()), 4), round(sum(abs(v) for v in accts.values()), 4)]


# ------------------------------------------------------------------ reference parse
def parse_reference(dataset, path, relname, cfg, errs, warns):
    ds = cfg["sources"][dataset]
    explicit = merged_columns(ds, relname)
    dec = cfg["decimal_separator"]
    status_map = {nh(k): v for k, v in (ds.get("status_map") or {}).items()}
    try:
        sheets = read_sheets(path)
    except Exception as e:
        errs.append({"code": "unreadable_file", "file": relname, "detail": "%s: %s" % (type(e).__name__, e)})
        return None
    pref = ds.get("sheet")
    cands = []
    for sname, rows in sheets:
        if pref and nh(sname) != nh(pref):
            continue
        hi, colmap = find_header(rows, dataset, explicit)
        if hi is not None:
            kw = {"accounts": "account", "entities": "entit", "fx": "fx", "periods": "period"}[dataset]
            cands.append((0 if (kw in nh(sname) or (dataset == "fx" and "rate" in nh(sname))) else 1,
                          sname, rows, hi, colmap))
    if not cands:
        first = next(((s, find_header(r, dataset, explicit)[1]) for s, r in sheets), None)
        errs.append({"code": "columns_not_found", "file": relname,
                     "detail": "%s needs columns: %s. Seen: %s" % (dataset, expected_text(dataset),
                                                                 first[1] if first else "empty file")})
        return None
    cands.sort(key=lambda x: x[0])
    _, sname, rows, hi, c = cands[0]
    out = []
    for ri, row in enumerate(rows[hi + 1:], start=hi + 2):
        if not any(x not in (None, "") for x in row):
            continue
        if dataset == "accounts":
            a = norm_id(cell(row, c["account"]))
            if not a or is_total_row(a):
                continue
            out.append({"account": a, "name": str(cell(row, c.get("name")) or "").strip(),
                        "type_raw": str(cell(row, c["type"]) or "").strip(),
                        "rate_class": nh(cell(row, c.get("rate_class"))) if "rate_class" in c else ""})
        elif dataset == "entities":
            e = norm_id(cell(row, c["entity"]))
            if not e or is_total_row(e):
                continue
            el = nh(cell(row, c.get("is_elim"))) if "is_elim" in c else ""
            out.append({"entity": e, "name": str(cell(row, c.get("name")) or "").strip() if "name" in c else "",
                        "currency": str(cell(row, c["currency"]) or "").strip().upper(),
                        "parent": norm_id(cell(row, c.get("parent"))) if "parent" in c else "",
                        "is_elim": el in ("t", "true", "yes", "y", "1")})
        elif dataset == "fx":
            cur = str(cell(row, c["currency"]) or "").strip().upper()
            per = norm_period(cell(row, c["period"]))
            if not cur or is_total_row(cur):
                continue
            if not per:
                errs.append({"code": "bad_period", "file": relname, "detail": "fx row %d period %r" % (
                    ri, cell(row, c["period"]))})
                continue
            try:
                cl = parse_num(cell(row, c["closing"]), dec)
                av = parse_num(cell(row, c["average"]), dec) if "average" in c else None
                hs = parse_num(cell(row, c["historical"]), dec) if "historical" in c else None
            except Exception:
                errs.append({"code": "bad_number", "file": relname, "detail": "fx row %d" % ri})
                continue
            out.append({"currency": cur, "period": per, "closing": cl,
                        "average": av or None, "historical": hs or None})
        elif dataset == "periods":
            per = norm_period(cell(row, c["period"]))
            sv = cell(row, c["status"])
            st = status_map.get(nh(sv)) or norm_status(sv)
            if not per:
                continue
            if st is None:
                errs.append({"code": "bad_status", "file": relname, "detail": "period %s status %r" % (
                    per, cell(row, c["status"]))})
                continue
            out.append({"period": per, "status": st})
    return out


# ------------------------------------------------------------------ discovery + ingest
def resolve_path(p, store, pathmap):
    if os.path.exists(p):
        return p
    best = None
    for host, sb in pathmap.items():
        h = host.rstrip("/")
        if p == h or p.startswith(h + "/"):
            if best is None or len(h) > len(best[0]):
                best = (h, sb)
    if best:
        return os.path.join(best[1], p[len(best[0]):].lstrip("/"))
    if not os.path.isabs(p):
        return os.path.join(store, p)
    return p


def list_files(dataset, cfg, store, pathmap, errs):
    """-> list of (file_key, abs_path). file_key is stable across sessions."""
    ds = cfg["sources"][dataset]
    pats = ds.get("pattern") or []
    if isinstance(pats, str):
        pats = [x.strip() for x in pats.split(",") if x.strip()]
    # connector mode: "paths" holds SharePoint/OneDrive locations that the agent downloads into .state/inbox/<dataset>/.
    # They are not local folders, so only the inbox is read (no path_not_found).
    local_paths = [] if ds.get("mode") == "connector" else ds.get("paths", [])
    roots = [(p, resolve_path(p, store, pathmap)) for p in local_paths]
    roots.append(("inbox", os.path.join(store, ".state", "inbox", dataset)))
    found = []
    for label, root in roots:
        if label == "inbox" and not os.path.isdir(root):
            continue
        if not os.path.exists(root):
            errs.append({"code": "path_not_found", "file": label,
                         "detail": "%s path not found: %s. Is the folder mounted / synced / spelled correctly?" % (
                             dataset, label)})
            continue
        if os.path.isfile(root):
            found.append(("%s:%s" % (label, os.path.basename(root)), root))
            continue
        for dp, dn, fn in os.walk(root):
            dn[:] = [d for d in dn if not d.startswith(".")]
            for f in sorted(fn):
                if f.startswith("~$") or f.startswith(".") or not f.lower().endswith(FILE_EXT):
                    continue
                if pats and not any(fnmatch.fnmatch(f.lower(), pt.lower()) for pt in pats):
                    continue
                full = os.path.join(dp, f)
                found.append(("%s:%s" % (label, os.path.relpath(full, root)), full))
    return found


def ingest(store, cfg, pathmap, now_ts, baseline=None):
    """Refresh .state caches from the files. Returns summary dict (errors/warnings inside)."""
    state = os.path.join(store, ".state")
    os.makedirs(state, exist_ok=True)
    errs, warns = [], []
    # ---- ledger
    lpath = os.path.join(state, "ledger_cache.json")
    cache = json.load(open(lpath)) if os.path.exists(lpath) else {"files": {}, "groups": {}}
    files = list_files("ledger", cfg, store, pathmap, errs)
    seen, changed, unsettled, drift = set(), [], [], []
    for key, full in files:
        seen.add(key)
        st = os.stat(full)
        sha = sha256_file(full)
        rec = cache["files"].get(key)
        if rec and rec["sha"] == sha:
            continue
        if now_ts - st.st_mtime < cfg["settle_seconds"]:
            unsettled.append(key)
            if rec is None:   # never read before: skipping would silently leave months out
                errs.append({"code": "file_still_changing", "file": key,
                             "detail": "new file modified %ds ago and may still be uploading/syncing. "
                                       "Nothing was changed; wait a minute and run again (a scheduled run retries by itself)." % int(now_ts - st.st_mtime)})
            else:
                warns.append({"code": "file_still_changing", "file": key,
                              "detail": "modified %ds ago; skipped this run, previous version kept" % int(now_ts - st.st_mtime)})
            continue
        parsed = parse_ledger_file(full, key, cfg, errs, warns)
        if parsed is None:
            continue
        for g in (rec or {}).get("groups", []):
            cache["groups"].pop(g, None)
        glist = []
        for (per, ent), accts in parsed.items():
            gk = "%s|%s" % (per, ent)
            other = cache["groups"].get(gk)
            if other and other["file"] != key:
                errs.append({"code": "duplicate_group", "file": key,
                             "detail": "period %s entity %s also appears in %s - would be double counted" % (
                                 per, ent, other["file"])})
                continue
            cache["groups"][gk] = {"file": key, "rows": accts, "fp": group_fp(accts)}
            glist.append(gk)
            if baseline and per <= baseline["cutoff"]:
                old = (baseline.get("period_controls", {}).get(per, {}) or {}).get(ent)
                fp = group_fp(accts)
                if old and (old[0] != fp[0] or abs(old[1] - fp[1]) > 0.01 or abs(old[2] - fp[2]) > 0.01):
                    drift.append({"kind": "ledger", "period": per, "entity": ent,
                                  "detail": "closed-month data changed since baseline (count %s->%s, abs %s->%s)" % (
                                      old[0], fp[0], old[2], fp[2])})
        cache["files"][key] = {"sha": sha, "size": st.st_size, "mtime": st.st_mtime, "groups": glist}
        changed.append(key)
    for key in list(cache["files"]):
        if key not in seen:
            errs.append({"code": "missing_file", "file": key,
                         "detail": "was ingested before but is no longer found (moved, renamed, sync glitch?). "
                                   "Restore it, or run with --accept-removed after checking."})
    if errs and any(e["code"] == "missing_file" for e in errs) and cfg.get("_accept_removed"):
        for e in [e for e in errs if e["code"] == "missing_file"]:
            for g in cache["files"].pop(e["file"], {}).get("groups", []):
                cache["groups"].pop(g, None)
            errs.remove(e)
            warns.append({"code": "file_removed_accepted", "file": e["file"], "detail": "data removed from cache"})
    # ---- reference data
    ref, ref_changed = {}, []
    for ds in ("accounts", "entities", "fx", "periods"):
        if cfg["sources"].get(ds, {}).get("type") == "none":
            ref[ds] = []
            continue
        rows = []
        for key, full in list_files(ds, cfg, store, pathmap, errs):
            r = parse_reference(ds, full, key, cfg, errs, warns)
            if r:
                rows.extend(r)
        if not rows and not any(e.get("file") and ds in e.get("detail", "") for e in errs):
            errs.append({"code": "dataset_empty", "file": ds,
                         "detail": "no %s rows found in the configured paths" % ds})
        ref[ds] = rows
    ref = dedupe_reference(ref, errs, warns)
    rpath = os.path.join(state, "ref_cache.json")
    old_ref = json.load(open(rpath)) if os.path.exists(rpath) else {}
    for ds in ref:
        if json.dumps(old_ref.get(ds), sort_keys=True) != json.dumps(ref[ds], sort_keys=True):
            ref_changed.append(ds)
    if baseline:
        for r in ref.get("fx", []):
            old = (baseline.get("fx_controls", {}).get(r["period"], {}) or {}).get(r["currency"])
            if old and (abs(old[0] - r["closing"]) > 1e-9 or abs(old[1] - (r["average"] or r["closing"])) > 1e-9):
                drift.append({"kind": "fx", "period": r["period"], "entity": r["currency"],
                              "detail": "FX rate for closed period changed since baseline"})
    if not errs:
        json.dump(cache, open(lpath, "w"))
        json.dump(ref, open(rpath, "w"))
    pers = sorted({k.split("|")[0] for k in cache["groups"]})
    return {"ledger_files": len(files), "ledger_files_changed": changed, "ledger_files_unsettled": unsettled,
            "groups": len(cache["groups"]), "periods": [pers[0], pers[-1]] if pers else [],
            "reference_changed": ref_changed,
            "counts": {k: len(v) for k, v in ref.items()}, "errors": errs, "warnings": warns, "drift": drift}


def dedupe_reference(ref, errs, warns):
    out = {}
    seen = {}
    for r in ref.get("accounts", []):
        o = seen.get(r["account"])
        if o and (o["type_raw"], o["name"]) != (r["type_raw"], r["name"]):
            errs.append({"code": "conflicting_reference", "file": "accounts", "detail": "account %s defined twice differently" % r["account"]})
        seen[r["account"]] = r
    out["accounts"] = list(seen.values())
    seen = {}
    for r in ref.get("entities", []):
        o = seen.get(r["entity"])
        if o and (o["currency"], o["parent"]) != (r["currency"], r["parent"]):   # (name may differ harmlessly)
            errs.append({"code": "conflicting_reference", "file": "entities", "detail": "entity %s defined twice differently" % r["entity"]})
        seen[r["entity"]] = r
    out["entities"] = list(seen.values())
    seen = {}
    for r in ref.get("fx", []):
        k = (r["currency"], r["period"])
        o = seen.get(k)
        if o and abs(o["closing"] - r["closing"]) > 1e-12:
            errs.append({"code": "conflicting_reference", "file": "fx", "detail": "rate %s %s defined twice differently" % k})
        seen[k] = r
    out["fx"] = list(seen.values())
    seen = {}
    for r in ref.get("periods", []):
        o = seen.get(r["period"])
        if o and o["status"] != r["status"]:
            errs.append({"code": "conflicting_reference", "file": "periods", "detail": "period %s has two statuses" % r["period"]})
        seen[r["period"]] = r
    out["periods"] = list(seen.values())
    return out

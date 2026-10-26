"""G4 Sales Priority Workspace — standard-library Python web application.
Run: python app.py  |  http://127.0.0.1:8050
"""
import csv
import json
import os
import sqlite3
import threading
import secrets
from http.cookies import SimpleCookie
from datetime import datetime, timezone
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from scoring_v3 import assess, POLICY_VERSION

ROOT = Path(__file__).resolve().parent
DATA_PATH = Path(os.environ.get('G4_DATA_PATH', ROOT / 'data' / 'opportunities.csv'))
DB_PATH = Path(os.environ.get('G4_DB_PATH', ROOT / 'data' / 'workspace.sqlite3'))
PORT = int(os.environ.get('PORT', '8050'))
DB_LOCK = threading.Lock()
DEMO_MODE = os.environ.get('G4_DEMO_MODE', '1') == '1'
DEMO_SESSIONS = {}
DEMO_PERSONAS = {'head': {'role':'HEAD','label':'Head de RevOps'}, 'manager': {'role':'MANAGER','label':'Manager','manager':None}, 'seller': {'role':'SELLER','label':'Vendedor','seller':None}}



def load_opportunities(path=DATA_PATH):
    with open(path, encoding='utf-8-sig', newline='') as handle:
        rows = list(csv.DictReader(handle))
    if not rows or len({r['opportunity_id'] for r in rows}) != len(rows):
        raise ValueError('Dataset vazio ou com IDs duplicados')
    for row in rows:
        row['priority_score'] = float(row['priority_score'])
        row['sales_price'] = float(row['sales_price'])
        for field in ('stage_component', 'product_component', 'account_component'):
            row[field] = float(row[field])
        row['account_known'] = bool(row['account'].strip())
        row['next_best_action'] = action_for(row)
    return rows


def action_for(row, qualification=None):
    qualification = qualification or {}
    if not row.get('account', '').strip():
        return 'IDENTIFY_ACCOUNT'
    if row['deal_stage'] == 'Prospecting':
        return 'QUALIFY_OPPORTUNITY'
    if qualification.get('decision_maker') == 'unknown' or qualification.get('timeline') == 'unknown':
        return 'QUALIFY_OPPORTUNITY'
    return 'REVIEW_ENGAGEMENT'


@contextmanager
def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA busy_timeout=10000')
    try:
        yield db
    finally:
        db.close()


def init_db():
    with DB_LOCK, connect() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS sales_action_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT, opportunity_id TEXT NOT NULL,
            title TEXT NOT NULL, owner TEXT NOT NULL, due_date TEXT NOT NULL,
            priority TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'OPEN',
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL)''')
        db.execute('''CREATE TABLE IF NOT EXISTS sales_action_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT, opportunity_id TEXT NOT NULL,
            event_type TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL)''')
        db.execute('''CREATE TABLE IF NOT EXISTS qualifications (
            opportunity_id TEXT PRIMARY KEY, decision_maker TEXT NOT NULL,
            timeline TEXT NOT NULL, budget TEXT NOT NULL,
            notes TEXT NOT NULL, updated_at TEXT NOT NULL)''')
        db.execute('''CREATE TABLE IF NOT EXISTS account_overrides (opportunity_id TEXT PRIMARY KEY, account TEXT NOT NULL, updated_at TEXT NOT NULL)''')
        db.execute('''CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT, opportunity_id TEXT NOT NULL,
            action TEXT NOT NULL, note TEXT NOT NULL, created_at TEXT NOT NULL)''')
        db.execute('''CREATE TABLE IF NOT EXISTS opportunity_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, opportunity_id TEXT NOT NULL,
            job_type TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'OPEN',
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
            UNIQUE(opportunity_id, job_type))''')
        db.execute('''CREATE TABLE IF NOT EXISTS quality_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT, opportunity_id TEXT NOT NULL,
            event_type TEXT NOT NULL, defect_code TEXT NOT NULL,
            detail TEXT NOT NULL, created_at TEXT NOT NULL)''')
        db.execute('''CREATE TABLE IF NOT EXISTS score_audit (
            opportunity_id TEXT PRIMARY KEY, score_before REAL NOT NULL,
            score_after REAL NOT NULL, score_policy TEXT NOT NULL,
            account_before TEXT NOT NULL, account_after TEXT NOT NULL,
            calculation_note TEXT NOT NULL, verified_at TEXT NOT NULL)''')
        db.execute('''CREATE TABLE IF NOT EXISTS deal_closures (opportunity_id TEXT PRIMARY KEY, previous_stage TEXT NOT NULL, outcome TEXT NOT NULL, close_value REAL, loss_reason TEXT, evidence TEXT NOT NULL, actor TEXT NOT NULL, closed_at TEXT NOT NULL)''')
        existing_columns={r[1] for r in db.execute('PRAGMA table_info(deal_closures)')}
        for column, kind in [('product_snapshot','TEXT'),('catalog_price_snapshot','REAL')]:
            if column not in existing_columns: db.execute(f'ALTER TABLE deal_closures ADD COLUMN {column} {kind}')
        db.execute('''CREATE TABLE IF NOT EXISTS owner_overrides (opportunity_id TEXT PRIMARY KEY, sales_agent TEXT NOT NULL, updated_at TEXT NOT NULL)''')
        db.execute('''CREATE TABLE IF NOT EXISTS ownership_events (id INTEGER PRIMARY KEY AUTOINCREMENT, opportunity_id TEXT NOT NULL, previous_owner TEXT NOT NULL, new_owner TEXT NOT NULL, actor TEXT NOT NULL, created_at TEXT NOT NULL)''')
        db.execute('''CREATE TABLE IF NOT EXISTS job_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT, job_id INTEGER NOT NULL,
            event_type TEXT NOT NULL, note TEXT NOT NULL, created_at TEXT NOT NULL)''')
        db.commit()
    apply_account_overrides()
    apply_owner_overrides()
    apply_deal_closures()
    sync_jobs()
    seed_quality_events()


def apply_account_overrides():
    with DB_LOCK, connect() as db:
        overrides = {r['opportunity_id']:r['account'] for r in db.execute('SELECT opportunity_id,account FROM account_overrides')}
    for row in ROWS:
        account = overrides.get(row['opportunity_id'], row['account'])
        row['account'] = account
        row['account_known'] = bool(account.strip())
        row['next_best_action'] = action_for(row)


def apply_owner_overrides():
    with DB_LOCK, connect() as db:
        overrides={r['opportunity_id']:r['sales_agent'] for r in db.execute('SELECT opportunity_id,sales_agent FROM owner_overrides')}
    for r in ROWS:
        if r['opportunity_id'] in overrides:r['sales_agent']=overrides[r['opportunity_id']]

def reassign_owner(opportunity_id, new_owner, actor):
    if opportunity_id not in INDEX:raise KeyError('Deal não encontrado')
    row=INDEX[opportunity_id]
    eligible=sorted({r['sales_agent'] for r in ROWS if r['manager']==row['manager']})
    if new_owner not in eligible:raise ValueError('Novo vendedor deve pertencer à mesma equipe')
    old=row['sales_agent']
    if old==new_owner:raise ValueError('Novo responsável igual ao atual')
    now=utc_now()
    with DB_LOCK, connect() as db:
        db.execute('INSERT OR REPLACE INTO owner_overrides VALUES (?,?,?)',(opportunity_id,new_owner,now))
        db.execute('INSERT INTO ownership_events (opportunity_id,previous_owner,new_owner,actor,created_at) VALUES (?,?,?,?,?)',(opportunity_id,old,new_owner,actor,now))
        db.commit()
    row['sales_agent']=new_owner
    return {'saved':True,'opportunity_id':opportunity_id,'previous_owner':old,'new_owner':new_owner}

def utc_now():
    return datetime.now(timezone.utc).isoformat()


def job_condition(row, qualification, job_type):
    q = qualification or {}
    if job_type == 'IDENTIFY_ACCOUNT':
        return not row['account_known']
    if job_type == 'RESOLVE_QUALIFICATION_BLOCKER':
        return any(q.get(k) == 'no' for k in ('decision_maker','timeline','budget'))
    if job_type == 'QUALIFY_OPPORTUNITY':
        return any(q.get(k, 'unknown') == 'unknown' for k in ('decision_maker','timeline','budget'))
    return False


def apply_deal_closures():
    with DB_LOCK, connect() as db:
        closures = [dict(r) for r in db.execute('SELECT * FROM deal_closures')]
    for c in closures:
        if c['opportunity_id'] in INDEX:
            INDEX[c['opportunity_id']]['deal_stage'] = c['outcome']
            INDEX[c['opportunity_id']]['close_value'] = c['close_value']
            INDEX[c['opportunity_id']]['next_best_action'] = 'DEAL_CLOSED'


def close_deal(opportunity_id, payload, actor):
    if opportunity_id not in INDEX: raise KeyError('Oportunidade não encontrada')
    row = INDEX[opportunity_id]
    outcome = str(payload.get('outcome', '')).strip()
    evidence = str(payload.get('evidence', '')).strip()
    if outcome not in ('Won', 'Lost'): raise ValueError('Resultado deve ser Won ou Lost')
    if not evidence or len(evidence) > 1000: raise ValueError('Informe evidência de 1 a 1000 caracteres')
    if not quality_gate(row)['eligible']: raise ValueError('Quality Gate bloqueante: identifique a conta')
    with DB_LOCK, connect() as db:
        qualification = db.execute('SELECT * FROM qualifications WHERE opportunity_id=?',(opportunity_id,)).fetchone()
        if not qualification or any(qualification[k] != 'yes' for k in ('decision_maker','timeline','budget')):
            raise ValueError('Qualificação incompleta: decisor, prazo e orçamento devem estar confirmados')
        pending = db.execute("SELECT COUNT(*) FROM opportunity_jobs WHERE opportunity_id=? AND status NOT IN ('VERIFIED')",(opportunity_id,)).fetchone()[0]
        if pending: raise ValueError('Existem pendências de Rework não verificadas')
        if row['deal_stage'] not in ('Prospecting','Engaging'): raise ValueError('Deal já encerrado')
        value = None
        reason = None
        if outcome == 'Won':
            try: value = float(payload.get('close_value', ''))
            except (ValueError, TypeError): raise ValueError('Informe valor fechado válido')
            import math
            if not math.isfinite(value) or value <= 0: raise ValueError('Valor fechado deve ser positivo')
        else:
            reason = str(payload.get('loss_reason', '')).strip()
            if reason not in ('PRICE','COMPETITOR','TIMING','NO_FIT','OTHER'):
                raise ValueError('Informe motivo válido de perda')
        now = utc_now()
        try:
            db.execute('BEGIN IMMEDIATE')
            db.execute('INSERT INTO deal_closures (opportunity_id,previous_stage,outcome,close_value,loss_reason,evidence,actor,closed_at,product_snapshot,catalog_price_snapshot) VALUES (?,?,?,?,?,?,?,?,?,?)', (opportunity_id,row['deal_stage'],outcome,value,reason,evidence,actor,now,row['product_normalized'],row['sales_price']))
            db.execute('INSERT INTO sales_action_events (opportunity_id,event_type,detail,created_at) VALUES (?,?,?,?)', (opportunity_id,'DEAL_CLOSED',json.dumps({'from':row['deal_stage'],'to':outcome,'close_value':value,'loss_reason':reason,'evidence':evidence,'actor':actor,'product':row['product_normalized'],'catalog_price':row['sales_price'],'price_basis':'catalog_reference_not_transaction_value'},ensure_ascii=False),now))
            db.execute("UPDATE opportunity_jobs SET status='VERIFIED',updated_at=? WHERE opportunity_id=? AND status!='VERIFIED'",(now,opportunity_id))
            db.commit()
        except sqlite3.IntegrityError:
            db.rollback();raise ValueError('Deal já encerrado')
        row['deal_stage'] = outcome
        row['close_value'] = value
        row['next_best_action'] = 'DEAL_CLOSED'
    return {'saved':True,'opportunity_id':opportunity_id,'deal_stage':outcome,'closed_at':now}


def sync_jobs(opportunity_id=None):
    """Idempotent rule evaluation; only confirmed evidence verifies a job."""
    types = ('IDENTIFY_ACCOUNT','RESOLVE_QUALIFICATION_BLOCKER','QUALIFY_OPPORTUNITY')
    with DB_LOCK, connect() as db:
        qs = {r['opportunity_id']:dict(r) for r in db.execute('SELECT * FROM qualifications')}
        selected = [INDEX[opportunity_id]] if opportunity_id else ROWS
        now = utc_now()
        for row in selected:
            if row['deal_stage'] in ('Won','Lost'): continue
            key = row['opportunity_id']
            for kind in types:
                active = job_condition(row, qs.get(key), kind)
                existing = db.execute('SELECT id,status FROM opportunity_jobs WHERE opportunity_id=? AND job_type=?',(key,kind)).fetchone()
                if active and existing is None:
                    cur=db.execute('INSERT INTO opportunity_jobs (opportunity_id,job_type,status,created_at,updated_at) VALUES (?,?,?,?,?)',(key,kind,'OPEN',now,now))
                    db.execute('INSERT INTO job_events (job_id,event_type,note,created_at) VALUES (?,?,?,?)',(cur.lastrowid,'CREATED','Regra de negócio ativada',now))
                elif existing and existing['status'] in ('OPEN','REOPENED','RESOLVED','IN_PROGRESS') and not active and kind == 'IDENTIFY_ACCOUNT':
                    db.execute('UPDATE opportunity_jobs SET status=?,updated_at=? WHERE id=?',('VERIFIED',now,existing['id']))
                    db.execute('INSERT INTO job_events (job_id,event_type,note,created_at) VALUES (?,?,?,?)',(existing['id'],'VERIFIED','Quality Gate: conta identificada e verificada pela regra local',now))
                elif existing and existing['status'] in ('OPEN','REOPENED','RESOLVED','IN_PROGRESS') and not active and kind in ('QUALIFY_OPPORTUNITY','RESOLVE_QUALIFICATION_BLOCKER'):
                    db.execute('UPDATE opportunity_jobs SET status=?,updated_at=? WHERE id=?',('VERIFIED',now,existing['id']))
                    db.execute('INSERT INTO job_events (job_id,event_type,note,created_at) VALUES (?,?,?,?)',(existing['id'],'VERIFIED','Qualificação comercial confirmada; pendência verificada automaticamente pela regra de negócio',now))
                elif existing and existing['status'] == 'VERIFIED' and active:
                    db.execute('UPDATE opportunity_jobs SET status=?,updated_at=? WHERE id=?',('REOPENED',now,existing['id']))
                    db.execute('INSERT INTO job_events (job_id,event_type,note,created_at) VALUES (?,?,?,?)',(existing['id'],'REOPENED','Condição voltou a ocorrer',now))
        db.commit()


QUALITY_POLICY_VERSION = 'QG-1.0'


def quality_gate(row):
    """Eligibility is independent from commercial score and qualification jobs."""
    defects = []
    if not row['account_known']:
        defects.append('MISSING_ACCOUNT')
    return {'eligible':not defects, 'status':'PASS' if not defects else 'BLOCKED',
            'blocking_defects':defects, 'policy_version':QUALITY_POLICY_VERSION}


def seed_quality_events():
    """Capture first observation once; never manufacture a historical intake timestamp."""
    with DB_LOCK, connect() as db:
        now=utc_now()
        existing={r[0] for r in db.execute("SELECT opportunity_id FROM quality_events WHERE event_type='FIRST_OBSERVED'")}
        for row in ROWS:
            key=row['opportunity_id']
            if key not in existing:
                defects=quality_gate(row)['blocking_defects']
                db.execute('INSERT INTO quality_events (opportunity_id,event_type,defect_code,detail,created_at) VALUES (?,?,?,?,?)',
                           (key,'FIRST_OBSERVED',','.join(defects),'Snapshot observed at application initialization; not CRM intake time',now))
        db.commit()


def quality_metrics():
    """Observed-snapshot metrics, not historical source-system quality rates."""
    with DB_LOCK, connect() as db:
        first=[dict(r) for r in db.execute("SELECT opportunity_id,defect_code FROM quality_events WHERE event_type='FIRST_OBSERVED'")]
        events=[dict(r) for r in db.execute('SELECT * FROM quality_events ORDER BY id DESC LIMIT 100')]
    blocked=sum(bool(r['defect_code']) for r in first)
    return {'policy_version':QUALITY_POLICY_VERSION,'observed':len(first),
            'first_observation_pass':len(first)-blocked,'first_observation_blocked':blocked,
            'first_observation_pass_rate':round((len(first)-blocked)/len(first)*100,2) if first else None,
            'currently_eligible':sum(quality_gate(r)['eligible'] for r in ROWS),
            'currently_blocked':sum(not quality_gate(r)['eligible'] for r in ROWS),
            'events':events,
            'note':'Métricas baseadas na primeira observação pelo aplicativo, não no instante de entrada no CRM. FPY de origem e lead time real exigem eventos de ingestão.'}


def evidence_hint(kind, row):
    if kind == 'IDENTIFY_ACCOUNT':
        return 'Informe a conta na aba Qualificação e salve; o sistema verificará automaticamente.' if not row['account_known'] else 'Conta identificada; verificação automática disponível.'
    if kind == 'QUALIFY_OPPORTUNITY':
        return 'Preencha Decisor, Prazo e Orçamento na aba Qualificação e salve.'
    if kind == 'RESOLVE_QUALIFICATION_BLOCKER':
        return 'Revise os campos marcados como Não na aba Qualificação e salve as evidências.'
    return 'Registre a evidência exigida pela regra.'


def jobs_for(opportunity_id=None, seller=None, include_history=False, limit=100):
    with DB_LOCK, connect() as db:
        sql='SELECT * FROM opportunity_jobs WHERE 1=1'
        params=[]
        if opportunity_id:
            sql+=' AND opportunity_id=?';params.append(opportunity_id)
        if not include_history:
            sql+=" AND status != 'VERIFIED'"
            sql+=" AND opportunity_id NOT IN (SELECT opportunity_id FROM deal_closures)"
        jobs=[dict(r) for r in db.execute(sql,params)]
        ev={}
        if include_history:
            for e in db.execute('SELECT * FROM job_events ORDER BY id DESC'):
                ev.setdefault(e['job_id'],[]).append(dict(e))
    priority={'RESOLVE_QUALIFICATION_BLOCKER':0,'IDENTIFY_ACCOUNT':1,'QUALIFY_OPPORTUNITY':2}
    statusrank={'REOPENED':0,'OPEN':1,'IN_PROGRESS':2,'RESOLVED':3,'VERIFIED':4}
    result=[]
    for j in jobs:
        row=INDEX[j['opportunity_id']]
        if seller and row['sales_agent']!=seller:continue
        j.update({'sales_agent':row['sales_agent'],'account':row['account'],'deal_score':row['priority_score'],
                  'priority':'P1' if j['job_type']=='RESOLVE_QUALIFICATION_BLOCKER' else 'P2' if j['job_type']=='IDENTIFY_ACCOUNT' else 'P3',
                  'events':ev.get(j['id'],[]),
                  'evidence_hint':evidence_hint(j['job_type'],row)})
        result.append(j)
    result.sort(key=lambda j:(statusrank.get(j['status'],9),priority[j['job_type']],-j['deal_score'],j['id']))
    return result[:max(1,min(int(limit),500))]


def transition_job(job_id, action, note=''):
    if action not in ('START','RESOLVE') or len(note)>1000:
        raise ValueError('Transição inválida')
    with DB_LOCK, connect() as db:
        job=db.execute('SELECT * FROM opportunity_jobs WHERE id=?',(job_id,)).fetchone()
        if job is None:raise KeyError('Job não encontrado')
        current=job['status']
        if action=='START' and current not in ('OPEN','REOPENED'):
            raise ValueError('START permitido somente em OPEN/REOPENED')
        if action=='RESOLVE' and current!='IN_PROGRESS':
            raise ValueError('RESOLVE permitido somente em IN_PROGRESS')
        new='IN_PROGRESS' if action=='START' else 'RESOLVED'
        now=utc_now()
        db.execute('UPDATE opportunity_jobs SET status=?,updated_at=? WHERE id=?',(new,now,job_id))
        db.execute('INSERT INTO job_events (job_id,event_type,note,created_at) VALUES (?,?,?,?)',(job_id,new,note,now))
        db.commit()
    if action=='RESOLVE':sync_jobs(job['opportunity_id'])
    return {'saved':True,'job_id':job_id,'status':next(j['status'] for j in jobs_for(job['opportunity_id'],include_history=True) if j['id']==job_id)}


def get_state():
    with DB_LOCK, connect() as db:
        q = {r['opportunity_id']: dict(r) for r in db.execute('SELECT * FROM qualifications')}
        activities = [dict(r) for r in db.execute('SELECT * FROM activities ORDER BY id DESC')]
    return q, activities


def enriched(row, q, activity_count):
    r = dict(row)
    r['qualification'] = q.get(row['opportunity_id'])
    r['activity_count'] = activity_count.get(row['opportunity_id'], 0)
    r.update(assess(row, r['qualification']))
    r['quality_gate'] = quality_gate(row)
    r['data_confidence'] = 'ACCOUNT_KNOWN' if row['account_known'] else 'ACCOUNT_MISSING'
    return r


ROWS = load_opportunities()
INDEX = {r['opportunity_id']: r for r in ROWS}


def dashboard(filters=None):
    filters = filters or {}
    q, acts = get_state()
    counts = {}
    for a in acts:
        counts[a['opportunity_id']] = counts.get(a['opportunity_id'], 0) + 1
    blocked_rows = [r for r in ROWS if not quality_gate(r)['eligible']]
    rows = [enriched(r, q, counts) for r in ROWS if quality_gate(r)['eligible'] and r['deal_stage'] not in ('Won','Lost')]
    for key in ('sales_agent', 'manager', 'regional_office', 'deal_stage', 'priority_band'):
        if filters.get(key):
            rows = [r for r in rows if r[key] == filters[key]]
    if filters.get('search'):
        term = filters['search'].casefold().strip()
        rows = [r for r in rows if term in ' '.join(str(r.get(k,'')) for k in ('opportunity_id','account','product_normalized','sales_agent')).casefold()]
    rows.sort(key=lambda r: (-r['priority_score'], r['opportunity_id']))
    total = len(rows)
    page_size = max(1, min(int(filters.get('page_size', 6)), 100))
    page = max(1, min(int(filters.get('page', 1)), max(1, (total+page_size-1)//page_size)))
    page_rows = rows[(page-1)*page_size:page*page_size]
    return {
        'total':total, 'page':page, 'pages':max(1,(total+page_size-1)//page_size),
        'kpis':{'open':total,'engaging':sum(r['deal_stage']=='Engaging' for r in rows),
                'prospecting':sum(r['deal_stage']=='Prospecting' for r in rows),
                'account_missing':len(blocked_rows),
                'actions_recorded':sum(r['activity_count'] for r in rows),
                'qualified':sum(r['qualification'] is not None for r in rows)},
        'rows':page_rows, 'quality_gate':{'version':QUALITY_POLICY_VERSION,'blocked_total':len(blocked_rows)},
        'options':{k:sorted({r[k] for r in ROWS}) for k in ('sales_agent','manager','regional_office')},
        'policy':{'version':POLICY_VERSION,'weights':{'stage':40,'product':35,'account':25},
                  'disclaimer':'Decision-support heuristic, NOT a close probability. V2 baseline weights are provisional. Catalog price is NOT deal value. Historical CRM dates are not used as current urgency.'}
    }



def historical_conversion(filters=None):
    """Historical CRM closing cohort, distinct from the live eligible pipeline."""
    from collections import Counter, defaultdict
    path = ROOT / 'data' / 'sales_pipeline_history.csv'
    if not path.exists():
        return {'available': False, 'reason': 'Arquivo histórico sales_pipeline_history.csv ausente.'}
    with path.open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    filters=filters or {}
    seller_meta={r['sales_agent']:(r['manager'],r['regional_office']) for r in ROWS}
    closed=[]
    for r in rows:
        if r.get('deal_stage') not in ('Won','Lost'):continue
        manager,region=seller_meta.get(r.get('sales_agent'),('',''))
        if filters.get('sales_agent') and r.get('sales_agent')!=filters['sales_agent']:continue
        if filters.get('manager') and manager!=filters['manager']:continue
        if filters.get('regional_office') and region!=filters['regional_office']:continue
        if filters.get('account') and r.get('account')!=filters['account']:continue
        if filters.get('deal_stage') and r.get('deal_stage')!=filters['deal_stage']:continue
        closed.append(r)
    won = sum(r['deal_stage'] == 'Won' for r in closed)
    lost = len(closed) - won
    months = defaultdict(lambda: {'won': 0, 'lost': 0})
    revenue = 0.0
    for r in closed:
        date = (r.get('close_date') or '').strip()
        if len(date) >= 7 and date[:7].replace('-', '').isdigit():
            months[date[:7]][r['deal_stage'].lower()] += 1
        if r['deal_stage'] == 'Won':
            try: revenue += float(r.get('close_value') or 0)
            except ValueError: pass
    series = [{'month': month, 'won': values['won'], 'lost': values['lost'],
               'win_rate': round(100 * values['won'] / (values['won'] + values['lost']), 2)}
              for month, values in sorted(months.items()) if values['won'] + values['lost']]
    return {'available': True, 'won': won, 'lost': lost,
            'win_rate': round(100 * won / (won + lost), 2) if won + lost else None,
            'won_close_value': round(revenue, 2), 'series': series,
            'period': [series[0]['month'], series[-1]['month']] if series else [],
            'scope': 'CRM histórico: negócios encerrados no escopo de filtros aplicáveis (seller, manager, região, conta, estágio)',
            'currency': 'Unidade monetária não especificada no CSV original'}



def reconciled_historical_rows():
    """Overlay persisted closures by opportunity_id, never append duplicate historical rows."""
    with (ROOT/'data'/'sales_pipeline_history.csv').open(encoding='utf-8-sig',newline='') as f:
        history=list(csv.DictReader(f))
    with DB_LOCK, connect() as db:
        closures={r['opportunity_id']:dict(r) for r in db.execute('SELECT * FROM deal_closures')}
    output=[]
    seen=set()
    for original in history:
        r=dict(original)
        oid=r.get('opportunity_id')
        if oid in seen:
            continue
        seen.add(oid)
        c=closures.get(oid)
        if c:
            r['deal_stage']=c['outcome']
            r['close_value']=str(c['close_value'] or '') if c['outcome']=='Won' else ''
            r['close_date']=c['closed_at'][:10]
            r['closure_source']='operational_sqlite'
        else:
            r['closure_source']='historical_csv'
        output.append(r)
    return output


def executive_intelligence(region='', manager='', sector='All Sectors'):
    """Historical closed/open opportunities; sectors inferred by account from CRM snapshot.

    Unknown account/sector stays explicitly unclassified. Sales price is catalog
    exposure, never recognized revenue. No predictive probability is inferred.
    """
    from collections import Counter, defaultdict
    with (ROOT/'data'/'historical_dimensions.csv').open(encoding='utf-8',newline='') as f:
        dimensions={r['opportunity_id']:r for r in csv.DictReader(f)}
    sector_names=sorted({r['sector'] for r in dimensions.values() if r.get('sector') and r['sector']!='28'})
    history=reconciled_historical_rows()
    scoped=[]
    for r in history:
        dim=dimensions.get(r.get('opportunity_id'),{})
        if region and dim.get('regional_office')!=region:continue
        if manager and dim.get('manager')!=manager:continue
        row=dict(r)
        row['sector']=dim.get('sector') if dim.get('sector') not in ('',None,'28') else 'Não informado'
        row['manager']=dim.get('manager','')
        row['region']=dim.get('regional_office','')
        row['catalog_price']=dim.get('sales_price','')
        scoped.append(row)
    sector_counts=Counter(r['sector'] for r in scoped)
    sectors=[{'name':name,'deals':sector_counts.get(name,0)} for name in sector_names]
    sectors.append({'name':'Não informado','deals':sector_counts.get('Não informado',0)})
    sectors.append({'name':'All Sectors','deals':len(scoped)})
    selected=scoped if sector=='All Sectors' else [r for r in scoped if r['sector']==sector]
    stage=Counter(r['deal_stage'] for r in selected)
    won=[r for r in selected if r['deal_stage']=='Won']
    lost=[r for r in selected if r['deal_stage']=='Lost']
    closed=len(won)+len(lost)
    def value(r,k):
        try:return float(r.get(k) or 0)
        except (ValueError,TypeError):return 0
    won_value=sum(value(r,'close_value') for r in won)
    lost_catalog_exposure=sum(value(r,'catalog_price') for r in lost)
    cycles=[]
    for r in won:
        try:
            if r.get('engage_date') and r.get('close_date'):
                cycles.append((datetime.fromisoformat(r['close_date'])-datetime.fromisoformat(r['engage_date'])).days)
        except ValueError:pass
    months=defaultdict(lambda:Counter())
    for r in selected:
        if r['deal_stage'] in ('Won','Lost') and r.get('engage_date'):
            months[r['engage_date'][:7]][r['deal_stage']]+=1
    cohorts=[{'month':k,'won':v['Won'],'lost':v['Lost'],'win_rate':round(100*v['Won']/(v['Won']+v['Lost']),2) if v['Won']+v['Lost'] else None} for k,v in sorted(months.items())]
    account_counts=Counter(r['account'] or 'Não identificado' for r in selected)
    return {'scope':{'region':region or 'Todas','manager':manager or 'Todos','sector':sector},
      'sectors':sectors,'stages':{k:stage[k] for k in ('Won','Lost','Prospecting','Engaging')},
      'account360':{'deals':len(selected),'accounts':len({r['account'] for r in selected if r.get('account')}),
       'won':len(won),'lost':len(lost),'open':stage['Prospecting']+stage['Engaging'],
       'won_revenue':round(won_value,2),'avg_won_deal':round(won_value/len(won),2) if won else None,
       'avg_won_cycle_days':round(sum(cycles)/len(cycles),2) if cycles else None,
       'top_accounts':[{'account':k,'deals':v} for k,v in account_counts.most_common(8)]},
      'derived':{'win_rate':round(100*len(won)/closed,2) if closed else None,
       'loss_rate':round(100*len(lost)/closed,2) if closed else None,
       'closed':closed,'open':stage['Prospecting']+stage['Engaging'],
       'catalog_lost_exposure':round(lost_catalog_exposure,2),'catalog_exposure_reason':'Soma dos preços de catálogo dos negócios Lost; não é receita recuperável.',
       'cohorts':cohorts}}



def management_intelligence(region='', manager='', sector='All Sectors'):
    """Tactical historical performance and live workload; demo region comparison is read-only."""
    from collections import Counter
    with (ROOT/'data'/'historical_dimensions.csv').open(encoding='utf-8',newline='') as f:
        dims={r['opportunity_id']:r for r in csv.DictReader(f)}
    historical=reconciled_historical_rows()
    sector_names=sorted({r['sector'] for r in dims.values() if r.get('sector') and r['sector']!='28'})
    def normalized_sector(dim):
        value=dim.get('sector')
        return value if value not in ('',None,'28') else 'Não informado'
    def summarize(items):
        stages=Counter(r['deal_stage'] for r in items)
        closed=stages['Won']+stages['Lost']
        return {'deals':len(items),'won':stages['Won'],'lost':stages['Lost'],
                'prospecting':stages['Prospecting'],'engaging':stages['Engaging'],
                'win_rate':round(100*stages['Won']/closed,1) if closed else None}
    enriched=[]
    for r in historical:
        d=dims.get(r.get('opportunity_id'),{})
        enriched.append({**r,'region':d.get('regional_office',''),
                         'manager':d.get('manager',''), 'sector':normalized_sector(d), 'sales_agent':r.get('sales_agent','')})
    regions=[]
    for name in ('Central','East','West'):
        subset=[r for r in enriched if r['region']==name]
        regions.append({'name':name,**summarize(subset)})
    regional=[r for r in enriched if not region or r['region']==region]
    managers=[]
    for name in sorted({r['manager'] for r in regional if r['manager']}):
        subset=[r for r in regional if r['manager']==name]
        managers.append({'name':name,**summarize(subset)})
    team_scope=[r for r in regional if not manager or r['manager']==manager]
    sectors=[{'name':name,'deals':sum(r['sector']==name for r in team_scope)} for name in sector_names]
    sectors.append({'name':'Não informado','deals':sum(r['sector']=='Não informado' for r in team_scope)})
    sectors.append({'name':'All Sectors','deals':len(team_scope)})
    if sector not in {item['name'] for item in sectors}:
        raise ValueError('Setor inválido')
    team=team_scope if sector=='All Sectors' else [r for r in team_scope if r['sector']==sector]
    sellers=[]
    for name in sorted({r['sales_agent'] for r in team if r['sales_agent']}):
        subset=[r for r in team if r['sales_agent']==name]
        scoped_ids={r['opportunity_id'] for r in subset}
        live=[r for r in ROWS if r.get('opportunity_id') in scoped_ids and r['deal_stage'] not in ('Won','Lost')]
        sellers.append({'name':name,**summarize(subset),
                        'active_pipeline':len(live),
                        'high_priority':sum(r.get('priority_band')=='HIGH' for r in live)})
    sellers.sort(key=lambda x:(x['win_rate'] is None,x['win_rate'] if x['win_rate'] is not None else 101,-x['deals']))
    return {'scope':{'region':region or 'Todas','manager':manager or 'Selecione um manager','sector':sector},
            'regions':regions,'managers':managers,'sectors':sectors,'team':summarize(team),
            'sellers':sellers,'live_team_pipeline':sum(x['active_pipeline'] for x in sellers),
            'note':'CRM histórico reconciliado por opportunity_id com fechamentos operacionais persistidos; sem duplicação. Win Rate descritivo; diferenças não comprovam causalidade.'}


def revops_analytics(filters=None):
    """Separate current eligible cohorts, observed quality events and historical closed deals."""
    from collections import Counter
    filters = filters or {}
    qualified = [r for r in ROWS if quality_gate(r)['eligible']]
    for key in ('sales_agent','manager','regional_office','deal_stage','priority_band'):
        if filters.get(key):
            qualified = [r for r in qualified if r.get(key) == filters[key]]
    q, acts = get_state()
    eligible_ids = {r['opportunity_id'] for r in qualified}
    activity_count = sum(a['opportunity_id'] in eligible_ids for a in acts)
    observed = quality_metrics()
    # Current-state metrics are not historical observations. Do not turn engagement
    # cohorts or event volume into fictitious historical pipeline balances.
    from collections import Counter
    with DB_LOCK, connect() as db:
        events = [dict(row) for row in db.execute(
            "SELECT opportunity_id,event_type,defect_code,created_at FROM quality_events ORDER BY created_at,id")]
    # A genuine dated observation exists only when a snapshot was recorded. The
    # imported CRM does not contain dated stage transitions or pipeline snapshots.
    series = {key: [] for key in ('opportunities','engaging','prospecting','missing_account')}
    series_status = {
        'opportunities': 'Sem snapshots históricos de estoque de oportunidades. Total atual calculado diretamente dos Deals elegíveis.',
        'engaging': 'Sem histórico de entrada/saída do estágio Engaging. Total atual calculado diretamente dos Deals elegíveis.',
        'prospecting': 'Sem histórico de entrada/saída do estágio Prospecting. Total atual calculado diretamente dos Deals elegíveis.',
        'missing_account': 'Sem snapshots históricos do backlog de Missing Account. Eventos de correção não equivalem a saldo de defeitos.'}
    # Keep event observations in the API for audit only; they are NOT KPI trends.
    event_months = Counter(e['created_at'][:7] for e in events if len(e.get('created_at') or '') >= 7)
    return {
      'scope': 'eligible_active_opportunities',
      'metrics': {'opportunities': len(qualified),
                  'engaging': sum(r['deal_stage'] == 'Engaging' for r in qualified),
                  'prospecting': sum(r['deal_stage'] == 'Prospecting' for r in qualified),
                  'missing_account': observed['currently_blocked'],
                  'qualified': sum(r['opportunity_id'] in q for r in qualified),
                  'activities': activity_count},
      'quality': {'observed': observed['observed'],
                  'first_observation_pass': observed['first_observation_pass'],
                  'first_observation_blocked': observed['first_observation_blocked'],
                  'first_observation_pass_rate': observed['first_observation_pass_rate'],
                  'currently_blocked': observed['currently_blocked'],
                  'source': 'Primeira observação pelo app, NÃO First Pass Yield na entrada do CRM'},
      'series': {**series, 'quality_events': [{'month': month, 'value': v} for month, v in sorted(event_months.items())]},
      'series_status': series_status,
      'conversion': historical_conversion(filters),
      'availability': {},
      'notes': ['Os quatro KPIs são saldos atuais. O CRM não fornece snapshots históricos nem transições datadas suficientes para construir tendências de estoque.',
                'Quality events são registrados pelo aplicativo, não são datas de entrada no CRM.',
                'Conversão histórica de Won/Lost não é o desempenho atual; segue os filtros de vendedor, gerente e região quando aplicáveis.']}


def hierarchy(persona=None):
    """Read-only commercial hierarchy. Counts refer exclusively to active opportunities."""
    from collections import Counter
    scoped_rows = ROWS
    if persona and persona['role'] == 'MANAGER' and persona.get('manager'):
        scoped_rows = [r for r in ROWS if r['manager'] == persona['manager']]
    elif persona and persona['role'] == 'SELLER' and persona.get('seller'):
        scoped_rows = [r for r in ROWS if r['sales_agent'] == persona['seller']]
    regions = []
    for region in sorted({r['regional_office'] for r in scoped_rows}):
        region_rows = [r for r in scoped_rows if r['regional_office'] == region]
        managers = []
        for manager in sorted({r['manager'] for r in region_rows}):
            manager_rows = [r for r in region_rows if r['manager'] == manager]
            sellers = []
            for seller in sorted({r['sales_agent'] for r in manager_rows}):
                sr = [r for r in manager_rows if r['sales_agent'] == seller]
                sellers.append({'name': seller, 'total':len(sr), 'engaging':sum(r['deal_stage']=='Engaging' for r in sr), 'prospecting':sum(r['deal_stage']=='Prospecting' for r in sr)})
            managers.append({'name':manager,'total':len(manager_rows),'sellers':sellers})
        sectors = Counter((r.get('sector') or 'Não informado') for r in region_rows)
        regions.append({'name':region,'total':len(region_rows),
                        'engaging':sum(r['deal_stage']=='Engaging' for r in region_rows),
                        'prospecting':sum(r['deal_stage']=='Prospecting' for r in region_rows),
                        'sectors':[{'name':k,'total':v} for k,v in sorted(sectors.items(),key=lambda kv:(-kv[1],kv[0]))],
                        'managers':managers})
    return {'regions':regions,'scope':'active_opportunities', 'note':'Won/Lost por região não disponível no snapshot de oportunidades abertas.'}


def assert_pipeline_eligible(opportunity_id):
    if opportunity_id not in INDEX:
        raise KeyError('Oportunidade não encontrada')
    if not quality_gate(INDEX[opportunity_id])['eligible']:
        raise ValueError('Quality Gate bloqueado: regularize a conta no Rework.')


def sales_action_state(opportunity_id):
    assert_pipeline_eligible(opportunity_id)
    with DB_LOCK, connect() as db:
        plans=[dict(r) for r in db.execute('SELECT * FROM sales_action_plans WHERE opportunity_id=? ORDER BY id DESC',(opportunity_id,))]
        events=[dict(r) for r in db.execute('SELECT * FROM sales_action_events WHERE opportunity_id=? ORDER BY id DESC LIMIT 100',(opportunity_id,))]
        activities=[dict(r) for r in db.execute('SELECT * FROM activities WHERE opportunity_id=? ORDER BY id DESC LIMIT 100',(opportunity_id,))]
        qualification=db.execute('SELECT * FROM qualifications WHERE opportunity_id=?',(opportunity_id,)).fetchone()
    return {'opportunity_id':opportunity_id,'product':INDEX[opportunity_id]['product_normalized'],'catalog_price':INDEX[opportunity_id]['sales_price'],'quantity':None,'currency':None,'price_basis':'catalog_reference_not_transaction_value','plans':plans,'events':events,'activities':activities,'qualification':dict(qualification) if qualification else None}


def record_sales_event(opportunity_id, event_type, detail):
    with DB_LOCK, connect() as db:
        db.execute('INSERT INTO sales_action_events (opportunity_id,event_type,detail,created_at) VALUES (?,?,?,?)',
                   (opportunity_id,event_type,detail,utc_now()))
        db.commit()


def save_action_plan(opportunity_id, payload):
    assert_pipeline_eligible(opportunity_id)
    from datetime import date
    title=str(payload.get('title','')).strip()
    owner=str(payload.get('owner','')).strip()
    due=str(payload.get('due_date','')).strip()
    priority=str(payload.get('priority','MEDIUM'))
    if not 1<=len(title)<=180 or not 1<=len(owner)<=120 or priority not in {'HIGH','MEDIUM','LOW'}:
        raise ValueError('Título, responsável ou prioridade inválidos')
    try: parsed=date.fromisoformat(due)
    except ValueError: raise ValueError('Data de vencimento inválida (AAAA-MM-DD)')
    if parsed<date.today(): raise ValueError('O prazo não pode estar no passado')
    with DB_LOCK, connect() as db:
        cur=db.execute('INSERT INTO sales_action_plans (opportunity_id,title,owner,due_date,priority,status,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)',
                       (opportunity_id,title,owner,due,priority,'OPEN',utc_now(),utc_now()))
        plan_id=cur.lastrowid
        db.execute('INSERT INTO sales_action_events (opportunity_id,event_type,detail,created_at) VALUES (?,?,?,?)',
                   (opportunity_id,'PLAN_CREATED',f'#{plan_id} {title} · {owner} · {due} · {priority}',utc_now()))
        db.commit()
    return {'saved':True,'id':plan_id}


def update_action_plan(opportunity_id, payload):
    assert_pipeline_eligible(opportunity_id)
    try: plan_id=int(payload.get('id',0))
    except (TypeError,ValueError): raise ValueError('ID de plano inválido')
    status=str(payload.get('status',''))
    if status not in {'OPEN','IN_PROGRESS','DONE','CANCELLED'}: raise ValueError('Status inválido')
    with DB_LOCK, connect() as db:
        row=db.execute('SELECT * FROM sales_action_plans WHERE id=? AND opportunity_id=?',(plan_id,opportunity_id)).fetchone()
        if not row: raise KeyError('Plano não encontrado neste Deal')
        if row['status'] in {'DONE','CANCELLED'} and row['status']!=status: raise ValueError('Plano finalizado não pode ser reaberto')
        db.execute('UPDATE sales_action_plans SET status=?,updated_at=? WHERE id=? AND opportunity_id=?',(status,utc_now(),plan_id,opportunity_id))
        db.execute('INSERT INTO sales_action_events (opportunity_id,event_type,detail,created_at) VALUES (?,?,?,?)',
                   (opportunity_id,'PLAN_STATUS',f'#{plan_id} {row["status"]} → {status}',utc_now()))
        db.commit()
    return {'saved':True}


def save_qualification(opportunity_id, payload):
    if opportunity_id not in INDEX:
        raise KeyError('Oportunidade não encontrada')
    assert_pipeline_eligible(opportunity_id)
    allowed = {'unknown','yes','no'}
    decision_maker = str(payload.get('decision_maker','unknown'))
    budget = str(payload.get('budget','unknown'))
    timeline = str(payload.get('timeline','unknown'))
    notes = str(payload.get('notes','')).strip()
    if any(v not in allowed for v in (decision_maker,budget,timeline)) or len(notes)>1000:
        raise ValueError('Dados de qualificação inválidos')
    with DB_LOCK, connect() as db:
        db.execute('''INSERT INTO qualifications VALUES (?,?,?,?,?,?)
          ON CONFLICT(opportunity_id) DO UPDATE SET decision_maker=excluded.decision_maker,
          timeline=excluded.timeline, budget=excluded.budget, notes=excluded.notes, updated_at=excluded.updated_at''',
          (opportunity_id,decision_maker,timeline,budget,notes,datetime.now(timezone.utc).isoformat()))
        db.commit()
    sync_jobs(opportunity_id)
    record_sales_event(opportunity_id,'QUALIFICATION_SAVED','Qualificação comercial atualizada')
    return {'saved':True}


def save_account(opportunity_id, payload):
    if opportunity_id not in INDEX:
        raise KeyError('Oportunidade não encontrada')
    account = str(payload.get('account', '')).strip()
    if not account or len(account) > 120 or any(ord(c) < 32 for c in account):
        raise ValueError('Informe uma conta válida (1 a 120 caracteres).')
    original = INDEX[opportunity_id]['account']
    score_before = round(float(INDEX[opportunity_id]['priority_score']), 1)
    if original.strip() and original != account:
        raise ValueError('Esta conta já está identificada. Alterações cadastrais requerem revisão específica.')
    with DB_LOCK, connect() as db:
        db.execute("""INSERT INTO account_overrides (opportunity_id,account,updated_at) VALUES (?,?,?)
          ON CONFLICT(opportunity_id) DO UPDATE SET account=excluded.account,updated_at=excluded.updated_at""",
          (opportunity_id,account,utc_now()))
        db.execute('INSERT INTO quality_events (opportunity_id,event_type,defect_code,detail,created_at) VALUES (?,?,?,?,?)',
                   (opportunity_id,'ACCOUNT_CORRECTED','MISSING_ACCOUNT',account,utc_now()))
        db.commit()
    INDEX[opportunity_id]['account'] = account
    INDEX[opportunity_id]['account_known'] = True
    INDEX[opportunity_id]['next_best_action'] = action_for(INDEX[opportunity_id])
    sync_jobs(opportunity_id)
    with DB_LOCK, connect() as db:
        db.execute('''INSERT INTO score_audit
          (opportunity_id,score_before,score_after,score_policy,account_before,account_after,calculation_note,verified_at)
          VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(opportunity_id) DO UPDATE SET
          score_after=excluded.score_after,account_after=excluded.account_after,
          calculation_note=excluded.calculation_note,verified_at=excluded.verified_at''',
          (opportunity_id,score_before,round(float(INDEX[opportunity_id]['priority_score']),1),
           POLICY_VERSION,original,account,
           'Score V3 permanece no baseline CSV; cadastro mestre de porte não integrado; componente Account Scale neutro preservado.',utc_now()))
        db.execute('INSERT INTO quality_events (opportunity_id,event_type,defect_code,detail,created_at) VALUES (?,?,?,?,?)',
                   (opportunity_id,'GATE_PASSED','MISSING_ACCOUNT','Local rule passed; no external account registry validation',utc_now()))
        db.commit()
    return {'saved':True,'account':account,'verified_by_rule':True,'quality_gate':quality_gate(INDEX[opportunity_id])}


def score_trace(opportunity_id):
    with DB_LOCK, connect() as db:
        row=db.execute('SELECT * FROM score_audit WHERE opportunity_id=?',(opportunity_id,)).fetchone()
    return dict(row) if row else None

def save_activity(opportunity_id, payload):
    assert_pipeline_eligible(opportunity_id)
    if opportunity_id in INDEX and INDEX[opportunity_id]['deal_stage'] in ('Won','Lost'):raise ValueError('Deal encerrado')
    if opportunity_id not in INDEX:
        raise KeyError('Oportunidade não encontrada')
    action = str(payload.get('action','')).strip()
    note = str(payload.get('note','')).strip()
    if action not in {'CONTACT','QUALIFY','REVIEW','FOLLOW_UP','OTHER'} or len(note)>1000:
        raise ValueError('Atividade inválida')
    with DB_LOCK, connect() as db:
        db.execute('INSERT INTO activities (opportunity_id,action,note,created_at) VALUES (?,?,?,?)',
                   (opportunity_id,action,note,datetime.now(timezone.utc).isoformat()))
        db.commit()
    record_sales_event(opportunity_id,'ACTIVITY_RECORDED',f'{action}: {note[:200]}')
    return {'saved':True}


class Handler(BaseHTTPRequestHandler):
    def persona(self):
        if not DEMO_MODE:return None
        jar=SimpleCookie()
        try:jar.load(self.headers.get('Cookie',''))
        except Exception:return None
        token=jar.get('g4_demo')
        return DEMO_SESSIONS.get(token.value) if token else None

    def authorized(self, path, method, persona):
        if not DEMO_MODE:return True
        if path in ('/api/health','/api/demo/session') and method=='GET':return True
        if path in ('/api/demo/login','/api/demo/identity') and method=='POST':return True
        if persona is None:return False
        if persona['role']=='HEAD':return True
        if method=='POST' and path.endswith('/reassign'):return persona['role']=='MANAGER'
        if persona['role']!='HEAD' and path=='/api/quality/metrics':return False
        return True

    def scoped_args(self, args, persona):
        if not DEMO_MODE or not persona:return args
        result=dict(args)
        if persona['role']=='MANAGER':result['manager']=persona.get('manager') or '__UNSELECTED_MANAGER__'
        elif persona['role']=='SELLER':result['sales_agent']=persona.get('seller') or '__UNSELECTED_SELLER__'
        return result

    def deal_allowed(self, deal_id, persona):
        if not DEMO_MODE:return True
        if persona is None or deal_id not in INDEX:return False
        r=INDEX[deal_id]
        if persona['role']=='HEAD':return True
        if persona['role']=='MANAGER':return bool(persona.get('manager')) and r['manager']==persona['manager']
        return bool(persona.get('seller')) and r['sales_agent']==persona['seller']

    def respond(self, status, content, mime='application/json; charset=utf-8'):
        data = json.dumps(content,ensure_ascii=False).encode('utf-8') if mime.startswith('application/json') else content
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length',str(len(data)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlsplit(self.path)
        try:
            persona=self.persona()
            if path.path.startswith('/api/') and not self.authorized(path.path,'GET',persona):
                return self.respond(403,{'error':'Acesso não autorizado; selecione uma persona na capa.'})
            if path.path == '/api/demo/session':
                return self.respond(200,{'demo_mode':DEMO_MODE,'persona':persona})
            if path.path == '/':
                self.respond(200,(ROOT/'static'/'index.html').read_bytes(),'text/html; charset=utf-8')
            elif path.path == '/static/app.js':
                self.respond(200,(ROOT/'static'/'app.js').read_bytes(),'text/javascript; charset=utf-8')
            elif path.path == '/static/style.css':
                self.respond(200,(ROOT/'static'/'style.css').read_bytes(),'text/css; charset=utf-8')
            elif path.path == '/static/avatar-map.json':
                self.respond(200,json.loads((ROOT/'static'/'avatar-map.json').read_text(encoding='utf-8')))
            elif path.path.startswith('/static/avatars/'):
                from urllib.parse import unquote
                filename=unquote(path.path[len('/static/avatars/'):])
                if not filename or '/' in filename or '\\' in filename or filename in ('.','..') or not filename.lower().endswith('.png'):
                    self.respond(404,{'error':'Not found'})
                else:
                    avatar_path=ROOT/'static'/'avatars'/filename
                    if avatar_path.is_file():
                        self.respond(200,avatar_path.read_bytes(),'image/png')
                    else:
                        self.respond(404,{'error':'Not found'})
            elif path.path == '/api/hierarchy':
                self.respond(200,hierarchy(persona))
            elif path.path == '/api/executive/intelligence':
                if persona and persona['role']!='HEAD':return self.respond(403,{'error':'Acesso restrito à Diretoria'})
                args={k:v[0] for k,v in parse_qs(path.query).items()}
                self.respond(200,executive_intelligence(args.get('region',''),args.get('manager',''),args.get('sector','All Sectors')))
            elif path.path == '/api/management/intelligence':
                if not persona or persona['role']!='MANAGER':return self.respond(403,{'error':'Workspace exclusivo de Manager'})
                args={k:v[0] for k,v in parse_qs(path.query).items()}
                region=args.get('region','')
                manager=args.get('manager','')
                # A demo manager may compare regions before selecting a team, but
                # detailed team data is scoped to the active demo identity.
                if manager and manager!=persona.get('manager'):
                    return self.respond(403,{'error':'Equipe fora da identidade demonstrativa ativa'})
                if manager and region and not any(r['manager']==manager and r['regional_office']==region for r in ROWS):
                    return self.respond(400,{'error':'Manager não pertence à região'})
                self.respond(200,management_intelligence(region,manager,args.get('sector','All Sectors')))
            elif path.path == '/api/revops/analytics':
                args={k:v[0] for k,v in parse_qs(path.query).items()}
                self.respond(200,revops_analytics(self.scoped_args(args,persona)))
            elif path.path == '/api/dashboard':
                args = {k:v[0] for k,v in parse_qs(path.query).items()}
                self.respond(200,dashboard(self.scoped_args(args,persona)))
            elif path.path.startswith('/api/opportunities/'):
                key=path.path.rsplit('/',1)[-1]
                if key not in INDEX: raise KeyError('Oportunidade não encontrada')
                if not self.deal_allowed(key,persona):return self.respond(403,{'error':'Deal fora do escopo autorizado'})
                q,acts=get_state()
                self.respond(200,{'opportunity':enriched(INDEX[key],q, {key:sum(a['opportunity_id']==key for a in acts)}),
                                  'activities':[a for a in acts if a['opportunity_id']==key][:30],
                                  'jobs':jobs_for(opportunity_id=key,include_history=True),
                                  'score_trace':score_trace(key)})
            elif path.path.startswith('/api/sales-action/'):
                deal_id=path.path.split('/')[-1]
                if not self.deal_allowed(deal_id,persona):return self.respond(403,{'error':'Deal fora do escopo autorizado'})
                self.respond(200,sales_action_state(deal_id))
            elif path.path == '/api/jobs':
                args={k:v[0] for k,v in parse_qs(path.query).items()}
                jobs=jobs_for(seller=persona['seller'] if persona and persona['role']=='SELLER' else args.get('sales_agent'),include_history=args.get('history')=='1',limit=args.get('limit',100))
                if persona and persona['role']=='MANAGER':jobs=[j for j in jobs if persona.get('manager') and INDEX[j['opportunity_id']]['manager']==persona['manager']]
                if persona and persona['role']=='SELLER' and not persona.get('seller'):jobs=[]
                self.respond(200,{'jobs':jobs})
            elif path.path == '/api/quality/metrics':
                self.respond(200,quality_metrics())
            elif path.path == '/api/health':
                self.respond(200,{'status':'ok','opportunities':len(ROWS)})
            else:self.respond(404,{'error':'Not found'})
        except (ValueError, TypeError) as exc:self.respond(400,{'error':str(exc)})
        except KeyError as exc:self.respond(404,{'error':str(exc)})
        except Exception as exc:
            print('Server error:',repr(exc));self.respond(500,{'error':'Erro interno'})

    def do_POST(self):
        try:
            n=int(self.headers.get('Content-Length','0'))
            if n<=0 or n>4096:raise ValueError('Payload inválido')
            body=json.loads(self.rfile.read(n))
            path=urlsplit(self.path).path
            if path=='/api/demo/login' and DEMO_MODE:
                key=body.get('persona')
                if key not in DEMO_PERSONAS:return self.respond(400,{'error':'Persona inválida'})
                token=secrets.token_urlsafe(32)
                DEMO_SESSIONS[token]=dict(DEMO_PERSONAS[key])
                data=json.dumps({'persona':DEMO_SESSIONS[token]}).encode('utf-8')
                self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)))
                self.send_header('Set-Cookie',f'g4_demo={token}; HttpOnly; SameSite=Strict; Path=/')
                self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data);return
            persona=self.persona()
            if path=='/api/demo/identity' and DEMO_MODE:
                if not persona or persona['role'] not in ('MANAGER','SELLER'):
                    return self.respond(403,{'error':'Persona sem permissão de seleção'})
                field='manager' if persona['role']=='MANAGER' else 'seller'
                candidate=str(body.get(field,'')).strip()
                valid={r[field if field=='manager' else 'sales_agent'] for r in ROWS}
                if candidate not in valid:return self.respond(400,{'error':'Identidade demonstrativa desconhecida'})
                persona[field]=candidate
                return self.respond(200,{'persona':persona})
            if not self.authorized(path,'POST',persona):return self.respond(403,{'error':'Operação não autorizada'})
            if len(path.strip('/').split('/'))==4 and path.endswith('/reassign'):
                deal_id=path.strip('/').split('/')[2]
                if not self.deal_allowed(deal_id,persona):return self.respond(403,{'error':'Deal fora do escopo autorizado'})
                if persona and persona['role']=='SELLER':return self.respond(403,{'error':'Reatribuição exige manager ou head'})
                return self.respond(200,reassign_owner(deal_id,str(body.get('sales_agent','')),persona['label'] if persona else 'local'))
            if path.startswith('/api/opportunities/'):
                deal_id=path.strip('/').split('/')[2]
                if not self.deal_allowed(deal_id,persona):return self.respond(403,{'error':'Deal fora do escopo autorizado'})
            if path.startswith('/api/jobs/') and persona:
                with DB_LOCK,connect() as db:
                    job=db.execute('SELECT opportunity_id FROM opportunity_jobs WHERE id=?',(path.split('/')[-1],)).fetchone()
                if not job or not self.deal_allowed(job['opportunity_id'],persona):return self.respond(403,{'error':'Job fora do escopo autorizado'})
            parts=path.strip('/').split('/')
            if len(parts)==3 and parts[:2]==['api','jobs']:
                return self.respond(200,transition_job(int(parts[2]),str(body.get('action','')),str(body.get('note',''))))
            if len(parts)!=4 or parts[:2]!=['api','opportunities']:
                return self.respond(404,{'error':'Not found'})
            if parts[3]!='close' and INDEX[parts[2]]['deal_stage'] in ('Won','Lost'):
                return self.respond(400,{'error':'Deal encerrado; alterações bloqueadas'})
            if parts[3]=='sales-plan':result=save_action_plan(parts[2],body)
            elif parts[3]=='sales-plan-status':result=update_action_plan(parts[2],body)
            elif parts[3]=='account':result=save_account(parts[2],body)
            elif parts[3]=='qualification':result=save_qualification(parts[2],body)
            elif parts[3]=='activities':result=save_activity(parts[2],body)
            elif parts[3]=='close':
                if not persona or persona['role']!='SELLER':return self.respond(403,{'error':'Encerramento reservado ao vendedor responsável'})
                result=close_deal(parts[2],body,persona['seller'])
            else:return self.respond(404,{'error':'Not found'})
            self.respond(200,result)
        except (ValueError,TypeError,json.JSONDecodeError) as exc:self.respond(400,{'error':str(exc)})
        except KeyError as exc:self.respond(404,{'error':str(exc)})
        except Exception as exc:
            print('Server error:',repr(exc));self.respond(500,{'error':'Erro interno'})


def main():
    init_db()
    if not DEMO_MODE:
        raise RuntimeError('Este pacote demonstra autorização apenas em Demo Mode; integração IAM de produção não implementada.')
    server=ThreadingHTTPServer(('127.0.0.1',PORT),Handler)
    print(f'G4 Sales Priority Workspace: http://127.0.0.1:{PORT} ({len(ROWS)} open opportunities)')
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()


if __name__=='__main__':main()

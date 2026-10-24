"""Transactional tools. All mutations are serialized and checked in SQLite."""
import contextlib
import hashlib
import json
import sqlite3
import time
import uuid
from pathlib import Path
from .config import database_path

class WorkflowError(ValueError): pass

def check(case, driver, recipient, used_driver=0, used_recipient=0):
    reasons = []
    if not driver['available']: reasons.append('Driver unavailable')
    if not recipient['accepting']: reasons.append('Recipient not accepting')
    if driver['capacity'] - used_driver < case['boxes']: reasons.append('Insufficient driver capacity')
    if recipient['capacity'] - used_recipient < case['boxes']: reasons.append('Insufficient recipient capacity')
    if driver['handling'] is not True or recipient['handling'] is not True: reasons.append('Missing handling evidence')
    arrival = case['pickup'] + driver['travel']
    if arrival > case['deadline']: reasons.append('Food deadline missed')
    if not recipient['opens'] <= arrival <= recipient['closes']: reasons.append('Outside receiving window')
    return dict(driver=driver['id'], recipient=recipient['id'], arrival=arrival, boxes=case['boxes'], valid=not reasons, reasons=reasons)

class Store:
    def __init__(self, path=None, clock=time.time):
        if path is None: path = database_path()
        self.path, self.clock = str(path), clock
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self.tx() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS cases(id TEXT PRIMARY KEY, version INTEGER, status TEXT, data TEXT, plan TEXT, approval TEXT);
            CREATE TABLE IF NOT EXISTS holds(id TEXT PRIMARY KEY, case_id TEXT, version INTEGER, driver TEXT, recipient TEXT, boxes INTEGER, expires REAL, status TEXT, driver_reply TEXT, recipient_reply TEXT, UNIQUE(case_id,version));
            CREATE TABLE IF NOT EXISTS audit(seq INTEGER PRIMARY KEY AUTOINCREMENT, at REAL, case_id TEXT, version INTEGER, tool TEXT, detail TEXT);
            ''')

    @contextlib.contextmanager
    def tx(self):
        db = sqlite3.connect(self.path, timeout=15, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally: db.close()

    def log(self, db, cid, version, tool, detail):
        db.execute('INSERT INTO audit(at,case_id,version,tool,detail) VALUES(?,?,?,?,?)',
                   (self.clock(), cid, version, tool, json.dumps(detail, sort_keys=True)))

    def record(self, cid, tool, detail):
        with self.tx() as db:
            c = self._get(db, cid)
            self.log(db, cid, c['version'], tool, detail)

    def ingest(self, data):
        data = json.loads(json.dumps(data))
        data['id'] = 'RR-' + uuid.uuid4().hex[:8].upper()
        with self.tx() as db:
            db.execute('INSERT INTO cases VALUES(?,1,?,?,NULL,NULL)', (data['id'], 'OPEN', json.dumps(data)))
            self.log(db, data['id'], 1, 'ingest_cancellation', data)
        return data['id']

    def _get(self, db, cid):
        row = db.execute('SELECT * FROM cases WHERE id=?', (cid,)).fetchone()
        if not row: raise WorkflowError('Unknown case')
        c = dict(row)
        for k in ('data','plan','approval'): c[k] = json.loads(c[k]) if c[k] else None
        return c

    def get(self, cid):
        with self.tx() as db:
            self._expire(db)
            return self._get(db, cid)

    def cases(self):
        with self.tx() as db: return [dict(r) for r in db.execute('SELECT id,version,status FROM cases ORDER BY rowid DESC')]

    def _expire(self, db):
        rows = db.execute("SELECT * FROM holds WHERE status='HELD' AND expires<=?", (self.clock(),)).fetchall()
        for h in rows:
            db.execute("UPDATE holds SET status='EXPIRED' WHERE id=?", (h['id'],))
            db.execute("UPDATE cases SET status='ESCALATED',approval=NULL WHERE id=? AND version=?", (h['case_id'],h['version']))
            self.log(db,h['case_id'],h['version'],'hold_expired',{'hold':h['id'],'action':'Manual review or replan required'})

    def _validate(self, db, c, did, rid):
        self._expire(db)
        ds = {d['id']:d for d in c['data']['drivers']}
        rs = {r['id']:r for r in c['data']['recipients']}
        if did not in ds or rid not in rs: raise WorkflowError('Unknown resource')
        # Resources share a sandbox namespace. All other active allocations consume capacity.
        allocations = db.execute("SELECT * FROM holds WHERE case_id<>? AND status IN ('HELD','CONFIRMED')", (c['id'],)).fetchall()
        du = sum(h['boxes'] for h in allocations if h['driver']==did)
        ru = sum(h['boxes'] for h in allocations if h['recipient']==rid)
        result = check(c['data'], ds[did], rs[rid], du, ru)
        self.log(db,c['id'],c['version'],'validate_constraints',result)
        return result

    def validate(self, cid, did, rid):
        with self.tx() as db: return self._validate(db,self._get(db,cid),did,rid)

    def propose(self, cid, expected, did, rid):
        with self.tx() as db:
            c = self._get(db,cid)
            if c['version'] != expected or c['status'] not in ('OPEN','PROPOSED','ESCALATED'): raise WorkflowError('Case changed or already reserved; reload')
            p = self._validate(db,c,did,rid)
            if not p['valid']: raise WorkflowError('; '.join(p['reasons']))
            version = expected + 1
            p['fingerprint'] = hashlib.sha256(json.dumps([cid,version,p],sort_keys=True).encode()).hexdigest()
            db.execute("UPDATE cases SET version=?,status='PROPOSED',plan=?,approval=NULL WHERE id=?",(version,json.dumps(p),cid))
            self.log(db,cid,version,'propose_plan',p)
        return p

    def approve(self, cid, expected, fingerprint, actor):
        if not actor.strip(): raise WorkflowError('Dispatcher name required')
        with self.tx() as db:
            c=self._get(db,cid)
            if c['version']!=expected or c['status']!='PROPOSED' or c['plan']['fingerprint']!=fingerprint: raise WorkflowError('Stale approval: review current plan')
            p=self._validate(db,c,c['plan']['driver'],c['plan']['recipient'])
            if not p['valid']: raise WorkflowError('Evidence changed: replan required')
            approval=dict(actor=actor.strip(),version=expected,fingerprint=fingerprint,at=self.clock())
            db.execute("UPDATE cases SET approval=?,status='APPROVED' WHERE id=?",(json.dumps(approval),cid))
            self.log(db,cid,expected,'human_approval',approval)

    def reject(self, cid, expected, actor, reason):
        if not actor.strip() or not reason.strip(): raise WorkflowError('Dispatcher and rejection reason required')
        with self.tx() as db:
            c=self._get(db,cid)
            if c['version']!=expected or c['status'] not in ('PROPOSED','APPROVED'): raise WorkflowError('Stale or already reserved plan')
            db.execute("UPDATE cases SET status='ESCALATED',approval=NULL WHERE id=?",(cid,))
            self.log(db,cid,expected,'human_rejection',{'actor':actor.strip(),'reason':reason.strip()[:500]})

    def reserve(self, cid, expected, fingerprint):
        with self.tx() as db:
            self._expire(db)
            c=self._get(db,cid)
            if c['version']!=expected or not c['plan'] or c['plan']['fingerprint']!=fingerprint: raise WorkflowError('Stale plan')
            h=db.execute('SELECT * FROM holds WHERE case_id=? AND version=?',(cid,expected)).fetchone()
            if h:
                if h['status'] in ('HELD','CONFIRMED'): return dict(h)
                raise WorkflowError('Previous hold ended; replan and approve a new version')
            if c['status']!='APPROVED' or not c['approval'] or c['approval']['fingerprint']!=fingerprint: raise WorkflowError('Human approval required')
            p=self._validate(db,c,c['plan']['driver'],c['plan']['recipient'])
            if not p['valid']: raise WorkflowError('Capacity or evidence changed: replan required')
            hid=uuid.uuid4().hex
            db.execute('INSERT INTO holds VALUES(?,?,?,?,?,?,?,?,?,?)',(hid,cid,expected,p['driver'],p['recipient'],p['boxes'],self.clock()+120,'HELD',None,None))
            db.execute("UPDATE cases SET status='AWAITING_CONFIRMATIONS' WHERE id=?",(cid,))
            self.log(db,cid,expected,'reserve_capacity',{'hold':hid,'ttl_seconds':120,'simulated_transport':True})
            return dict(db.execute('SELECT * FROM holds WHERE id=?',(hid,)).fetchone())

    def reply(self, cid, expected, party, response):
        if party not in ('driver','recipient') or response not in ('accept','decline','timeout'): raise WorkflowError('Invalid reply')
        with self.tx() as db:
            self._expire(db)
            c=self._get(db,cid)
            h=db.execute('SELECT * FROM holds WHERE case_id=? AND version=?',(cid,expected)).fetchone()
            if c['version']!=expected or not h: raise WorkflowError('Stale or missing reservation')
            if h['status']!='HELD': return h['status']
            if h[party+'_reply']:
                if h[party+'_reply']!=response: raise WorkflowError('Conflicting replay ignored')
                return h['status']
            db.execute(f'UPDATE holds SET {party}_reply=? WHERE id=?',(response,h['id']))
            self.log(db,cid,expected,'simulated_'+party+'_reply',{'response':response,'hold':h['id']})
            if response!='accept':
                db.execute("UPDATE holds SET status='RELEASED' WHERE id=?",(h['id'],))
                # Failed party is excluded from future investigation, preserving the failure evidence.
                data=c['data']
                group,key=('drivers','driver') if party=='driver' else ('recipients','recipient')
                for r in data[group]:
                    if r['id']==h[key]: r['available' if party=='driver' else 'accepting']=False
                db.execute("UPDATE cases SET status='ESCALATED',approval=NULL,data=? WHERE id=?",(json.dumps(data),cid))
                self.log(db,cid,expected,'release_and_escalate',{'reason':party+' '+response,'hold':h['id']})
                return 'RELEASED'
            h=db.execute('SELECT * FROM holds WHERE id=?',(h['id'],)).fetchone()
            if h['driver_reply']==h['recipient_reply']=='accept':
                db.execute("UPDATE holds SET status='CONFIRMED' WHERE id=?",(h['id'],))
                db.execute("UPDATE cases SET status='CONFIRMED' WHERE id=?",(cid,))
                self.log(db,cid,expected,'verify_booking',{'hold':h['id'],'both_accepted':True})
                return 'CONFIRMED'
            return 'HELD'

    def change_capacity(self,cid,rid,capacity):
        if type(capacity)!=int or capacity<0: raise WorkflowError('Capacity must be a nonnegative integer')
        with self.tx() as db:
            c=self._get(db,cid)
            if c['status']=='CONFIRMED': raise WorkflowError('Confirmed rescue requires dispatcher intervention')
            data=c['data']
            if rid not in {r['id'] for r in data['recipients']}: raise WorkflowError('Unknown recipient')
            for r in data['recipients']:
                if r['id']==rid: r['capacity']=capacity
            db.execute("UPDATE holds SET status='RELEASED' WHERE case_id=? AND status='HELD'",(cid,))
            db.execute("UPDATE cases SET version=version+1,status='OPEN',data=?,plan=NULL,approval=NULL WHERE id=?",(json.dumps(data),cid))
            self.log(db,cid,c['version']+1,'capacity_changed',{'recipient':rid,'capacity':capacity,'approval_invalidated':True})

    def escalate(self,cid,reason):
        with self.tx() as db:
            c=self._get(db,cid)
            if c['status'] in ('CONFIRMED','AWAITING_CONFIRMATIONS','APPROVED'): raise WorkflowError('Active allocation cannot be escalated by planner')
            db.execute("UPDATE cases SET status='ESCALATED',approval=NULL WHERE id=?",(cid,))
            self.log(db,cid,c['version'],'escalate',{'reason':reason})

    def audit(self,cid):
        with self.tx() as db: return [dict(r) for r in db.execute('SELECT * FROM audit WHERE case_id=? ORDER BY seq',(cid,))]

    def holds(self,cid):
        with self.tx() as db:
            self._expire(db)
            return [dict(r) for r in db.execute('SELECT * FROM holds WHERE case_id=? ORDER BY rowid',(cid,))]

    def competing_allocations(self, cid):
        """Current allocations in other cases sharing this case's resources."""
        with self.tx() as db:
            self._expire(db)
            c = self._get(db, cid)
            drivers = {d['id'] for d in c['data']['drivers']}
            recipients = {r['id'] for r in c['data']['recipients']}
            rows = db.execute("SELECT * FROM holds WHERE case_id<>? AND status IN ('HELD','CONFIRMED')", (cid,)).fetchall()
            return [dict(h) for h in rows if h['driver'] in drivers or h['recipient'] in recipients]

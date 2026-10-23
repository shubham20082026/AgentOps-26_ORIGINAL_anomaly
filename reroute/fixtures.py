"""Synthetic, reproducible evidence. Times are fixture minutes, not live ETAs."""
import copy

SCENARIOS = {
    'Happy path': 'Reject A; recover 24 boxes with Driver 2 and Recipient B at 14:22.',
    'No capacity': 'No recipient can accept the full donation.',
    'Late arrival': 'Every available driver misses the food deadline.',
    'Missing handling': 'No eligible recipient has verified handling evidence.',
    'Closed recipient': 'Receiving windows close before arrival.',
    'Driver unavailable': 'No available driver.',
    'Recipient declines': 'A valid plan fails recipient confirmation; recover or escalate.',
    'Recovery with alternate': 'Driver 3 declines; investigate again and switch to Driver 2 with fresh approval.',
}

def fixture(name='Happy path'):
    c = dict(id='RR-001', boxes=24, pickup=840, deadline=870,
             donor='Campus dining hall', cancellation='Original volunteer cancelled at 14:00. Recover all 24 packed boxes.',
             handling='sealed ambient meals', recipients=[
                 dict(id='A', name='Recipient A', capacity=8, opens=840, closes=900, handling=True, accepting=True),
                 dict(id='B', name='Recipient B', capacity=30, opens=840, closes=900, handling=True, accepting=True)],
             drivers=[dict(id='D1', name='Driver 1', capacity=30, available=False, handling=True, travel=12),
                      dict(id='D2', name='Driver 2', capacity=30, available=True, handling=True, travel=22),
                      dict(id='D3', name='Driver 3', capacity=10, available=True, handling=True, travel=8)],
             replies={'driver': 'accept', 'recipient': 'decline' if name == 'Recipient declines' else 'accept'}, scenario=name)
    if name == 'No capacity':
        for r in c['recipients']: r['capacity'] = 8
    if name == 'Late arrival':
        for d in c['drivers']: d['travel'] = 45
    if name == 'Missing handling':
        for r in c['recipients']: r['handling'] = False
    if name == 'Closed recipient':
        for r in c['recipients']: r['closes'] = 845
    if name == 'Driver unavailable':
        for d in c['drivers']: d['available'] = False
    if name == 'Recovery with alternate':
        c['drivers'][2].update(capacity=30, travel=18)
        c['replies']['driver']='decline'
    return copy.deepcopy(c)

def hhmm(n):
    return f'{n//60:02d}:{n%60:02d}'

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import pytest
from app.execution.budget import Ledger, BudgetError

def test_race():
    ledger = Ledger()
    run = ledger.create('1')
    def reserve(_):
        try:
            return ledger.reserve(run,'.6')
        except BudgetError:
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(x is not None for x in pool.map(reserve,range(2))) == 1
    assert ledger.totals(run)['liability'] == Decimal('.6')

def test_unknown_and_cancel():
    ledger = Ledger()
    run = ledger.create('1')
    reservation = ledger.reserve(run,'.8')
    ledger.settle(reservation,'.2',False)
    assert ledger.totals(run) == {'known':Decimal('.2'),'liability':Decimal('.6')}
    ledger.cancel(run)
    with pytest.raises(BudgetError):
        ledger.reserve(run,'.1')
    ledger.settle(reservation,'.3')
    assert ledger.totals(run)['liability'] == 0

def test_restart(tmp_path):
    path = tmp_path/'ledger.db'
    ledger = Ledger(path)
    run = ledger.create('1')
    ledger.reserve(run,'.9')
    ledger.close()
    ledger = Ledger(path)
    with pytest.raises(BudgetError):
        ledger.reserve(run,'.2')

@pytest.mark.parametrize('value',['NaN','Infinity','-1','0.0000000000001'])
def test_invalid(value):
    with pytest.raises(BudgetError):
        Ledger().create(value)

def test_double_settlement():
    ledger = Ledger()
    run = ledger.create('1')
    reservation = ledger.reserve(run,'.5')
    ledger.settle(reservation,'.2')
    with pytest.raises(BudgetError):
        ledger.settle(reservation,'.1')

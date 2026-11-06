"""Durable reservation ledger. One API process owns this DuckDB connection."""
from contextlib import contextmanager
from decimal import Decimal
from threading import RLock
from uuid import uuid4
import duckdb

class BudgetError(ValueError):
    pass

class Ledger:
    def __init__(self, path=':memory:'):
        self.lock = RLock()
        self.db = duckdb.connect(str(path))
        self.db.execute('CREATE TABLE IF NOT EXISTS runs(id VARCHAR PRIMARY KEY, cap DECIMAL(24,12), cancelled BOOLEAN DEFAULT false)')
        self.db.execute('CREATE TABLE IF NOT EXISTS reservations(id VARCHAR PRIMARY KEY, run_id VARCHAR, bound DECIMAL(24,12), known DECIMAL(24,12), liability DECIMAL(24,12), closed BOOLEAN)')

    @contextmanager
    def transaction(self):
        with self.lock:
            self.db.execute('BEGIN')
            try:
                yield
                self.db.execute('COMMIT')
            except Exception:
                self.db.execute('ROLLBACK')
                raise

    @staticmethod
    def money(value):
        value = Decimal(str(value))
        if not value.is_finite() or value < 0 or value.as_tuple().exponent < -12:
            raise BudgetError('Amount must be finite, nonnegative, and at most 12 decimal places')
        return value

    def create(self, cap):
        cap = self.money(cap)
        if cap <= 0:
            raise BudgetError('Cap must be positive')
        run_id = str(uuid4())
        with self.transaction():
            self.db.execute('INSERT INTO runs VALUES (?, ?, false)', [run_id, cap])
        return run_id

    def reserve(self, run_id, worst_case):
        bound = self.money(worst_case)
        if bound <= 0:
            raise BudgetError('Paid reservation must be positive')
        with self.transaction():
            row = self.db.execute('SELECT cap,cancelled FROM runs WHERE id=?',[run_id]).fetchone()
            if not row or row[1]:
                raise BudgetError('Unknown or cancelled run')
            used = self.db.execute('SELECT coalesce(sum(known+liability),0) FROM reservations WHERE run_id=?',[run_id]).fetchone()[0]
            if used+bound > row[0]:
                raise BudgetError('Budget exhausted')
            reservation = str(uuid4())
            self.db.execute('INSERT INTO reservations VALUES (?,?,?,0,?,false)',[reservation,run_id,bound,bound])
        return reservation

    def settle(self, reservation, total_known, complete_usage=True):
        known = self.money(total_known)
        with self.transaction():
            row = self.db.execute('SELECT bound,known,closed FROM reservations WHERE id=?',[reservation]).fetchone()
            if not row or row[2]:
                raise BudgetError('Unknown or closed reservation')
            if known < row[1] or known > row[0]:
                raise BudgetError('Usage outside reserved bound; manual reconciliation required')
            liability = Decimal(0) if complete_usage else row[0]-known
            self.db.execute('UPDATE reservations SET known=?,liability=?,closed=? WHERE id=?',[known,liability,complete_usage,reservation])

    def cancel(self, run_id):
        with self.transaction():
            self.db.execute('UPDATE runs SET cancelled=true WHERE id=?',[run_id])

    def totals(self, run_id):
        with self.lock:
            row = self.db.execute('SELECT coalesce(sum(known),0),coalesce(sum(liability),0) FROM reservations WHERE run_id=?',[run_id]).fetchone()
            return {'known': row[0], 'liability': row[1]}

    def close(self):
        with self.lock:
            self.db.close()

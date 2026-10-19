import test from 'node:test';
import assert from 'node:assert/strict';
import { buildMonth, shiftMonth } from '../assets/calendar.js';

test('Monday-first month keeps date alignment and blank adjacent cells', () => {
  const cells = buildMonth('2026-10', []);
  assert.equal(cells.length, 35);
  assert.deepEqual(cells.slice(0, 3), [null, null, null]);
  assert.equal(cells[3].date, '2026-10-01');
  assert.equal(cells[33].day, 31);
  assert.equal(cells[34], null);
});

test('leap years, Sunday starts and six-week months use valid dates', () => {
  assert.equal(buildMonth('2024-02', []).filter(Boolean).length, 29);
  assert.equal(buildMonth('2025-02', []).filter(Boolean).length, 28);
  const cells = buildMonth('2026-03', []);
  assert.equal(cells.length, 42);
  assert.equal(cells[6].date, '2026-03-01');
});

test('same-day editions share a day; missing dates remain distinct from empty dates', () => {
  const editions = [{ id: 'a', date: '2026-10-03' }, { id: 'b', date: '2026-10-03' }, { id: 'c', date: '2026-11-03' }];
  const cells = buildMonth('2026-10', editions, ['2026-10-02']);
  assert.deepEqual(cells.find(c => c?.day === 3).editions, editions.slice(0, 2));
  assert.equal(cells.find(c => c?.day === 2).missing, true);
  assert.equal(cells.find(c => c?.day === 1).missing, false);
});

test('month navigation crosses year boundaries without local timezone shifts', () => {
  assert.equal(shiftMonth('2026-01', -1), '2025-12');
  assert.equal(shiftMonth('2026-12', 1), '2027-01');
});

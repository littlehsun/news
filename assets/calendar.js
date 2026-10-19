// Calendar arithmetic uses UTC; edition dates themselves are Asia/Taipei dates.
export function shiftMonth(month, offset) {
  const [year, number] = month.split('-').map(Number);
  const date = new Date(Date.UTC(year, number - 1 + offset, 1));
  return `${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, '0')}`;
}

export function buildMonth(month, editions, missingDates = []) {
  const [year, number] = month.split('-').map(Number);
  const start = new Date(Date.UTC(year, number - 1, 1));
  const offset = (start.getUTCDay() + 6) % 7; // Monday first.
  const days = new Date(Date.UTC(year, number, 0)).getUTCDate();
  const count = Math.ceil((offset + days) / 7) * 7;
  const groups = new Map();
  for (const edition of editions) {
    if (!groups.has(edition.date)) groups.set(edition.date, []);
    groups.get(edition.date).push(edition);
  }
  return Array.from({ length: count }, (_, index) => {
    const day = index - offset + 1;
    if (day < 1 || day > days) return null;
    const date = `${month}-${String(day).padStart(2, '0')}`;
    return { date, day, editions: groups.get(date) || [], missing: missingDates.includes(date) };
  });
}

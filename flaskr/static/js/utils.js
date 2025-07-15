export function diffInDays(date) {
  const MS_PER_DAY = 1000 * 60 * 60 * 24;
  const utc_start_session_date = Date.UTC(
    startDateSession.getFullYear(),
    startDateSession.getMonth(),
    startDateSession.getDate(),
  );
  const utc_count_date = Date.UTC(
    date.getFullYear(),
    date.getMonth(),
    date.getDate(),
  );
  return Math.floor((utc_count_date - utc_start_session_date) / MS_PER_DAY);
}

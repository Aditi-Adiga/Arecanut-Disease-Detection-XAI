export function formatScore(value) {
  if (value > 0.999) return '>99.9%';
  if (value > 0 && value < 0.001) return '<0.1%';
  return `${(value * 100).toFixed(1)}%`;
}

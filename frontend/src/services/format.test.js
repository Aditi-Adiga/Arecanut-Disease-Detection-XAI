import { formatScore } from './format';

test('very high model outputs are not displayed as 100 percent certainty', () => {
  expect(formatScore(1)).toBe('>99.9%');
  expect(formatScore(.999999)).toBe('>99.9%');
  expect(formatScore(.995)).toBe('99.5%');
  expect(formatScore(.00001)).toBe('<0.1%');
});

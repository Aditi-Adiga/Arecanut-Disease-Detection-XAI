import { readHistory, saveHistory } from './history';

test('history retains only the latest eight results', () => {
  for (let i = 0; i < 10; i++) saveHistory({ status: 'unsure' }, `photo-${i}`);
  expect(readHistory()).toHaveLength(8);
  expect(readHistory()[0].name).toBe('photo-9');
});

test('corrupted browser storage does not crash history loading', () => {
  localStorage.setItem('arecalens-scans-v1', 'broken-json');
  expect(readHistory()).toEqual([]);
});

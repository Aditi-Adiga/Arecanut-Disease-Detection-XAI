import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { beforeEach, afterEach, vi } from 'vitest';
import App from './App';

const result = {
  status: 'suspected', class_id: 'Mahali_Koleroga', display_name: 'Mahali / Koleroga (fruit rot)',
  confidence: .96, probabilities: [{ class_id: 'Mahali_Koleroga', label: 'Mahali / Koleroga', probability: .96 }],
  explanation: { lines: ['Suspected', 'The heatmap does not prove the cause.'] },
  photo_tips: [], original_image: 'data:image/png;base64,a', heatmap_image: 'data:image/png;base64,b',
};

beforeEach(() => {
  URL.createObjectURL = vi.fn(() => 'blob:preview');
  URL.revokeObjectURL = vi.fn();
  Element.prototype.scrollIntoView = vi.fn();
});
afterEach(() => vi.unstubAllGlobals());

test('upload, analyse, see explanation and reopen saved result', async () => {
  vi.stubGlobal('fetch', vi.fn(async (path) => ({ ok: true, json: async () => path === '/api/health' ? { model_loaded: true } : path === '/api/predict' ? result : null })));
  render(<App/>);
  await screen.findByText('Local model ready');
  fireEvent.change(screen.getByLabelText('Choose plant image'), { target: { files: [new File(['image'], 'plant.png', { type: 'image/png' })] } });
  fireEvent.click(screen.getByRole('button', { name: /analyse plant health/i }));
  expect(await screen.findByText('Disease pattern suspected')).toBeInTheDocument();
  expect(screen.getByText('The heatmap does not prove the cause.')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: /scan history/i }));
  expect(screen.getByText('plant.png')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: /suspected pattern/i }));
  expect(await screen.findByText('Viewing a saved result. Choose a new photo to run another analysis.')).toBeInTheDocument();
});

test('an unreachable API offers recovery and prevents a scan', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => { throw new Error('Failed to fetch'); }));
  render(<App/>);
  await waitFor(() => expect(screen.getByText('Model unavailable')).toBeInTheDocument());
  expect(screen.getByRole('button', { name: /retry server connection/i })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /analyse plant health/i })).toBeDisabled();
});

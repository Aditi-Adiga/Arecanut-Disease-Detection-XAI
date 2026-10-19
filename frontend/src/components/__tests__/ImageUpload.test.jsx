import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import ImageUpload from '../ImageUpload';

function props() { return { file: null, preview: '', busy: false, ready: true, onFile: vi.fn(), onAnalyse: vi.fn(), onClear: vi.fn(), onError: vi.fn() }; }

test('analysis is disabled until an image is selected', () => {
  render(<ImageUpload {...props()}/>);
  expect(screen.getByRole('button', { name: /analyse plant health/i })).toBeDisabled();
});

test('invalid files show an actionable error and are not selected', () => {
  const options = props(); render(<ImageUpload {...options}/>);
  fireEvent.change(screen.getByLabelText('Choose plant image'), { target: { files: [new File(['text'], 'notes.txt', { type: 'text/plain' })] } });
  expect(options.onError).toHaveBeenCalledWith('Choose a JPEG, PNG or WebP image.');
  expect(options.onFile).not.toHaveBeenCalled();
});

test('valid image passes to the upload handler', () => {
  const options = props(); render(<ImageUpload {...options}/>);
  const file = new File(['data'], 'leaf.png', { type: 'image/png' });
  fireEvent.change(screen.getByLabelText('Choose plant image'), { target: { files: [file] } });
  expect(options.onFile).toHaveBeenCalledWith(file);
});

import { render, screen } from '@testing-library/react';
import PredictionResult from '../PredictionResult';

test('uncertain predictions do not display a healthy or disease conclusion', () => {
  render(<PredictionResult result={{ status: 'unsure', display_name: 'Healthy nut', confidence: .92, probabilities: [], explanation: { lines: ['Not sure', 'Retake the image.'] }, photo_tips: [], original_image: 'data:image/png;base64,a', heatmap_image: 'data:image/png;base64,b' }}/>);
  expect(screen.getByText('Not sure — retake the photo')).toBeInTheDocument();
  expect(screen.getByText('This photo needs another look.')).toBeInTheDocument();
  expect(screen.queryByText('No visible disease pattern detected')).not.toBeInTheDocument();
});

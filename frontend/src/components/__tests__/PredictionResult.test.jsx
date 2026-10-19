import { render, screen } from '@testing-library/react';
import PredictionResult from '../PredictionResult';

test('uncertain predictions do not display a healthy or disease conclusion', () => {
  render(<PredictionResult result={{ status: 'unsure', display_name: 'Healthy nut', confidence: .92, probabilities: [], explanation: { lines: ['Not sure', 'Retake the image.'] }, photo_tips: [], original_image: 'data:image/png;base64,a', heatmap_image: 'data:image/png;base64,b' }}/>);
  expect(screen.getByText('Not sure — retake the photo')).toBeInTheDocument();
  expect(screen.getByText('This photo needs another look.')).toBeInTheDocument();
  expect(screen.queryByText('No visible disease pattern detected')).not.toBeInTheDocument();
});

test('a healthy-nut guess below the cautious cutoff is explained without sounding diseased', () => {
  render(<PredictionResult result={{ status: 'unsure', class_id: 'Healthy_Nut', display_name: 'Healthy nut', healthy_guess_below_threshold: true, healthy_cutoff: .95, confidence: .925, probabilities: [], explanation: { lines: ['Not sure', 'The closest guess is healthy nut.'] }, photo_tips: [], original_image: 'data:image/png;base64,a', heatmap_image: 'data:image/png;base64,b' }}/>);
  expect(screen.getByText('Closest model match: Healthy nut')).toBeInTheDocument();
  expect(screen.getByText(/Top score: 92\.5%\. The app needs 95\.0% or higher to show a healthy result/)).toBeInTheDocument();
  expect(screen.getByText(/Not sure” is not a disease warning/)).toBeInTheDocument();
});

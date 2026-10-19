import { fireEvent, render, screen, within } from '@testing-library/react';
import { vi } from 'vitest';
import HelpChat, { HelpChatBoundary } from '../HelpChat';
import DiseaseInfo from '../DiseaseInfo';
import { LanguageProvider } from '../../locales/LanguageContext';

const healthyNutInfo = {
  language: 'en',
  explanation: { thresholds: { healthy_below: 0.95, unsure_below: 0.7 } },
  classes: {
    Healthy_Nut: {
      display_name: 'Healthy nut', short_name: 'Healthy nut', status: 'no_disease_found',
      summary: { text: 'The model leans toward the healthy nut class.', sources: [] },
      check_signs: [{ text: 'A dark, water-soaked patch near the top of the nut.', sources: [] }],
      possible_causes: [], what_to_do: [{ text: 'Continue routine local care.', sources: [] }],
      when_to_get_help: [], limits: { text: 'One photo cannot rule out early disease.', sources: [] },
    },
  },
  sources: {},
};

test('chat explains why a healthy-nut guess can remain not sure', () => {
  render(<HelpChat info={healthyNutInfo} guideClass="Healthy_Nut" result={{ class_id: 'Healthy_Nut', status: 'unsure', confidence: 0.925 }}/>);
  fireEvent.click(screen.getByRole('button', { name: 'Ask ArecaLens' }));
  fireEvent.click(screen.getByRole('button', { name: 'Explain my result' }));
  expect(screen.getByText(/92\.5%/)).toBeInTheDocument();
  expect(screen.getByText(/95%/)).toBeInTheDocument();
  expect(screen.getByText(/does not mean the plant is diseased/i)).toBeInTheDocument();
});

test.each([
  ['Explain my result', /There is no screening result yet/],
  ['What should I check?', /Signs to check: A dark, water-soaked patch/],
  ['How do I take a better photo?', /For a clearer photo, use daylight/],
])('quick reply "%s" answers in the panel without leaving the app', (prompt, answer) => {
  render(<><main><h1>Screening page</h1></main><HelpChat info={healthyNutInfo} guideClass="Healthy_Nut"/></>);
  fireEvent.click(screen.getByRole('button', { name: 'Ask ArecaLens' }));
  fireEvent.click(screen.getByRole('button', { name: prompt }));
  expect(screen.getByRole('heading', { name: 'Screening page' })).toBeInTheDocument();
  expect(screen.getAllByRole('button', { name: 'Close help' })).toHaveLength(2);
  expect(screen.getByText(answer)).toBeInTheDocument();
});

test.each([
  ['kn', 'ArecaLens ಸಹಾಯ', 'ಏನು ಪರಿಶೀಲಿಸಬೇಕು?', /ಎಲೆಗಳ ತುದಿ ಹಳದಿಯಾಗಿದೆಯೇ ಅಥವಾ ಕಲೆಗಳಿವೆಯೇ/],
  ['hi', 'ArecaLens से पूछें', 'क्या जाँचूँ?', /पानी से भीगे जैसे हिस्सों/],
  ['ml', 'ArecaLens സഹായം', 'എന്താണ് പരിശോധിക്കേണ്ടത്?', /ഇലയുടെ അറ്റങ്ങൾ മഞ്ഞയാകുന്നതോ പാടുകളോ ഉണ്ടോ/],
])('gives useful local-language advice without guide-loading errors (%s)', (language, launcher, prompt, answer) => {
  render(<LanguageProvider language={language}><HelpChat info={null}/></LanguageProvider>);
  fireEvent.click(screen.getByRole('button', { name: launcher }));
  const panel = screen.getByRole('region', { name: /plant-care help|ಸಹಾಯ|देखभाल सहायता|കൃഷി സഹായം/i });
  fireEvent.click(within(panel).getByRole('button', { name: prompt }));
  expect(within(panel).getByText(answer)).toBeInTheDocument();
  expect(within(panel).queryByText(/guide.*(unavailable|not loaded)|ಮಾರ್ಗದರ್ಶಿ.*ಲಭ್ಯವಿಲ್ಲ|मार्गदर्शिका.*उपलब्ध नहीं|മാർഗ്ഗദർശി.*ലഭ്യമല്ല/i)).not.toBeInTheDocument();
});

test('unknown typed questions get a clear steer instead of repeating disease signs', () => {
  render(<HelpChat info={healthyNutInfo} guideClass="Healthy_Nut"/>);
  fireEvent.click(screen.getByRole('button', { name: 'Ask ArecaLens' }));
  const panel = screen.getByRole('region', { name: 'ArecaLens plant-care help' });
  const input = within(panel).getByRole('textbox', { name: /Ask about your plant/ });
  fireEvent.change(input, { target: { value: 'Do you have market prices?' } });
  fireEvent.click(within(panel).getByRole('button', { name: 'Send' }));
  expect(within(panel).getByText(/I can help with the latest screening/)).toBeInTheDocument();
  expect(within(panel).queryByText(/A dark, water-soaked patch/)).not.toBeInTheDocument();
});

test('a malformed guide falls back to local help instead of breaking the page', () => {
  vi.spyOn(console, 'error').mockImplementation(() => {});
  const brokenInfo = { get classes() { throw new Error('incomplete guide'); } };
  render(<><main><h1>Screening page</h1></main><HelpChat info={brokenInfo} guideClass="Healthy_Nut"/></>);
  fireEvent.click(screen.getByRole('button', { name: 'Ask ArecaLens' }));
  fireEvent.click(screen.getByRole('button', { name: 'What should I check?' }));
  expect(screen.getByRole('heading', { name: 'Screening page' })).toBeInTheDocument();
  const panel = screen.getByRole('region', { name: 'ArecaLens plant-care help' });
  expect(within(panel).getByText(/Look for yellow tips or spots on leaves/)).toBeInTheDocument();
});

test.each([
  ['What should I check?', /Look for yellow tips or spots on leaves/],
  ['What should I do to care for it?', /Take a clear close-up photo/],
  ['Why is this happening?', /A photo cannot reliably identify the cause/],
  ['What does the score mean?', /A model score compares the supported classes/],
  ['How do I take a photo?', /For a clearer photo/],
  ['What does the heatmap show?', /The heatmap shows image regions/],
])('answers "%s" with the matching local help when the guide has not loaded', (question, answer) => {
  render(<HelpChat info={null}/>);
  fireEvent.click(screen.getByRole('button', { name: 'Ask ArecaLens' }));
  const panel = screen.getByRole('region', { name: 'ArecaLens plant-care help' });
  const input = within(panel).getByRole('textbox', { name: /Ask about your plant/ });
  fireEvent.change(input, { target: { value: question } });
  fireEvent.click(within(panel).getByRole('button', { name: 'Send' }));
  expect(within(panel).getByText(answer)).toBeInTheDocument();
  expect(document.querySelector('.help-chat-fallback')).not.toBeInTheDocument();
});

test.each([
  ['Explain my result', /There is no screening result yet/],
  ['What should I check?', /Look for yellow tips or spots on leaves/],
  ['How do I take a better photo?', /For a clearer photo/],
])('the chat remains useful after a rendering failure: "%s"', (prompt, reply) => {
  vi.spyOn(console, 'error').mockImplementation(() => {});
  function BrokenChild() { throw new Error('chat render failed'); }
  render(<HelpChatBoundary onClose={() => {}}><BrokenChild/></HelpChatBoundary>);
  const panel = screen.getByRole('region', { name: 'ArecaLens plant-care help' });
  expect(within(panel).getByText(/Hello! I can explain your latest screening/)).toBeInTheDocument();
  expect(within(panel).getByRole('button', { name: 'Close help' })).toBeInTheDocument();
  expect(document.querySelector('.help-chat-fallback')).not.toBeInTheDocument();
  fireEvent.click(within(panel).getByRole('button', { name: prompt }));
  expect(within(panel).getByText(reply)).toBeInTheDocument();
  expect(within(panel).queryByText(/field guide has not loaded yet/i)).not.toBeInTheDocument();
});

test('closing the chat hides only its panel and lets it reopen from the launcher', () => {
  vi.spyOn(console, 'error').mockImplementation(() => {});
  function BrokenChild() { throw new Error('chat render failed'); }
  render(<><main><h1>Screening page</h1></main><HelpChatBoundary><BrokenChild/></HelpChatBoundary></>);
  const panel = screen.getByRole('region', { name: 'ArecaLens plant-care help' });
  fireEvent.click(within(panel).getByRole('button', { name: 'Close help' }));
  expect(screen.queryByRole('region', { name: 'ArecaLens plant-care help' })).not.toBeInTheDocument();
  expect(screen.getByRole('heading', { name: 'Screening page' })).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Ask ArecaLens' }));
  expect(screen.getByRole('region', { name: 'ArecaLens plant-care help' })).toBeInTheDocument();
});

test('lets the farmer type and send a message in the recovery chat panel', () => {
  vi.spyOn(console, 'error').mockImplementation(() => {});
  function BrokenChild() { throw new Error('chat render failed'); }
  render(<HelpChatBoundary onClose={() => {}}><BrokenChild/></HelpChatBoundary>);
  const panel = screen.getByRole('region', { name: 'ArecaLens plant-care help' });
  const input = within(panel).getByRole('textbox', { name: /Ask about your plant/ });
  const send = within(panel).getByRole('button', { name: 'Send' });
  expect(send).toBeDisabled();
  fireEvent.change(input, { target: { value: 'How do I take a better photo?' } });
  expect(input).toHaveValue('How do I take a better photo?');
  expect(send).toBeEnabled();
  fireEvent.click(send);
  expect(within(panel).getByText('How do I take a better photo?')).toBeInTheDocument();
  expect(within(panel).getByText(/For a clearer photo/)).toBeInTheDocument();
  expect(input).toHaveValue('');
});

test('general guide is clearly separated from the latest photo result', () => {
  render(<DiseaseInfo info={healthyNutInfo} classId="Healthy_Nut" referenceOnly currentResultName="Healthy nut" onSelect={() => {}}/>);
  expect(screen.getByText(/General reference only/)).toBeInTheDocument();
  expect(screen.getByText(/Your latest screening result: Healthy nut/)).toBeInTheDocument();
  expect(screen.queryByText('The model leans toward the healthy nut class.')).not.toBeInTheDocument();
});

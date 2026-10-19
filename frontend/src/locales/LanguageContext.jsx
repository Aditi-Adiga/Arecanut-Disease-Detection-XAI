import { createContext, useContext, useMemo } from 'react';
import { LANGUAGES, translator } from './messages';

const LanguageContext = createContext({ language: 'en', t: translator('en'), locale: 'en-IN' });
export function LanguageProvider({ language, children }) {
  const value = useMemo(() => ({ language, t: translator(language), locale: LANGUAGES.find(item => item.code === language)?.locale || 'en-IN' }), [language]);
  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}
export function useLanguage() { return useContext(LanguageContext); }

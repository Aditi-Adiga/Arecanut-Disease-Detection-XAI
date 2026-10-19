import { createContext, useContext } from 'react';
import { LANGUAGES, translator } from './messages';

const LanguageContext = createContext({ language: 'en', t: translator('en'), locale: 'en-IN' });
export function LanguageProvider({ language, children }) {
  return <LanguageContext.Provider value={{ language, t: translator(language), locale: LANGUAGES.find(item => item.code === language)?.locale || 'en-IN' }}>{children}</LanguageContext.Provider>;
}
export function useLanguage() { return useContext(LanguageContext); }

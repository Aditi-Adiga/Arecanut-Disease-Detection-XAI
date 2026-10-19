const answers = {
  en: {
    signs: 'Look for yellow tips or spots on leaves, and dark or water-soaked patches on nuts. These signs alone cannot confirm a disease.',
    care: 'Take a clear close-up photo in daylight and watch whether the change spreads. Ask a local agricultural officer or KVK before using a treatment.',
    cause: 'A photo cannot reliably identify the cause. Similar signs can have different causes, so ask a local agricultural officer or KVK if the plant is worsening.',
    score: 'A model score compares the supported classes; it is not the chance that a diagnosis is correct. Run a photo screening to see a score for your plant.',
    result: 'Your latest screening suggests {name} ({score} relative model score). This is not a confirmed diagnosis. Ask an agricultural expert if you are concerned.',
  },
  kn: {
    signs: 'ಎಲೆಗಳ ತುದಿ ಹಳದಿಯಾಗಿದೆಯೇ ಅಥವಾ ಕಲೆಗಳಿವೆಯೇ ನೋಡಿ; ಕಾಯಿಯಲ್ಲಿ ಕಪ್ಪು ಅಥವಾ ನೀರು ನೆನೆದಂತೆ ಕಾಣುವ ಭಾಗಗಳನ್ನೂ ಗಮನಿಸಿ. ಇವು ಮಾತ್ರದಿಂದ ರೋಗ ದೃಢವಾಗುವುದಿಲ್ಲ.',
    care: 'ಹಗಲಿನ ಬೆಳಕಿನಲ್ಲಿ ಹತ್ತಿರದ ಸ್ಪಷ್ಟ ಫೋಟೋ ತೆಗೆದು, ಬದಲಾವಣೆ ಹರಡುತ್ತಿದೆಯೇ ಗಮನಿಸಿ. ಚಿಕಿತ್ಸೆ ಬಳಸುವ ಮೊದಲು ಸ್ಥಳೀಯ ಕೃಷಿ ಅಧಿಕಾರಿ ಅಥವಾ KVKಯನ್ನು ಸಂಪರ್ಕಿಸಿ.',
    cause: 'ಫೋಟೋದಿಂದ ಕಾರಣವನ್ನು ಖಚಿತವಾಗಿ ಗುರುತಿಸಲಾಗುವುದಿಲ್ಲ. ಒಂದೇ ರೀತಿಯ ಲಕ್ಷಣಗಳಿಗೆ ಬೇರೆ ಕಾರಣಗಳಿರಬಹುದು; ಗಿಡದ ಸ್ಥಿತಿ ಹದಗೆಟ್ಟರೆ ಸ್ಥಳೀಯ ಕೃಷಿ ಅಧಿಕಾರಿ ಅಥವಾ KVKಯನ್ನು ಸಂಪರ್ಕಿಸಿ.',
    score: 'ಮಾದರಿಯ ಅಂಕವು ಬೆಂಬಲಿತ ವರ್ಗಗಳನ್ನು ಹೋಲಿಸುತ್ತದೆ; ರೋಗನಿರ್ಣಯ ಸರಿಯಾಗಿರುವ ಸಾಧ್ಯತೆಯಲ್ಲ. ನಿಮ್ಮ ಗಿಡದ ಅಂಕ ನೋಡಲು ಫೋಟೋ ಪರಿಶೀಲನೆ ಮಾಡಿ.',
    result: 'ಇತ್ತೀಚಿನ ಪರಿಶೀಲನೆಯ ಅಂದಾಜು {name} ({score} ಹೋಲಿಕೆ ಅಂಕ). ಇದು ದೃಢವಾದ ರೋಗನಿರ್ಣಯವಲ್ಲ. ಚಿಂತೆ ಇದ್ದರೆ ಕೃಷಿ ತಜ್ಞರನ್ನು ಸಂಪರ್ಕಿಸಿ.',
  },
  hi: {
    signs: 'पत्तियों के सिरों का पीला होना या धब्बे देखें, और सुपारी पर गहरे या पानी से भीगे जैसे हिस्सों पर ध्यान दें। केवल इन लक्षणों से बीमारी की पुष्टि नहीं होती।',
    care: 'दिन की रोशनी में पास से साफ़ फोटो लें और देखें कि बदलाव फैल रहा है या नहीं। कोई उपचार करने से पहले स्थानीय कृषि अधिकारी या KVK से पूछें।',
    cause: 'फोटो से कारण की विश्वसनीय पहचान नहीं हो सकती। मिलते-जुलते लक्षणों के अलग कारण हो सकते हैं; पौधा बिगड़ रहा हो तो स्थानीय कृषि अधिकारी या KVK से सलाह लें।',
    score: 'मॉडल स्कोर समर्थित वर्गों की तुलना करता है; यह सही निदान की संभावना नहीं है। अपने पौधे का स्कोर देखने के लिए फोटो जाँच चलाएँ।',
    result: 'आपकी हाल की जाँच {name} का सुझाव देती है (तुलनात्मक मॉडल स्कोर {score})। यह पक्का निदान नहीं है। चिंता हो तो कृषि विशेषज्ञ से पूछें।',
  },
  ml: {
    signs: 'ഇലയുടെ അറ്റങ്ങൾ മഞ്ഞയാകുന്നതോ പാടുകളോ ഉണ്ടോ എന്ന് നോക്കുക; അടയ്ക്കയിലെ ഇരുണ്ടതോ വെള്ളം കെട്ടിയതുപോലെയോ ഉള്ള ഭാഗങ്ങളും ശ്രദ്ധിക്കുക. ഇതുകൊണ്ട് മാത്രം രോഗം സ്ഥിരീകരിക്കാനാകില്ല.',
    care: 'പകൽവെളിച്ചത്തിൽ അടുത്തുനിന്ന് വ്യക്തമായ ചിത്രം എടുക്കുക; മാറ്റം പടരുന്നുണ്ടോ എന്ന് ശ്രദ്ധിക്കുക. ചികിത്സയ്ക്ക് മുമ്പ് പ്രാദേശിക കൃഷി ഉദ്യോഗസ്ഥനെയോ KVKയെയോ സമീപിക്കുക.',
    cause: 'ചിത്രം മാത്രം ഉപയോഗിച്ച് കാരണം വിശ്വസനീയമായി തിരിച്ചറിയാനാകില്ല. ഒരേപോലുള്ള ലക്ഷണങ്ങൾക്ക് വ്യത്യസ്ത കാരണങ്ങളുണ്ടാകാം; ചെടി മോശമാകുന്നുവെങ്കിൽ പ്രാദേശിക കൃഷി ഉദ്യോഗസ്ഥനെയോ KVKയെയോ സമീപിക്കുക.',
    score: 'മോഡൽ സ്കോർ പിന്തുണയ്ക്കുന്ന വിഭാഗങ്ങളെ തമ്മിൽ താരതമ്യം ചെയ്യുന്നതാണ്; രോഗനിർണയം ശരിയാകാനുള്ള സാധ്യതയല്ല. നിങ്ങളുടെ ചെടിയുടെ സ്കോർ അറിയാൻ ചിത്രം പരിശോധിക്കുക.',
    result: 'ഏറ്റവും പുതിയ പരിശോധന {name} എന്ന് സൂചിപ്പിക്കുന്നു (താരതമ്യ മോഡൽ സ്കോർ {score}). ഇത് സ്ഥിരീകരിച്ച രോഗനിർണയമല്ല. ആശങ്കയുണ്ടെങ്കിൽ കൃഷി വിദഗ്ധനെ സമീപിക്കുക.',
  },
};

export function offlineChatAnswer(language, key, values = {}) {
  const template = answers[language]?.[key] || answers.en[key];
  return Object.entries(values).reduce((text, [name, value]) => text.replaceAll(`{${name}}`, String(value)), template);
}

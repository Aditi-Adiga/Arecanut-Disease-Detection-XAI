import { messages, LANGUAGES, translator } from './messages';
import { extraMessages } from './extraMessages';
import { localizeResult } from './localizeResult';

test('all four UI languages have the full set of English message keys', () => {
  for(const {code} of LANGUAGES) {
    expect(Object.keys(messages[code]).sort()).toEqual(Object.keys(messages.en).sort());
    expect(Object.values(messages[code]).every(value => typeof value==='string' && value.length>0)).toBe(true);
  }
});

test('language formatting replaces values without editing a numeric score', () => {
  expect(translator('kn')('savedScans',{count:3})).toContain('3');
  const result={class_id:'Healthy_Leaf',confidence:.83,status:'unsure',probabilities:[],explanation:{},photo_tips:[]};
  expect(localizeResult(result,null,translator('kn'))).toBe(result);
});

test('local help and reference notices exist in all four selected languages', () => {
  for (const { code } of LANGUAGES) {
    expect(extraMessages[code].chatWelcome).toBeTruthy();
    expect(extraMessages[code].generalGuideNote).toBeTruthy();
    expect(extraMessages[code].draftHealthyDescription).toBeTruthy();
  }
});

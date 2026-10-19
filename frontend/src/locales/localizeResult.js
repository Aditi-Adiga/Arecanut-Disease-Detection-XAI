import { formatScore } from '../services/format';

// Re-word a saved result. Numeric scores and the backend decision are preserved.
export function localizeResult(result, info, t) {
  if (!result || !info?.classes?.[result.class_id]) return result;
  const ci = info.classes[result.class_id], T = info.explanation.templates, th = info.explanation.thresholds;
  const ranking = [...result.probabilities].sort((a, b) => b.probability - a.probability), second = ranking[1];
  const pct = value => formatScore(value).replace('%', '');
  const fill = (text, values) => Object.entries(values).reduce((s, [key, value]) => s.replaceAll(`{${key}}`, value), text);
  let lines;
  if (result.status === 'unsure') {
    lines = [T.unsure_headline];
    if (second) lines.push(fill(T.top_guesses, { a: ci.short_name, pa: pct(result.confidence), b: info.classes[second.class_id].short_name, pb: pct(second.probability) }));
    if (ci.status === 'no_disease_found' && T.healthy_unsure_note) {
      lines.push(fill(T.healthy_unsure_note, { name: ci.short_name, pct: pct(result.confidence), cutoff: pct(th.healthy_below) }));
    }
    lines.push(...info.uncertain_result.what_to_do.map(item => item.text), T.heatmap_note);
  } else {
    const healthy = result.status === 'healthy';
    lines = [fill(T[healthy ? 'headline_healthy' : 'headline_suspected'], { name: ci.display_name }), fill(T[result.confidence >= th.high_at ? 'conf_high' : 'conf_medium'], { pct: pct(result.confidence) })];
    if (second && second.probability >= th.second_choice_at) lines.push(fill(T.second_choice, { other: info.classes[second.class_id].short_name, pct: pct(second.probability) }));
    const { where, concentration } = result.explanation;
    lines.push(!where || where === 'several_areas' || concentration < th.spread_below ? T.attention_spread : fill(T[healthy ? 'attention_focused_healthy' : 'attention_focused'], { where: info.explanation.positions[where] }));
    lines.push(`${T.check_signs_intro} ${ci.check_signs.map(item => item.text).join('; ')}.`);
    if (ci.also_consider?.length) lines.push(`${T.other_possibilities_intro} ${ci.also_consider.map(item => item.name).join(', ')}.`);
    lines.push(T.heatmap_note);
  }
  return { ...result, language: info.language, display_name: ci.display_name,
    healthy_guess_below_threshold: result.status === 'unsure' && ci.status === 'no_disease_found',
    healthy_cutoff: th.healthy_below,
    probabilities: result.probabilities.map(item => ({ ...item, label: info.classes[item.class_id].short_name })),
    explanation: { ...result.explanation, lines }, scope_note: t('scope'),
    photo_tips: result.photo_tips.map(tip => tip.includes('dark') ? t('darkTip') : tip.includes('bright') ? t('brightTip') : tip) };
}

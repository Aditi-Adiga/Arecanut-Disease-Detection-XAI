import 'dart:math' as math;

class ChatReply {
  final String answer;
  final String intent;
  final String? entryId;
  final List<String> sources;
  final double score;
  final bool refused;
  final bool needsExpertReview;
  final bool languageFallback;
  final List<Map<String, String>> suggestions;

  ChatReply({
    required this.answer,
    required this.intent,
    this.entryId,
    required this.sources,
    required this.score,
    required this.refused,
    required this.needsExpertReview,
    required this.languageFallback,
    required this.suggestions,
  });

  Map<String, dynamic> toJson() => {
    'answer': answer,
    'intent': intent,
    'entry_id': entryId,
    'sources': sources,
    'score': score,
    'refused': refused,
    'needs_expert_review': needsExpertReview,
    'language_fallback': languageFallback,
    'suggestions': suggestions,
  };
}

class ChatEngine {
  static final RegExp _tokenRegex = RegExp(r'[\p{L}\p{N}_]+', unicode: true);

  static const Set<String> _stop = {
    'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'am', 'do',
    'does', 'did', 'to', 'of', 'in', 'on', 'at', 'for', 'from', 'with', 'by',
    'and', 'or', 'if', 'it', 'its', 'this', 'that', 'these', 'those', 'i',
    'me', 'my', 'we', 'our', 'you', 'your', 'can', 'could', 'should', 'would',
    'will', 'shall', 'may', 'might', 'please', 'tell', 'about', 'any',
    'there', 'here', 'have', 'has', 'had', 'get', 'got', 'so', 'very', 'much'
  };

  static const Map<String, String> _syn = {
    'mahali': 'koleroga', 'kole': 'koleroga', 'kolleroga': 'koleroga', 'mahaali': 'koleroga',
    'fell': 'fall', 'dropp': 'fall', 'drop': 'fall', 'shedd': 'fall', 'shed': 'fall',
    'rott': 'rot', 'rotten': 'rot', 'rot': 'rot', 'decay': 'rot',
    'cure': 'treatment', 'treat': 'treatment', 'remedy': 'treatment', 'medicine': 'treatment',
    'solution': 'treatment', 'fix': 'treatment',
    'protect': 'prevention', 'prevent': 'prevention', 'avoid': 'prevention', 'stop': 'prevention',
    'pictur': 'photo', 'picture': 'photo', 'image': 'photo', 'pic': 'photo', 'camera': 'photo',
    'color': 'colour', 'colour': 'colour',
    'reliable': 'accuracy', 'accurate': 'accuracy', 'trust': 'accuracy', 'mistake': 'wrong',
    'uncertain': 'unsure', 'diseas': 'disease', 'symptom': 'sign', 'leav': 'leaf', 'leaves': 'leaf',
    'officer': 'expert', 'kvk': 'expert', 'scientist': 'expert', 'doctor': 'expert',
    'internet': 'offline', 'network': 'offline', 'signal': 'offline', 'connection': 'offline',
    'pest': 'pests', 'insect': 'pests', 'hopper': 'pests',
  };

  static const Set<String> _topic = {
    'koleroga', 'yellow', 'spot', 'bordeaux', 'bud', 'foot', 'nut', 'leaf', 'crown', 'spindle', 'trunk'
  };

  static final RegExp _dose = RegExp(
    r'\b(dose|dosage|how (many|much)\b.*\b(ml|gram|grams|g|kg|litre|liter)|per (litre|liter|acre|hectare|palm)|'
    r'\d+\s*(ml|mg|g|kg|ppm)\b|ppm|mixing ratio|concentration)\b',
    caseSensitive: false,
  );

  static final RegExp _chem = RegExp(
    r'\b(antibiotic|tetracycline|dimethoate|insecticide|pesticide|fungicide|mancozeb|metalaxyl|'
    r'copper oxychloride|weedicide|herbicide|which (chemical|spray|product|brand))\b',
    caseSensitive: false,
  );

  static final RegExp _health = RegExp(
    r'\b(fever|cough|headache|pregnan\w*|snake|poison\w*|swallow\w*|hospital|tablet|vomit\w*|'
    r'my (child|son|daughter|baby|wife|husband)|i feel (sick|unwell|dizzy))\b',
    caseSensitive: false,
  );

  static final RegExp _out = RegExp(
    r'\b(price|rate today|market|weather|forecast|will it rain|rain tomorrow|subsidy|loan|insurance|coconut|paddy|rice|banana|'
    r'pepper|cocoa|rubber|tomato|cow|goat)\b',
    caseSensitive: false,
  );

  static final RegExp _confirm = RegExp(
    r'\b(confirm\w*|diagnos\w*|100 ?%|for sure|certain)\b',
    caseSensitive: false,
  );

  static final RegExp _advice = RegExp(
    r'\b(what (should|do|can|shall) i do|what now|next step|what to do|advice|how (do|can|to) (i )?(treat|fix|save))\b|'
    r'(ಈಗ ನಾನು ಏನು ಮಾಡಬೇಕು|ಮುಂದಿನ ಕ್ರಮ|ಮುಂದೆ ಏನು ಮಾಡಬೇಕು|ಸಲಹೆ)|'
    r'(अब मुझे क्या करना चाहिए|अगला कदम|क्या करूँ|सलाह)|'
    r'(ഇനി ഞാൻ എന്താണ് ചെയ്യേണ്ടത്|അടുത്ത നടപടി|എന്ത് ചെയ്യണം|ഉപദേശം)',
    caseSensitive: false,
    unicode: true,
  );

  final Map<String, dynamic> faq;
  final Map<String, dynamic>? info;
  final double minScore;

  late final Map<String, Map<String, dynamic>> entries;
  late final Map<String, Set<String>> kw;
  late final Map<String, Set<String>> qt;
  late final Map<String, double> idf;

  ChatEngine(this.faq, {this.info, this.minScore = 0.5}) {
    entries = {};
    final rawEntries = (faq['entries'] as List<dynamic>? ?? []).cast<Map<String, dynamic>>();
    for (final e in rawEntries) {
      entries[e['id'] as String] = e;
    }

    kw = {};
    qt = {};
    final df = <String, int>{};

    for (final e in rawEntries) {
      final eid = e['id'] as String;
      final kws = <String>{};
      for (final k in (e['keywords'] as List<dynamic>? ?? [])) {
        kws.addAll(tokenize(k.toString()));
      }

      final qts = <String>{};
      final qs = (e['questions'] as List<dynamic>? ?? []).map((x) => x.toString()).toList();
      final qI18n = e['questions_i18n'] as Map<String, dynamic>? ?? {};
      for (final list in qI18n.values) {
        if (list is List) {
          qs.addAll(list.map((x) => x.toString()));
        }
      }
      for (final q in qs) {
        qts.addAll(tokenize(q));
      }

      kw[eid] = kws;
      qt[eid] = qts;

      final combined = {...kws, ...qts};
      for (final t in combined) {
        df[t] = (df[t] ?? 0) + 1;
      }
    }

    final n = entries.length;
    idf = {};
    df.forEach((t, c) {
      idf[t] = math.log((n + 1.0) / (c + 0.5)) + 0.1;
    });
  }

  static String _stem(String t) {
    for (final suf in const ['ing', 'ed', 'es', 's']) {
      if (t.length > suf.length + 3 && t.endsWith(suf)) {
        return t.substring(0, t.length - suf.length);
      }
    }
    return t;
  }

  static List<String> tokenize(String text) {
    final lower = text.toLowerCase();
    final out = <String>[];
    for (final m in _tokenRegex.allMatches(lower)) {
      final t = m.group(0)!;
      if (_stop.contains(t)) continue;
      final stemmed = _stem(t);
      out.add(_syn[stemmed] ?? stemmed);
    }
    return out;
  }

  List<Map<String, String>> _chips(String lang, [List<String>? ids]) {
    final out = <Map<String, String>>[];
    final chipIds = ids ?? (faq['chips'] as List<dynamic>? ?? []).cast<String>();
    for (final eid in chipIds) {
      final e = entries[eid];
      if (e == null) continue;
      final qI18n = e['questions_i18n'] as Map<String, dynamic>?;
      List<dynamic>? qs = qI18n?[lang] as List<dynamic>?;
      if (qs == null || qs.isEmpty) {
        qs = e['questions'] as List<dynamic>?;
      }
      final firstQ = (qs != null && qs.isNotEmpty) ? qs.first.toString() : eid;
      out.add({'id': eid, 'question': firstQ});
    }
    return out;
  }

  ChatReply _reply({
    required String answer,
    required String intent,
    Map<String, dynamic>? entry,
    List<String> sources = const [],
    double score = 0.0,
    bool refused = false,
    String lang = 'en',
    List<Map<String, String>>? suggestions,
    Map<String, dynamic>? i18nMap,
  }) {
    bool fallbackLang = false;
    String finalAnswer = answer;

    if (lang != 'en') {
      if (entry != null) {
        final i18n = entry['i18n'] as Map<String, dynamic>?;
        final translated = i18n?[lang] as String?;
        if (translated != null && translated.isNotEmpty) {
          finalAnswer = translated;
        } else {
          fallbackLang = true;
        }
      } else if (i18nMap != null) {
        final translated = i18nMap[lang] as String?;
        if (translated != null && translated.isNotEmpty) {
          finalAnswer = translated;
        } else {
          fallbackLang = true;
        }
      } else {
        fallbackLang = true;
      }
    }

    final needsReview = entry != null && (entry['needs_expert_review'] as bool? ?? false);

    return ChatReply(
      answer: finalAnswer,
      intent: intent,
      entryId: entry?['id'] as String?,
      sources: sources,
      score: (score * 1000).round() / 1000.0,
      refused: refused,
      needsExpertReview: needsReview,
      languageFallback: fallbackLang,
      suggestions: suggestions ?? _chips(lang),
    );
  }

  ChatReply? _currentResultAdvice(Map<String, dynamic> ctx, String lang) {
    if (info == null) return null;
    final cls = ctx['class'] as String?;
    final classes = info!['classes'] as Map<String, dynamic>?;
    if (cls == null || classes == null || !classes.containsKey(cls)) return null;

    final ci = classes[cls] as Map<String, dynamic>;
    final summaryObj = ci['summary'] as Map<String, dynamic>? ?? {};
    final parts = <String>[summaryObj['text'] as String? ?? ''];
    final src = <String>{};
    for (final s in (summaryObj['sources'] as List<dynamic>? ?? [])) {
      src.add(s.toString());
    }

    final todo = ci['what_to_do'] as List<dynamic>? ?? [];
    if (todo.isNotEmpty) {
      final todoLines = <String>[];
      for (final x in todo) {
        if (x is Map<String, dynamic>) {
          todoLines.add('- ${x['text']}');
          for (final s in (x['sources'] as List<dynamic>? ?? [])) {
            src.add(s.toString());
          }
        }
      }
      parts.add('What to do:\n${todoLines.join('\n')}');
    }

    final limits = ci['limits'] as Map<String, dynamic>?;
    if (limits != null && limits['text'] != null) {
      parts.add(limits['text'].toString());
    }

    final sortedSrc = src.toList()..sort();
    return _reply(
      answer: parts.join('\n\n'),
      intent: 'current_result_advice',
      sources: sortedSrc,
      lang: lang,
    );
  }

  ChatReply answer(String message, {String language = 'en', Map<String, dynamic>? context}) {
    final msg = message.trim();
    final ctx = context ?? {};
    final fb = faq['fallback'] as Map<String, dynamic>;
    final s = faq['safety'] as Map<String, dynamic>;

    if (msg.isEmpty) {
      return _reply(
        answer: fb['text'] as String,
        intent: 'fallback',
        lang: language,
        i18nMap: fb['i18n'] as Map<String, dynamic>?,
      );
    }

    final low = msg.toLowerCase();

    // 1. Health check
    if (_health.hasMatch(low)) {
      return _reply(
        answer: s['health'] as String,
        intent: 'safety_health',
        refused: true,
        lang: language,
        i18nMap: s['health_i18n'] as Map<String, dynamic>?,
      );
    }

    // 2. Bordeaux check
    final hasBordeaux = RegExp(r'bordeaux|bordo', caseSensitive: false).hasMatch(low);
    final hasBordDetails = _dose.hasMatch(low) ||
        RegExp(r'copper|sulphate|lime|make|prepar', caseSensitive: false).hasMatch(low);
    if (hasBordeaux && hasBordDetails) {
      final bEntry = entries['bordeaux_how']!;
      final bSources = (bEntry['sources'] as List<dynamic>? ?? []).cast<String>();
      return _reply(
        answer: bEntry['answer'] as String,
        intent: 'bordeaux_how',
        entry: bEntry,
        sources: bSources,
        lang: language,
      );
    }

    // 3. Dose check
    if (_dose.hasMatch(low)) {
      return _reply(
        answer: s['dose'] as String,
        intent: 'safety_dose',
        refused: true,
        lang: language,
        i18nMap: s['dose_i18n'] as Map<String, dynamic>?,
      );
    }

    // 4. Chemical check
    if (_chem.hasMatch(low)) {
      return _reply(
        answer: s['chemical'] as String,
        intent: 'safety_chemical',
        refused: true,
        lang: language,
        i18nMap: s['chemical_i18n'] as Map<String, dynamic>?,
      );
    }

    // 5. Out of scope check
    if (_out.hasMatch(low)) {
      return _reply(
        answer: s['out_of_scope'] as String,
        intent: 'out_of_scope',
        refused: true,
        lang: language,
        i18nMap: s['out_of_scope_i18n'] as Map<String, dynamic>?,
      );
    }

    final qtok = tokenize(msg);

    // 6. Confirm check
    if (_confirm.hasMatch(low)) {
      return _reply(
        answer: s['confirm'] as String,
        intent: 'safety_confirm',
        refused: true,
        lang: language,
        i18nMap: s['confirm_i18n'] as Map<String, dynamic>?,
      );
    }

    // 7. Context advice check
    final hasTopic = qtok.any((t) => _topic.contains(t));
    if (ctx['class'] != null && _advice.hasMatch(low) && !hasTopic) {
      final advice = _currentResultAdvice(ctx, language);
      if (advice != null) return advice;
    }

    // 8. Token scoring
    final qtokSet = qtok.toSet();
    final known = qtokSet.where((t) => idf.containsKey(t)).toList();
    if (known.isEmpty) {
      return _reply(
        answer: fb['text'] as String,
        intent: 'fallback',
        lang: language,
        i18nMap: fb['i18n'] as Map<String, dynamic>?,
      );
    }

    double total = 0.0;
    for (final t in known) {
      total += idf[t]!;
    }

    String? bestEid;
    double bestScore = 0.0;
    double secondScore = 0.0;

    for (final entry in entries.entries) {
      final eid = entry.key;
      final e = entry.value;

      final req = e['require'] as List<dynamic>?;
      if (req != null && req.isNotEmpty) {
        final reqTokens = tokenize(req.join(' '));
        if (!reqTokens.every((t) => qtokSet.contains(t))) {
          continue;
        }
      }

      final matched = known.where((t) => kw[eid]!.contains(t) || qt[eid]!.contains(t)).toList();
      if (matched.isEmpty) continue;

      double w = 0.0;
      for (final t in matched) {
        w += idf[t]! * (kw[eid]!.contains(t) ? 1.0 : 0.6);
      }

      double score = (w / total) * math.min(1.0, 0.5 + 0.25 * matched.length);
      final eClasses = (e['classes'] as List<dynamic>? ?? []).cast<String>();
      if (ctx['class'] != null && eClasses.contains(ctx['class'])) {
        score *= 1.15;
      }

      if (bestEid == null || score > bestScore) {
        secondScore = bestScore;
        bestScore = score;
        bestEid = eid;
      } else if (score > secondScore) {
        secondScore = score;
      }
    }

    if (bestEid == null || bestScore < minScore) {
      return _reply(
        answer: fb['text'] as String,
        intent: 'fallback',
        score: bestScore,
        lang: language,
        i18nMap: fb['i18n'] as Map<String, dynamic>?,
      );
    }

    final e = entries[bestEid]!;
    final eTopic = e['topic'] as String?;
    final same = <String>[];
    for (final other in entries.entries) {
      if (other.value['topic'] == eTopic && other.key != bestEid) {
        same.add(other.key);
        if (same.length >= 3) break;
      }
    }

    final sources = (e['sources'] as List<dynamic>? ?? []).cast<String>();

    return _reply(
      answer: e['answer'] as String,
      intent: 'faq',
      entry: e,
      sources: sources,
      score: bestScore,
      lang: language,
      suggestions: same.isNotEmpty ? _chips(language, same) : null,
    );
  }

  ChatReply answerById(String entryId, {String language = 'en', Map<String, dynamic>? context}) {
    if (!entries.containsKey(entryId)) {
      return answer('', language: language, context: context);
    }
    final e = entries[entryId]!;
    final eTopic = e['topic'] as String?;
    final same = <String>[];
    for (final other in entries.entries) {
      if (other.value['topic'] == eTopic && other.key != entryId) {
        same.add(other.key);
        if (same.length >= 3) break;
      }
    }

    final sources = (e['sources'] as List<dynamic>? ?? []).cast<String>();

    return _reply(
      answer: e['answer'] as String,
      intent: 'faq',
      entry: e,
      sources: sources,
      score: 1.0,
      lang: language,
      suggestions: same.isNotEmpty ? _chips(language, same) : null,
    );
  }
}

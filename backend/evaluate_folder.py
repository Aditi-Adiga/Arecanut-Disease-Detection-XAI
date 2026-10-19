"""Evaluate a labelled folder without changing model weights or thresholds."""
import argparse
import json
from pathlib import Path
import numpy as np
from .inference import Predictor, CLASS_NAMES
from .preprocessing import preprocess_image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--images', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path('folder-evaluation.json'))
    args = parser.parse_args()
    predictor = Predictor()
    paths = [(p, index) for index, name in enumerate(CLASS_NAMES) for p in sorted((args.images / name).rglob('*')) if p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp'}]
    if not paths:
        parser.error('No labelled images found.')
    matrix = np.zeros((4, 4), dtype=int)
    rows, failed = [], []
    thresholds = predictor.info['explanation']['thresholds']
    for offset in range(0, len(paths), 16):
        batch, labels = [], []
        for path, label in paths[offset:offset + 16]:
            try:
                image, _ = preprocess_image(path.read_bytes())
                batch.append(image[0])
                labels.append((path, label))
            except Exception as error:
                failed.append({'file': str(path), 'error': str(error)})
        if not batch:
            continue
        probabilities = predictor.model(np.stack(batch), training=False).numpy()
        for (path, label), probs in zip(labels, probabilities):
            predicted = int(probs.argmax())
            confidence = float(probs[predicted])
            matrix[label, predicted] += 1
            cutoff = thresholds['healthy_below'] if predicted in (0, 1) else thresholds['unsure_below']
            rows.append({'file': str(path.relative_to(args.images)), 'actual': CLASS_NAMES[label], 'predicted': CLASS_NAMES[predicted], 'confidence': confidence, 'answered': confidence >= cutoff, 'correct': label == predicted})
        print(f'Processed {min(offset + 16, len(paths))}/{len(paths)}', flush=True)
    answered = [row for row in rows if row['answered']]
    accuracy = sum(row['correct'] for row in rows) / len(rows) if rows else None
    report = {'note': 'Photo-level results on the supplied folder. Split provenance is unverified; do not substitute for the handoff clean test benchmark. Thresholds were not tuned.',
              'count': len(rows), 'failed': failed, 'class_order': CLASS_NAMES,
              'counts': matrix.sum(axis=1).tolist(), 'confusion_matrix': matrix.tolist(),
              'raw_accuracy': accuracy, 'raw_errors': sum(not row['correct'] for row in rows),
              'unsure_count': len(rows) - len(answered),
              'answered_accuracy': sum(row['correct'] for row in answered) / len(answered) if answered else None,
              'wrong_examples': [row for row in rows if not row['correct']]}
    args.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items() if key not in {'wrong_examples', 'failed'}}, indent=2))


if __name__ == '__main__':
    main()

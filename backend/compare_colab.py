"""Compare the running app pipeline against independently saved Colab outputs."""
import argparse
import json
from pathlib import Path
import numpy as np
from .inference import Predictor
from .preprocessing import preprocess_image
from .cam import class_activation_map


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle', type=Path, required=True, help='Extracted reference_bundle.zip folder')
    parser.add_argument('--output', type=Path, default=Path('colab-parity-results.json'))
    args = parser.parse_args()
    baseline = json.loads((args.bundle / 'reference.json').read_text(encoding='utf-8'))
    predictor = Predictor()
    rows = []
    for row in baseline['rows']:
        batch, _ = preprocess_image((args.bundle / row['file']).read_bytes())
        probs, features = predictor.forward(batch)
        expected = np.array(row['probabilities'])
        heat = class_activation_map(features, predictor.weights, int(probs.argmax()))
        heat_reference = np.load(args.bundle / row['heat_file'], allow_pickle=False)
        delta = float(abs(probs - expected).max())
        heat_delta = float(abs(heat - heat_reference).max())
        rows.append({'file': row['file'], 'same_class': bool(probs.argmax() == expected.argmax()), 'probability_max_diff': delta, 'heatmap_max_diff': heat_delta, 'passed': bool(probs.argmax() == expected.argmax() and delta < 1e-4 and heat_delta < 1e-3)})
    passed = bool(rows) and all(row['passed'] for row in rows)
    args.output.write_text(json.dumps({'passed': passed, 'count': len(rows), 'colab_tensorflow': baseline['tensorflow'], 'rows': rows}, indent=2), encoding='utf-8')
    print(f"Colab parity {'PASS' if passed else 'FAIL'} on {len(rows)} photos. Report: {args.output}")
    raise SystemExit(0 if passed else 1)


if __name__ == '__main__':
    main()

"""Run this cell in Colab to create baseline results for 50 validation images.

Needs Drive mounted and the existing grouped manifest/model artifacts. Download
reference_bundle.zip, extract locally and run backend.compare_colab.
"""
import json
import zipfile
from pathlib import Path
import numpy as np
import pandas as pd
import tensorflow as tf

D = Path('/content/drive/MyDrive/arecanut_models')
model = tf.keras.models.load_model(D / 'checkpoints/grouped_MobileNetV3Small_best.keras', compile=False)
base = next(layer for layer in model.layers if isinstance(layer, tf.keras.Model))
_, bn, _, dense = model.layers[-4:]
weights = (bn.gamma.numpy() / np.sqrt(bn.moving_variance.numpy() + bn.epsilon))[:, None] * dense.kernel.numpy()
manifest = pd.read_csv(D / 'grouped_split_manifest.csv')
validation = manifest[manifest['split'].isin(['validation', 'val'])]
selected = validation.groupby('cls', group_keys=False).sample(n=13, random_state=42).head(50)
folder = Path('/content/arecalens_reference')
folder.mkdir(exist_ok=True)
rows = []
for index, row in enumerate(selected.itertuples()):
    path = Path(row.path)
    content = path.read_bytes()
    filename = f'{index:03d}_{path.name}'
    (folder / filename).write_bytes(content)
    batch = tf.cast(tf.image.resize(tf.io.decode_image(content, channels=3, expand_animations=False), (224, 224), method='bilinear'), tf.float32)[None]
    probabilities = model(batch, training=False).numpy()[0]
    features = base(batch, training=False).numpy()[0]
    heat = np.maximum(features @ weights[:, int(probabilities.argmax())], 0)
    heat = heat / (heat.max() + 1e-8)
    heat = tf.image.resize(heat[..., None], (224, 224), method='bicubic').numpy()[..., 0].clip(0, 1)
    heatfile = f'{index:03d}_heat.npy'
    np.save(folder / heatfile, heat)
    rows.append({'file': filename, 'label': row.cls, 'probabilities': probabilities.tolist(), 'heat_file': heatfile})
(folder / 'reference.json').write_text(json.dumps({'tensorflow': tf.__version__, 'rows': rows}), encoding='utf-8')
archive = Path('/content/reference_bundle.zip')
with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as bundle:
    for item in folder.iterdir():
        bundle.write(item, item.name)
print(f'Saved {len(rows)} reference photos in {archive}')
from google.colab import files
files.download(str(archive))

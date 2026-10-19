# ArecaLens — Arecanut Disease Detection with XAI

React + Vite frontend, FastAPI + TensorFlow backend. Uses the supplied trained MobileNetV3Small and deterministic class activation maps (CAM), with no external AI API.

## Run the completed local app

Open this repository folder in VS Code. In a PowerShell terminal:

```powershell
.\backend\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. Alternatively double-click `start.cmd`. Stop with Ctrl+C. The backend serves the built React interface and API from one port.

The laptop app works without internet **after dependencies, model assets, and the frontend build are installed locally**, while Python is running. A phone visiting an online deployment cannot independently predict offline with this implementation. A browser runtime and model conversion/parity validation would be a separate stage. Camera capture depends on browser/device support; desktop browsers normally offer a file picker.

## First setup / clean install

Python 3.13 (64-bit) and Node 22.15.1 were used for the local setup. TensorFlow 2.21 supports this Python/Windows combination. Later Keras compatibility is verified by loading the real model and comparing outputs.

```powershell
python -m venv backend\.venv
.\backend\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
npm.cmd --prefix frontend ci
npm.cmd --prefix frontend run build
```

On a disk-constrained laptop, set `$env:TEMP` and `$env:TMP` to an existing folder on the installation drive before pip installation. Do not copy a `.venv` between directories; recreate it.

`backend/requirements-lock.txt`, when present, records the exact packages in the verified Windows/Python 3.13 environment. Use `pip install -r backend/requirements-lock.txt` to reproduce it on the same platform.

## Local assets

The user approved including the Keras deployment model in this public repository for hosting. Other model binaries remain ignored. Asset locations:

```text
backend/models/mobilenetv3small.keras       # grouped_MobileNetV3Small_best.keras
backend/models/v3small_probs_features.tflite # optional parity export
backend/data/cam_weights.json
backend/data/disease_info.json             # supplied 0.3-draft
```

The app uses Keras for inference; the supplied TFLite export is retained for equivalence checks. `cam_weights.json` validates the derived Keras CAM weights and class order at startup. No ImageNet or other weights are downloaded by the app.

## Develop

Terminal 1, from repository root:

```powershell
.\backend\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
```

Terminal 2:

```powershell
npm.cmd --prefix frontend run dev
```

Open http://127.0.0.1:5173. Vite proxies `/api` to the backend. Rebuild the frontend and restart FastAPI after frontend changes when using the single-server build.

## Tests

```powershell
.\backend\.venv\Scripts\python.exe -m pytest -q
npm.cmd --prefix frontend test
```

Backend checks cover uploads, size limits, real-model response structure, raw pixel preprocessing, equality with the Colab resize expression, confidence boundaries, original Keras vs feature pipeline, and exported CAM weights. Frontend tests cover file validation, uncertain results and bounded local history. Synthetic images verify wiring only; they do not measure agricultural accuracy.

### Real-photo parity check

```powershell
.\backend\.venv\Scripts\python.exe -m backend.verify_parity --images "D:\path\to\50-reference-images" --output parity-results.json
```

This compares the original Keras graph, app feature pipeline, and supplied TFLite probabilities, features and heatmaps on the same preprocessing. Use at least 50 real reference photos spanning all four classes, including nuts held in a hand. It does **not** replace a match against saved Colab outputs; use the same artifacts and inputs when comparing across environments. Do not retune thresholds on the held-out test set.

For an independent saved Colab baseline, run `colab_reference_export.py` as one Colab cell after mounting Drive. It packages 50 validation photos with class probabilities and CAM arrays. Download and extract `reference_bundle.zip`, then run:

```powershell
.\backend\.venv\Scripts\python.exe -m backend.compare_colab --bundle "D:\path\to\reference_bundle"
```

Investigate any difference before describing Colab/app parity as verified.

## API

- `GET /api/health`: model availability.
- `GET /api/diseases`: supplied reference information.
- `POST /api/predict`: multipart `file`; returns probabilities, result status, CAM overlay, resized input and deterministic explanation.
- `/docs`: interactive FastAPI API documentation.

JPEG/PNG/WebP, maximum 10 MB and 24 MP. Images are decoded as RGB with TensorFlow and resized to 224×224 with `tf.image.resize(..., method="bilinear")`, raw float32 values in 0–255. The backbone contains normalization. The image is stretched like the training pipeline, not cropped. EXIF auto-rotation is deliberately not applied to avoid silently changing the supplied Colab loader.

CAM = ReLU(features @ effective weights), max-normalized, bicubic-resized and clipped. The weights incorporate BatchNorm scaling before the Dense layer. A CAM highlights evidence contributing to a class logit and does not prove the disease or localize a confirmed lesion.

Class order: Healthy_Leaf, Healthy_Nut, Mahali_Koleroga, Yellow_Leaf. Healthy result cutoff 0.95; suspected disease cutoff 0.70. Below those values the result is unsure. These are supplied validation thresholds, not guarantees or calibrated disease probabilities.

## Data, history and limitations

- English only. Kannada, Hindi and Malayalam require translations and review; no language selector pretends otherwise.
- History stores up to eight resized scans in localStorage on this browser/device; raw uploads are not saved to the backend filesystem. Deployment operators must separately control proxy/server logs and storage policies.
- The disease guide is the supplied draft. Expert review of treatment guidance, especially historical doses and schedules, remains outstanding. The unverified Bordeaux recipe and items explicitly marked `verify` are not displayed.
- The model has no unrelated-object/OOD class. It can confidently classify unsupported inputs. Use actual arecanut leaves/nuts and get expert confirmation.
- Yellow_Leaf may mix yellow leaf disease and leaf spotting; the interface retains this limitation.
- Real plantation validation, source-group limitations and hand-held-nut errors remain important. No new field accuracy is claimed by app tests.

## Hosting

`Dockerfile` builds React and serves it with FastAPI, installs TensorFlow CPU on Linux, honours the host's `PORT`, and supports `/api/ready` to check actual model readiness. `render.yaml` requests a free Singapore web service from branch `codex/arecalens-webapp`. Its memory limit must be verified during deployment; do not silently select a paid plan after failure. Cloud hosting needs an account and configuration; a local build alone does not mean the app is deployed.

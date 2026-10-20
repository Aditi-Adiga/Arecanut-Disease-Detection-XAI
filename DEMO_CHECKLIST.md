# Demo and completion checklist

## Before the presentation

1. Run `start.cmd` from the repository root and wait for `Application startup complete`.
2. Open http://127.0.0.1:8000. Check that **Local model ready** is visible.
3. Prepare labelled source photos from all four classes, an uncertain example, a hand-held nut example and a malformed file. Do not describe new real photos as confirmed labels without expert review.
4. Upload an image. Show the predicted class, top model score, probability distribution, CAM overlay, explanation and field guide.
5. Switch between **Model input** and **CAM overlay**. Explain that the resize matches training and a heatmap is attention, not a confirmed lesion.
6. Open scan history, reopen a saved result, and download its JSON report.
7. Click the **Ask** tab. Try the starter chips (e.g. "What is Koleroga?", "Photo tips"). Show the source badge and expert-review warning badge on relevant answers.
8. Send a follow-up question related to the last scan result using the "About your last result" chip.
9. Ask an out-of-scope question (e.g. "What is the market price?") — confirm it is refused gracefully.
10. Ask for a spray dose (e.g. "How many ml of Bordeaux per litre?") — confirm it is refused safely.
11. Turn off Wi-Fi while the local server is running. Refresh the localhost page and analyse again. This demonstrates a fully local laptop workflow — both screening and chat work offline. It does not demonstrate independent offline phone inference.
12. Run backend/frontend tests and retain the terminal results.

## Scientific validation still required

- Compare app predictions with saved Colab reference outputs on around 50 real photos, not synthetic images.
- Run 50–100 new plantation photos, with particular attention to hand-held nuts and early symptoms. Ask an expert to assess labels.
- Review the disease information with a plant pathologist/agricultural officer.
- Obtain native-speaker review of all Kannada, Hindi and Malayalam translations (currently draft).
- Document group split limitations and Yellow_Leaf/leaf-spot label ambiguity.

## What the demo can claim

The application loads the supplied trained model locally, uses the original preprocessing expression, applies the provided confidence thresholds, visualizes CAM and produces deterministic explanation text. The offline chatbot is grounded in a knowledge file — it never invents chemical doses and refuses disease confirmation. Automated app tests establish software behavior, not additional field accuracy.

## Test results (at last commit)

- **Backend pytest:** 58 passed, 0 failed.
- **Frontend vitest:** 25 passed, 0 failed.
- **Chat dev set:** 64/64 (100 %).
- **Chat unseen set:** 15/20 (75 %) exact match; 20/20 (100 %) safe outcomes.

## Further features

Cloud deployment, independent phone offline inference/PWA, reviewed translations, optional online LLM mode (Phase 6), Flutter mobile app (Phase 7), reminders, expert photo sharing and backup are separate stages. No unavailable feature is represented as complete in the interface.


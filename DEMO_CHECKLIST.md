# Demo and completion checklist

## Before the presentation

1. Run `start.cmd` from the repository root and wait for `Application startup complete`.
2. Open http://127.0.0.1:8000. Check that **Local model ready** is visible.
3. Prepare labelled source photos from all four classes, an uncertain example, a hand-held nut example and a malformed file. Do not describe new real photos as confirmed labels without expert review.
4. Upload an image. Show the predicted class, top model score, probability distribution, CAM overlay, explanation and field guide.
5. Switch between **Model input** and **CAM overlay**. Explain that the resize matches training and a heatmap is attention, not a confirmed lesion.
6. Open scan history, reopen a saved result, and download its JSON report.
7. Turn off Wi-Fi while the local server is running. Refresh the localhost page and analyse again. This demonstrates a fully local laptop workflow. It does not demonstrate independent offline phone inference.
8. Run backend/frontend tests and retain the terminal results.

## Scientific validation still required

- Compare app predictions with saved Colab reference outputs on around 50 real photos, not synthetic images.
- Run 50–100 new plantation photos, with particular attention to hand-held nuts and early symptoms. Ask an expert to assess labels.
- Review the disease information with a plant pathologist/agricultural officer.
- Obtain native-speaker review before adding Kannada, Hindi and Malayalam.
- Document group split limitations and Yellow_Leaf/leaf-spot label ambiguity.

## What the demo can claim

The application loads the supplied trained model locally, uses the original preprocessing expression, applies the provided confidence thresholds, visualizes CAM and produces deterministic explanation text. Automated app tests establish software behavior, not additional field accuracy.

## Further features

Cloud deployment, independent phone offline inference/PWA, reviewed translations, reminders, expert photo sharing and backup are separate stages. No unavailable feature is represented as complete in the interface.

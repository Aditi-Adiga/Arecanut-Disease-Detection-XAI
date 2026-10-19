"""Match the Colab loader: TensorFlow decode, RGB, bilinear, raw 0..255."""
import warnings
from io import BytesIO

import numpy as np
import tensorflow as tf
from PIL import Image, UnidentifiedImageError

MAX_BYTES = 10 * 1024 * 1024
MAX_PIXELS = 24_000_000
Image.MAX_IMAGE_PIXELS = MAX_PIXELS


def preprocess_image(content: bytes):
    if not content:
        raise ValueError("Choose an image before analysing.")
    if len(content) > MAX_BYTES:
        raise ValueError("The image must be 10 MB or smaller.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(content)) as image:
                if image.format not in {"JPEG", "PNG", "WEBP"}:
                    raise ValueError("Use a JPEG, PNG or WebP image.")
                if image.width * image.height > MAX_PIXELS:
                    raise ValueError("Use an image smaller than 24 megapixels.")
                image.verify()
        # WebP is converted only for decoding; JPEG/PNG use the exact Colab path.
        if content[:4] == b"RIFF":
            with Image.open(BytesIO(content)) as image:
                encoded = BytesIO()
                image.convert("RGB").save(encoded, format="PNG")
                content = encoded.getvalue()
        decoded = tf.io.decode_image(content, channels=3, expand_animations=False)
        resized = tf.image.resize(decoded, (224, 224), method="bilinear")
        pixels = tf.cast(resized, tf.float32).numpy()
    except ValueError:
        raise
    except (UnidentifiedImageError, OSError, tf.errors.InvalidArgumentError,
            Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValueError("This image could not be read. Choose a valid JPEG, PNG or WebP.") from exc
    # These checks are photo tips, not a calibrated disease/OOD rejection system.
    tips = []
    brightness = float(pixels.mean())
    if brightness < 35:
        tips.append("The photo is dark. Retake it in daylight for a clearer result.")
    if brightness > 235:
        tips.append("The photo is very bright. Avoid glare and direct flash.")
    return pixels[None, ...], tips

from io import BytesIO
import numpy as np
import tensorflow as tf
from PIL import Image
from backend.preprocessing import preprocess_image


def test_matches_colab_resize_exactly():
    pixels = np.random.default_rng(42).integers(0, 256, (317, 489, 3), dtype=np.uint8)
    buffer = BytesIO()
    Image.fromarray(pixels).save(buffer, format="JPEG")
    content = buffer.getvalue()
    batch, _ = preprocess_image(content)
    reference = tf.image.resize(tf.io.decode_image(content, channels=3, expand_animations=False), (224, 224), method="bilinear").numpy()[None]
    np.testing.assert_array_equal(batch, reference)
    assert batch.dtype == np.float32
    assert batch.max() > 1

"""Class activation maps for the validated GAP -> BatchNorm -> Dense head."""
from io import BytesIO
import base64

import numpy as np
import tensorflow as tf
from matplotlib import colormaps
from PIL import Image


def effective_weights(batch_norm, dense):
    return (batch_norm.gamma.numpy() / np.sqrt(batch_norm.moving_variance.numpy() + batch_norm.epsilon))[:, None] * dense.kernel.numpy()


def class_activation_map(features, weights, class_index):
    heat = np.maximum(features @ weights[:, class_index], 0)
    heat = heat / (heat.max() + 1e-8)
    return tf.image.resize(heat[..., None], (224, 224), method="bicubic").numpy()[..., 0].clip(0, 1)


def png_data_url(pixels):
    image = Image.fromarray(np.uint8(np.clip(pixels, 0, 255)))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def overlay_image(pixels, heat, alpha=0.45):
    colours = colormaps["jet"](heat)[..., :3]
    return png_data_url(np.clip((1 - alpha) * pixels / 255 + alpha * colours, 0, 1) * 255)

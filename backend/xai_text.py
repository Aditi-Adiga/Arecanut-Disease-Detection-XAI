"""The deterministic explanation rules from the supplied Colab script."""
import numpy as np
from .formatting import percentage_label

POS_KEY = {
    ("upper", "left"): "upper_left", ("upper", "centre"): "top", ("upper", "right"): "upper_right",
    ("middle", "left"): "left", ("middle", "centre"): "centre", ("middle", "right"): "right",
    ("lower", "left"): "lower_left", ("lower", "centre"): "bottom", ("lower", "right"): "lower_right",
}


def attention(heat, thresholds):
    flat = np.sort(heat.ravel())[::-1]
    concentration = float(flat[:int(0.2 * flat.size)].sum() / (flat.sum() + 1e-9))
    ys, xs = np.nonzero(heat >= 0.5)
    if len(ys) == 0:
        return concentration, None
    height, width = heat.shape
    spread = float(np.sqrt(ys.var() + xs.var()) / height)
    if spread > thresholds["several_areas_above"]:
        return concentration, "several_areas"
    cy, cx = ys.mean() / height, xs.mean() / width
    row = "upper" if cy < 1 / 3 else "lower" if cy > 2 / 3 else "middle"
    col = "left" if cx < 1 / 3 else "right" if cx > 2 / 3 else "centre"
    return concentration, POS_KEY[row, col]


def explain(probs, heat, info, class_names):
    ex = info["explanation"]
    th, templates = ex["thresholds"], ex["templates"]
    order = np.argsort(probs)[::-1]
    c, c2 = int(order[0]), int(order[1])
    conf, conf2 = float(probs[c]), float(probs[c2])
    ci, c2i = info["classes"][class_names[c]], info["classes"][class_names[c2]]
    conc, where = attention(heat, th)
    healthy = ci["status"] == "no_disease_found"
    cutoff = th["healthy_below"] if healthy else th["unsure_below"]
    if conf < cutoff:
        lines = [templates["unsure_headline"], templates["top_guesses"].format(
            a=ci.get("short_name", ci["display_name"]), pa=percentage_label(conf),
            b=c2i.get("short_name", c2i["display_name"]), pb=percentage_label(conf2))]
        if healthy:
            lines.append(templates["healthy_unsure_note"].format(
                name=ci.get("short_name", ci["display_name"]),
                pct=percentage_label(conf),
                cutoff=percentage_label(cutoff)))
        lines += [item["text"] for item in info["uncertain_result"]["what_to_do"]]
        lines.append(templates["heatmap_note"])
        status = "unsure"
    else:
        status = "healthy" if healthy else "suspected"
        lines = [templates["headline_healthy" if healthy else "headline_suspected"].format(name=ci["display_name"]),
                 templates["conf_high" if conf >= th["high_at"] else "conf_medium"].format(pct=percentage_label(conf))]
        if conf2 >= th["second_choice_at"]:
            lines.append(templates["second_choice"].format(other=c2i.get("short_name", c2i["display_name"]), pct=percentage_label(conf2)))
        if where is None or where == "several_areas" or conc < th["spread_below"]:
            lines.append(templates["attention_spread"])
        else:
            key = "attention_focused_healthy" if healthy else "attention_focused"
            lines.append(templates[key].format(where=ex["positions"][where]))
        signs = [item["text"].rstrip(".") for item in ci["check_signs"]]
        lines.append(templates["check_signs_intro"] + " " + "; ".join(s[:1].lower() + s[1:] for s in signs) + ".")
        alternatives = [item["name"] for item in ci.get("also_consider", [])]
        if alternatives:
            lines.append(templates["other_possibilities_intro"] + " " + ", ".join(alternatives) + ".")
        lines.append(templates["heatmap_note"])
    return {"status": status, "lines": lines, "confidence": conf, "concentration": conc,
            "where": where, "threshold": cutoff, "class_id": class_names[c]}

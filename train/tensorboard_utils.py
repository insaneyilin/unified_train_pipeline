import torch
from PIL import Image, ImageDraw

def to_float_image_batch(images: torch.Tensor) -> torch.Tensor:
    if images.ndim == 3:
        images = images.unsqueeze(1)
    if images.ndim != 4:
        raise ValueError(
            f"Expected image batch with 3 or 4 dims, got shape={tuple(images.shape)}."
        )

    image_batch = images.detach().cpu()
    if not torch.is_floating_point(image_batch):
        image_batch = image_batch.float()
        image_batch = image_batch / 255.0
    return image_batch.clamp(0.0, 1.0)


def render_confusion_matrix_image(confusion_matrix: torch.Tensor,
                                  normalize_rows: bool) -> torch.Tensor:
    matrix = confusion_matrix.to(torch.float32).cpu()
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError(
            f"Expected square confusion matrix, got shape={tuple(matrix.shape)}")

    if normalize_rows:
        row_sums = matrix.sum(dim=1, keepdim=True).clamp(min=1.0)
        matrix = matrix / row_sums
    else:
        max_value = float(matrix.max().item()) if matrix.numel() > 0 else 0.0
        if max_value > 0:
            matrix = matrix / max_value

    class_count = int(matrix.shape[0])
    cell = 24
    top_pad = 24
    left_pad = 24
    width = left_pad + class_count * cell
    height = top_pad + class_count * cell
    image = Image.new("L", (width, height), color=255)
    draw = ImageDraw.Draw(image)

    for gt_idx in range(class_count):
        for pred_idx in range(class_count):
            value = float(matrix[gt_idx, pred_idx].item())
            shade = int((1.0 - max(0.0, min(1.0, value))) * 255.0)
            x0 = left_pad + pred_idx * cell
            y0 = top_pad + gt_idx * cell
            x1 = x0 + cell - 1
            y1 = y0 + cell - 1
            draw.rectangle([x0, y0, x1, y1], fill=shade)

    for idx in range(class_count):
        x_center = left_pad + idx * cell + cell // 2
        y_center = top_pad + idx * cell + cell // 2
        draw.text((x_center - 3, 4), str(idx), fill=0)
        draw.text((4, y_center - 4), str(idx), fill=0)

    image_bytes = torch.ByteTensor(torch.ByteStorage.from_buffer(image.tobytes()))
    image_tensor = image_bytes.view(height, width).unsqueeze(0).to(dtype=torch.float32) / 255.0
    return image_tensor

export type ImageHint = {
  filename: string;
  width: number;
  height: number;
  aspect_ratio: number;
  brightness_score: number;
  texture_score: number;
  edge_density: number;
  saturation_score: number;
  green_ratio: number;
  warm_ratio: number;
  contrast_score: number;
  red_ratio: number;
  yellow_ratio: number;
  white_ratio: number;
};

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

export async function analyzeImageFile(file: File): Promise<ImageHint> {
  const dataUrl = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });

  const img = await new Promise<HTMLImageElement>((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = reject;
    image.src = dataUrl;
  });

  const targetWidth = 160;
  const targetHeight = Math.max(1, Math.round((img.height / img.width) * targetWidth));
  const canvas = document.createElement("canvas");
  canvas.width = targetWidth;
  canvas.height = targetHeight;
  const ctx = canvas.getContext("2d");
  if (!ctx) {
    return {
      filename: file.name,
      width: img.width,
      height: img.height,
      aspect_ratio: img.width / img.height,
      brightness_score: 0.5,
      texture_score: 0.5,
      edge_density: 0.5,
      saturation_score: 0.4,
      green_ratio: 0.2,
      warm_ratio: 0.3,
      contrast_score: 0.4,
      red_ratio: 0.2,
      yellow_ratio: 0.12,
      white_ratio: 0.18,
    };
  }

  ctx.drawImage(img, 0, 0, targetWidth, targetHeight);
  const { data } = ctx.getImageData(0, 0, targetWidth, targetHeight);
  let brightnessTotal = 0;
  let varianceTotal = 0;
  let edgeCount = 0;
  let saturationTotal = 0;
  let greenCount = 0;
  let warmCount = 0;
  let redCount = 0;
  let yellowCount = 0;
  let whiteCount = 0;
  const grayscale: number[] = [];

  for (let index = 0; index < data.length; index += 4) {
    const red = data[index];
    const green = data[index + 1];
    const blue = data[index + 2];
    const gray = 0.299 * red + 0.587 * green + 0.114 * blue;
    grayscale.push(gray);
    brightnessTotal += gray;
    const maxChannel = Math.max(red, green, blue);
    const minChannel = Math.min(red, green, blue);
    saturationTotal += maxChannel === 0 ? 0 : (maxChannel - minChannel) / maxChannel;
    if (red > green * 1.08 && red > blue * 1.15 && red > 80) {
      redCount += 1;
    }
    if (green > red * 0.95 && green > blue * 1.1) {
      greenCount += 1;
    }
    if (red > 110 && green > 105 && Math.abs(red - green) < 55 && blue < green * 0.78) {
      yellowCount += 1;
    }
    if (red > 185 && green > 185 && blue > 185 && Math.max(red, green, blue) - Math.min(red, green, blue) < 35) {
      whiteCount += 1;
    }
    if (red > blue * 1.15 && red > 80) {
      warmCount += 1;
    }
  }

  const meanBrightness = brightnessTotal / grayscale.length;
  for (let index = 0; index < grayscale.length; index += 1) {
    varianceTotal += Math.abs(grayscale[index] - meanBrightness);
    if (index > 0 && Math.abs(grayscale[index] - grayscale[index - 1]) > 18) {
      edgeCount += 1;
    }
  }

  return {
    filename: file.name,
    width: img.width,
    height: img.height,
    aspect_ratio: Number((img.width / Math.max(img.height, 1)).toFixed(3)),
    brightness_score: Number(clamp(meanBrightness / 255, 0, 1).toFixed(3)),
    texture_score: Number(clamp((varianceTotal / grayscale.length) / 64, 0, 1).toFixed(3)),
    edge_density: Number(clamp(edgeCount / grayscale.length, 0, 1).toFixed(3)),
    saturation_score: Number(clamp(saturationTotal / grayscale.length, 0, 1).toFixed(3)),
    green_ratio: Number(clamp(greenCount / grayscale.length, 0, 1).toFixed(3)),
    warm_ratio: Number(clamp(warmCount / grayscale.length, 0, 1).toFixed(3)),
    contrast_score: Number(clamp((varianceTotal / grayscale.length) / 96, 0, 1).toFixed(3)),
    red_ratio: Number(clamp(redCount / grayscale.length, 0, 1).toFixed(3)),
    yellow_ratio: Number(clamp(yellowCount / grayscale.length, 0, 1).toFixed(3)),
    white_ratio: Number(clamp(whiteCount / grayscale.length, 0, 1).toFixed(3)),
  };
}

export async function analyzeImageFiles(files: File[]): Promise<ImageHint[]> {
  return Promise.all(files.map((file) => analyzeImageFile(file)));
}

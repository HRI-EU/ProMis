export default class ColorHelper {
  //Takes hex and returns hue, "#f0a599" -> 8
  static calcHueByHex(hex) {
    return ColorHelper.hexToHsl(hex).h;
  }

  //Takes hue and returns hex, 8 -> "#f0a599"
  static calcHexByHue(hue) {
    return ColorHelper.hslToHex(hue, 74, 77);
  }

  //Takes hex and returns hsl, "#f0a599" -> HSL{h=8,s=74,l=77}
  static hexToHsl(hex) {
    var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    var r = parseInt(result[1], 16);
    var g = parseInt(result[2], 16);
    var b = parseInt(result[3], 16);
    r /= 255;
    g /= 255;
    b /= 255;
    var max = Math.max(r, g, b),
      min = Math.min(r, g, b);
    var h,
      s,
      l = (max + min) / 2;
    if (max == min) {
      h = s = 0; // achromatic
    } else {
      var d = max - min;
      s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
      switch (max) {
        case r:
          h = (g - b) / d + (g < b ? 6 : 0);
          break;
        case g:
          h = (b - r) / d + 2;
          break;
        case b:
          h = (r - g) / d + 4;
          break;
      }
      h /= 6;
    }
    var HSL = new Object();
    HSL["h"] = h;
    HSL["s"] = s;
    HSL["l"] = l;
    return HSL;
  }

  //Takes hsl and returns hex, (8, 74,77) -> "#f0a599"
  static hslToHex(h, s, l) {
    l /= 100;
    const a = (s * Math.min(l, 1 - l)) / 100;
    const f = (n) => {
      const k = (n + h / 30) % 12;
      const color = l - a * Math.max(Math.min(k - 3, 9 - k, 1), -1);
      return Math.round(255 * color)
        .toString(16)
        .padStart(2, "0"); // convert to Hex and prefix "0" if needed
    };
    return `#${f(0)}${f(8)}${f(4)}`;
  }

  //Takes hue and sat and creates hsl string: 'hsl(hue, sat%, 65 if pos is true else 35%)'
  static calcHslFromParams(hue, sat, positive = true) {
    let lightness = 65;
    if (!positive) {
      lightness = 35;
    }
    return `hsl(
            ${hue}, 
            ${sat}%, 
            ${lightness}%)`;
  }

  //Takes hue, sat and alpha and creates hsla string: 'hsla(hue, sat%, 50%, alpha)'
  static calcHslaFromParams(hue, sat, alpha, positive = true) {
    let lightness = 65;
    if (!positive) {
      lightness = 35;
    }
    return `hsla(
              ${hue}, 
              ${sat}%, 
              ${lightness}%,
              ${alpha}
              )`;
  }
}

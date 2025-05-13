class Panel {
  constructor(name, fg, bg) {
    this.id = 0;
    this.name = name;
    this.fg = fg;
    this.bg = bg;
    this.gradient = null;
    this.PR = Math.round(window.devicePixelRatio || 1);
    this.WIDTH = 90 * this.PR;
    this.HEIGHT = 48 * this.PR;
    this.TEXT_X = 3 * this.PR;
    this.TEXT_Y = 2 * this.PR;
    this.GRAPH_X = 3 * this.PR;
    this.GRAPH_Y = 15 * this.PR;
    this.GRAPH_WIDTH = 84 * this.PR;
    this.GRAPH_HEIGHT = 30 * this.PR;
    this.canvas = document.createElement("canvas");
    this.canvas.width = this.WIDTH;
    this.canvas.height = this.HEIGHT;
    this.canvas.style.width = "90px";
    this.canvas.style.height = "48px";
    this.canvas.style.position = "absolute";
    this.canvas.style.cssText = "width:90px;height:48px;background-color: transparent !important;";
    this.context = this.canvas.getContext("2d");
    this.initializeCanvas();
  }
  createGradient() {
    if (!this.context)
      throw new Error("No context");
    const gradient = this.context.createLinearGradient(
      0,
      this.GRAPH_Y,
      0,
      this.GRAPH_Y + this.GRAPH_HEIGHT
    );
    let startColor;
    const endColor = this.fg;
    switch (this.fg.toLowerCase()) {
      case "#0ff":
        startColor = "#006666";
        break;
      case "#0f0":
        startColor = "#006600";
        break;
      case "#ff0":
        startColor = "#666600";
        break;
      case "#e1e1e1":
        startColor = "#666666";
        break;
      default:
        startColor = this.bg;
        break;
    }
    gradient.addColorStop(0, startColor);
    gradient.addColorStop(1, endColor);
    return gradient;
  }
  initializeCanvas() {
    if (!this.context)
      return;
    this.context.imageSmoothingEnabled = false;
    this.context.font = "bold " + 9 * this.PR + "px Helvetica,Arial,sans-serif";
    this.context.textBaseline = "top";
    this.gradient = this.createGradient();
    this.context.fillStyle = this.bg;
    this.context.fillRect(0, 0, this.WIDTH, this.HEIGHT);
    this.context.fillStyle = this.fg;
    this.context.fillText(this.name, this.TEXT_X, this.TEXT_Y);
    this.context.fillStyle = this.bg;
    this.context.globalAlpha = 0.9;
    this.context.fillRect(this.GRAPH_X, this.GRAPH_Y, this.GRAPH_WIDTH, this.GRAPH_HEIGHT);
  }
  // Update only text portion
  update(value, maxValue, decimals = 0) {
    if (!this.context || !this.gradient)
      return;
    const min = Math.min(Infinity, value);
    const max = Math.max(maxValue, value);
    this.context.globalAlpha = 1;
    this.context.fillStyle = this.bg;
    this.context.fillRect(0, 0, this.WIDTH, this.GRAPH_Y);
    this.context.fillStyle = this.fg;
    this.context.fillText(
      `${value.toFixed(decimals)} ${this.name} (${min.toFixed(decimals)}-${parseFloat(max.toFixed(decimals))})`,
      this.TEXT_X,
      this.TEXT_Y
    );
  }
  // Update only graph portion
  updateGraph(valueGraph, maxGraph) {
    if (!this.context || !this.gradient)
      return;
    if (valueGraph === 0 && maxGraph === 0) {
      maxGraph = 1;
    }
    maxGraph = Math.max(maxGraph, valueGraph, 0.1);
    valueGraph = Math.max(valueGraph, 0);
    const graphX = Math.round(this.GRAPH_X);
    const graphY = Math.round(this.GRAPH_Y);
    const graphWidth = Math.round(this.GRAPH_WIDTH);
    const graphHeight = Math.round(this.GRAPH_HEIGHT);
    const pr = Math.round(this.PR);
    this.context.drawImage(
      this.canvas,
      graphX + pr,
      graphY,
      graphWidth - pr,
      graphHeight,
      graphX,
      graphY,
      graphWidth - pr,
      graphHeight
    );
    this.context.fillStyle = this.bg;
    this.context.fillRect(
      graphX + graphWidth - pr,
      graphY,
      pr,
      graphHeight
    );
    const columnHeight = Math.min(
      graphHeight,
      Math.round(valueGraph / maxGraph * graphHeight)
    );
    if (columnHeight > 0) {
      this.context.globalAlpha = 0.9;
      this.context.fillStyle = this.gradient;
      this.context.fillRect(
        graphX + graphWidth - pr,
        graphY + (graphHeight - columnHeight),
        pr,
        columnHeight
      );
    }
    this.context.globalAlpha = 1;
  }
}
export {
  Panel
};
//# sourceMappingURL=panel.js.map

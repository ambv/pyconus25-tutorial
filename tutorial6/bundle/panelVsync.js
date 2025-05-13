import { Panel } from "./panel.js";
class PanelVSync extends Panel {
  constructor(name, fg, bg) {
    super(name, fg, bg);
    this.vsyncValue = 0;
    this.SMALL_HEIGHT = 9 * this.PR;
    this.HEIGHT = this.SMALL_HEIGHT;
    this.WIDTH = 35 * this.PR;
    this.TEXT_Y = 0 * this.PR;
    this.canvas.height = this.HEIGHT;
    this.canvas.width = this.WIDTH;
    this.canvas.style.height = "9px";
    this.canvas.style.width = "35px";
    this.canvas.style.cssText = `
            width: 35px;
            height: 9px;
            position: absolute;
            top: 0;
            left: 0;
            background-color: transparent !important;
            pointer-events: none;
        `;
    this.initializeCanvas();
  }
  initializeCanvas() {
    if (!this.context)
      return;
    this.context.imageSmoothingEnabled = false;
    this.context.font = "bold " + 9 * this.PR + "px Helvetica,Arial,sans-serif";
    this.context.textBaseline = "top";
    this.context.globalAlpha = 1;
  }
  // Override update for VSync-specific display
  update(value, _maxValue, _decimals = 0) {
    if (!this.context)
      return;
    this.vsyncValue = value;
    this.context.clearRect(0, 0, this.WIDTH, this.HEIGHT);
    this.context.globalAlpha = 1;
    this.context.fillStyle = this.bg;
    this.context.fillText(
      `${value.toFixed(0)}Hz`,
      this.TEXT_X,
      this.TEXT_Y
    );
  }
  // Override updateGraph to do nothing (we don't need a graph for VSync)
  updateGraph(_valueGraph, _maxGraph) {
    return;
  }
  // Method to set the offset position relative to parent panel
  setOffset(x, y) {
    this.canvas.style.transform = `translate(${x}px, ${y}px)`;
  }
}
export {
  PanelVSync
};
//# sourceMappingURL=panelVsync.js.map

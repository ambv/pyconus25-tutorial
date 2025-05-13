import { Panel } from "./panel.js";
import { PanelVSync } from "./panelVsync.js";
const _Stats = class _Stats2 {
  constructor({
    trackGPU = false,
    trackCPT = false,
    trackHz = false,
    logsPerSecond = 4,
    graphsPerSecond = 30,
    samplesLog = 40,
    samplesGraph = 10,
    precision = 2,
    minimal = false,
    horizontal = true,
    mode = 0
  } = {}) {
    this.gl = null;
    this.ext = null;
    this.activeQuery = null;
    this.gpuQueries = [];
    this.threeRendererPatched = false;
    this.frameTimes = [];
    this.renderCount = 0;
    this.totalCpuDuration = 0;
    this.totalGpuDuration = 0;
    this.totalGpuDurationCompute = 0;
    this.gpuPanel = null;
    this.gpuPanelCompute = null;
    this.vsyncPanel = null;
    this.averageFps = { logs: [], graph: [] };
    this.averageCpu = { logs: [], graph: [] };
    this.averageGpu = { logs: [], graph: [] };
    this.averageGpuCompute = { logs: [], graph: [] };
    this.updateCounter = 0;
    this.lastMin = {};
    this.lastMax = {};
    this.lastValue = {};
    this.VSYNC_RATES = [
      { refreshRate: 60, frameTime: 16.67 },
      { refreshRate: 75, frameTime: 13.33 },
      { refreshRate: 90, frameTime: 11.11 },
      { refreshRate: 120, frameTime: 8.33 },
      { refreshRate: 144, frameTime: 6.94 },
      { refreshRate: 165, frameTime: 6.06 },
      { refreshRate: 240, frameTime: 4.17 }
    ];
    this.detectedVSync = null;
    this.frameTimeHistory = [];
    this.HISTORY_SIZE = 120;
    this.VSYNC_THRESHOLD = 0.05;
    this.lastFrameTime = 0;
    this.handleClick = (event) => {
      event.preventDefault();
      this.showPanel(++this.mode % this.dom.children.length);
    };
    this.handleResize = () => {
      this.resizePanel(this.fpsPanel);
      this.resizePanel(this.msPanel);
      if (this.gpuPanel)
        this.resizePanel(this.gpuPanel);
      if (this.gpuPanelCompute)
        this.resizePanel(this.gpuPanelCompute);
    };
    this.mode = mode;
    this.horizontal = horizontal;
    this.minimal = minimal;
    this.trackGPU = trackGPU;
    this.trackCPT = trackCPT;
    this.trackHz = trackHz;
    this.samplesLog = samplesLog;
    this.samplesGraph = samplesGraph;
    this.precision = precision;
    this.logsPerSecond = logsPerSecond;
    this.graphsPerSecond = graphsPerSecond;
    const prevGraphTime = performance.now();
    this.prevGraphTime = prevGraphTime;
    this.dom = document.createElement("div");
    this.initializeDOM();
    this.beginTime = performance.now();
    this.prevTextTime = this.beginTime;
    this.prevCpuTime = this.beginTime;
    this._panelId = 0;
    this.fpsPanel = this.addPanel(new _Stats2.Panel("FPS", "#0ff", "#002"));
    this.msPanel = this.addPanel(new _Stats2.Panel("CPU", "#0f0", "#020"));
    if (this.trackHz === true) {
      this.vsyncPanel = new PanelVSync("", "#f0f", "#202");
      this.dom.appendChild(this.vsyncPanel.canvas);
      this.vsyncPanel.setOffset(56, 35);
    }
    this.setupEventListeners();
  }
  initializeDOM() {
    this.dom.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      opacity: 0.9;
      z-index: 10000;
      ${this.minimal ? "cursor: pointer;" : ""}
    `;
  }
  setupEventListeners() {
    if (this.minimal) {
      this.dom.addEventListener("click", this.handleClick);
      this.showPanel(this.mode);
    } else {
      window.addEventListener("resize", this.handleResize);
    }
  }
  async init(canvasOrGL) {
    if (!canvasOrGL) {
      console.error('Stats: The "canvas" parameter is undefined.');
      return;
    }
    if (this.handleThreeRenderer(canvasOrGL))
      return;
    if (await this.handleWebGPURenderer(canvasOrGL))
      return;
    if (this.initializeWebGL(canvasOrGL)) {
      if (this.trackGPU) {
        this.initializeGPUTracking();
      }
      return;
    } else {
      console.error("Stats-gl: Failed to initialize WebGL context");
    }
  }
  handleThreeRenderer(renderer) {
    if (renderer.isWebGLRenderer && !this.threeRendererPatched) {
      this.patchThreeRenderer(renderer);
      this.gl = renderer.getContext();
      if (this.trackGPU) {
        this.initializeGPUTracking();
      }
      return true;
    }
    return false;
  }
  async handleWebGPURenderer(renderer) {
    if (renderer.isWebGPURenderer) {
      if (this.trackGPU || this.trackCPT) {
        renderer.backend.trackTimestamp = true;
        if (await renderer.hasFeatureAsync("timestamp-query")) {
          this.initializeWebGPUPanels();
        }
      }
      this.info = renderer.info;
      this.patchThreeWebGPU(renderer);
      return true;
    }
    return false;
  }
  initializeWebGPUPanels() {
    if (this.trackGPU) {
      this.gpuPanel = this.addPanel(new _Stats2.Panel("GPU", "#ff0", "#220"));
    }
    if (this.trackCPT) {
      this.gpuPanelCompute = this.addPanel(new _Stats2.Panel("CPT", "#e1e1e1", "#212121"));
    }
  }
  initializeWebGL(canvasOrGL) {
    if (canvasOrGL instanceof WebGL2RenderingContext) {
      this.gl = canvasOrGL;
    } else if (canvasOrGL instanceof HTMLCanvasElement || canvasOrGL instanceof OffscreenCanvas) {
      this.gl = canvasOrGL.getContext("webgl2");
      if (!this.gl) {
        console.error("Stats: Unable to obtain WebGL2 context.");
        return false;
      }
    } else {
      console.error(
        "Stats: Invalid input type. Expected WebGL2RenderingContext, HTMLCanvasElement, or OffscreenCanvas."
      );
      return false;
    }
    return true;
  }
  initializeGPUTracking() {
    if (this.gl) {
      this.ext = this.gl.getExtension("EXT_disjoint_timer_query_webgl2");
      if (this.ext) {
        this.gpuPanel = this.addPanel(new _Stats2.Panel("GPU", "#ff0", "#220"));
      }
    }
  }
  begin() {
    this.beginProfiling("cpu-started");
    if (!this.gl || !this.ext)
      return;
    if (this.activeQuery) {
      this.gl.endQuery(this.ext.TIME_ELAPSED_EXT);
    }
    this.activeQuery = this.gl.createQuery();
    if (this.activeQuery) {
      this.gl.beginQuery(this.ext.TIME_ELAPSED_EXT, this.activeQuery);
    }
  }
  end() {
    this.renderCount++;
    if (this.gl && this.ext && this.activeQuery) {
      this.gl.endQuery(this.ext.TIME_ELAPSED_EXT);
      this.gpuQueries.push({ query: this.activeQuery });
      this.activeQuery = null;
    }
    this.endProfiling("cpu-started", "cpu-finished", "cpu-duration");
  }
  update() {
    this.endProfiling("cpu-started", "cpu-finished", "cpu-duration");
    if (!this.info) {
      this.processGpuQueries();
    } else {
      this.processWebGPUTimestamps();
    }
    this.updateAverages();
    this.resetCounters();
  }
  processWebGPUTimestamps() {
    this.totalGpuDuration = this.info.render.timestamp;
    this.totalGpuDurationCompute = this.info.compute.timestamp;
  }
  resetCounters() {
    this.renderCount = 0;
    this.totalCpuDuration = 0;
    this.beginTime = this.endInternal();
  }
  resizePanel(panel) {
    panel.canvas.style.position = "absolute";
    if (this.minimal) {
      panel.canvas.style.display = "none";
    } else {
      panel.canvas.style.display = "block";
      if (this.horizontal) {
        panel.canvas.style.top = "0px";
        panel.canvas.style.left = panel.id * panel.WIDTH / panel.PR + "px";
      } else {
        panel.canvas.style.left = "0px";
        panel.canvas.style.top = panel.id * panel.HEIGHT / panel.PR + "px";
      }
    }
  }
  addPanel(panel) {
    if (panel.canvas) {
      this.dom.appendChild(panel.canvas);
      panel.id = this._panelId;
      this.resizePanel(panel);
      this._panelId++;
    }
    return panel;
  }
  showPanel(id) {
    for (let i = 0; i < this.dom.children.length; i++) {
      const child = this.dom.children[i];
      child.style.display = i === id ? "block" : "none";
    }
    this.mode = id;
  }
  processGpuQueries() {
    if (!this.gl || !this.ext)
      return;
    this.totalGpuDuration = 0;
    this.gpuQueries.forEach((queryInfo, index) => {
      if (this.gl) {
        const available = this.gl.getQueryParameter(queryInfo.query, this.gl.QUERY_RESULT_AVAILABLE);
        const disjoint = this.gl.getParameter(this.ext.GPU_DISJOINT_EXT);
        if (available && !disjoint) {
          const elapsed = this.gl.getQueryParameter(queryInfo.query, this.gl.QUERY_RESULT);
          const duration = elapsed * 1e-6;
          this.totalGpuDuration += duration;
          this.gl.deleteQuery(queryInfo.query);
          this.gpuQueries.splice(index, 1);
        }
      }
    });
  }
  detectVSync(currentTime) {
    if (this.lastFrameTime === 0) {
      this.lastFrameTime = currentTime;
      return;
    }
    const frameTime = currentTime - this.lastFrameTime;
    this.lastFrameTime = currentTime;
    this.frameTimeHistory.push(frameTime);
    if (this.frameTimeHistory.length > this.HISTORY_SIZE) {
      this.frameTimeHistory.shift();
    }
    if (this.frameTimeHistory.length < 60)
      return;
    const avgFrameTime = this.frameTimeHistory.reduce((a, b) => a + b) / this.frameTimeHistory.length;
    const variance = this.frameTimeHistory.reduce((acc, time) => acc + Math.pow(time - avgFrameTime, 2), 0) / this.frameTimeHistory.length;
    const stability = Math.sqrt(variance);
    if (stability > 2) {
      this.detectedVSync = null;
      return;
    }
    let closestMatch = null;
    let smallestDiff = Infinity;
    for (const rate of this.VSYNC_RATES) {
      const diff = Math.abs(avgFrameTime - rate.frameTime);
      if (diff < smallestDiff) {
        smallestDiff = diff;
        closestMatch = rate;
      }
    }
    if (closestMatch && smallestDiff / closestMatch.frameTime <= this.VSYNC_THRESHOLD) {
      this.detectedVSync = closestMatch;
    } else {
      this.detectedVSync = null;
    }
  }
  endInternal() {
    var _a;
    const currentTime = performance.now();
    this.frameTimes.push(currentTime);
    while (this.frameTimes.length > 0 && this.frameTimes[0] <= currentTime - 1e3) {
      this.frameTimes.shift();
    }
    const fps = Math.round(this.frameTimes.length);
    this.addToAverage(fps, this.averageFps);
    const shouldUpdateText = currentTime >= this.prevTextTime + 1e3 / this.logsPerSecond;
    const shouldUpdateGraph = currentTime >= this.prevGraphTime + 1e3 / this.graphsPerSecond;
    this.updatePanelComponents(this.fpsPanel, this.averageFps, 0, shouldUpdateText, shouldUpdateGraph);
    this.updatePanelComponents(this.msPanel, this.averageCpu, this.precision, shouldUpdateText, shouldUpdateGraph);
    if (this.gpuPanel) {
      this.updatePanelComponents(this.gpuPanel, this.averageGpu, this.precision, shouldUpdateText, shouldUpdateGraph);
    }
    if (this.trackCPT && this.gpuPanelCompute) {
      this.updatePanelComponents(this.gpuPanelCompute, this.averageGpuCompute, this.precision, shouldUpdateText, shouldUpdateGraph);
    }
    if (shouldUpdateText) {
      this.prevTextTime = currentTime;
    }
    if (shouldUpdateGraph) {
      this.prevGraphTime = currentTime;
    }
    if (this.vsyncPanel !== null) {
      this.detectVSync(currentTime);
      const vsyncValue = ((_a = this.detectedVSync) == null ? void 0 : _a.refreshRate) || 0;
      if (shouldUpdateText && vsyncValue > 0) {
        this.vsyncPanel.update(vsyncValue, vsyncValue);
      }
    }
    return currentTime;
  }
  updatePanelComponents(panel, averageArray, precision, shouldUpdateText, shouldUpdateGraph) {
    if (!panel || averageArray.logs.length === 0)
      return;
    if (!(panel.name in this.lastMin)) {
      this.lastMin[panel.name] = Infinity;
      this.lastMax[panel.name] = 0;
      this.lastValue[panel.name] = 0;
    }
    const currentValue = averageArray.logs[averageArray.logs.length - 1];
    this.lastMax[panel.name] = Math.max(...averageArray.logs);
    this.lastMin[panel.name] = Math.min(this.lastMin[panel.name], currentValue);
    this.lastValue[panel.name] = this.lastValue[panel.name] * 0.7 + currentValue * 0.3;
    const graphMax = Math.max(
      Math.max(...averageArray.logs),
      ...averageArray.graph.slice(-this.samplesGraph)
    );
    this.updateCounter++;
    if (shouldUpdateText) {
      panel.update(
        this.lastValue[panel.name],
        this.lastMax[panel.name],
        precision
      );
    }
    if (shouldUpdateGraph) {
      panel.updateGraph(
        currentValue,
        graphMax
      );
    }
  }
  beginProfiling(marker) {
    if (window.performance) {
      try {
        window.performance.clearMarks(marker);
        window.performance.mark(marker);
      } catch (error) {
        console.debug("Stats: Performance marking failed:", error);
      }
    }
  }
  endProfiling(startMarker, endMarker, measureName) {
    if (!window.performance || !endMarker || !startMarker)
      return;
    try {
      const entries = window.performance.getEntriesByName(startMarker, "mark");
      if (entries.length === 0) {
        this.beginProfiling(startMarker);
      }
      window.performance.clearMarks(endMarker);
      window.performance.mark(endMarker);
      window.performance.clearMeasures(measureName);
      const cpuMeasure = performance.measure(measureName, startMarker, endMarker);
      this.totalCpuDuration += cpuMeasure.duration;
      window.performance.clearMarks(startMarker);
      window.performance.clearMarks(endMarker);
      window.performance.clearMeasures(measureName);
    } catch (error) {
      console.debug("Stats: Performance measurement failed:", error);
    }
  }
  updatePanel(panel, averageArray, precision = 2) {
    if (!panel || averageArray.logs.length === 0)
      return;
    const currentTime = performance.now();
    if (!(panel.name in this.lastMin)) {
      this.lastMin[panel.name] = Infinity;
      this.lastMax[panel.name] = 0;
      this.lastValue[panel.name] = 0;
    }
    const currentValue = averageArray.logs[averageArray.logs.length - 1];
    const recentMax = Math.max(...averageArray.logs.slice(-30));
    this.lastMin[panel.name] = Math.min(this.lastMin[panel.name], currentValue);
    this.lastMax[panel.name] = Math.max(this.lastMax[panel.name], currentValue);
    this.lastValue[panel.name] = this.lastValue[panel.name] * 0.7 + currentValue * 0.3;
    const graphMax = Math.max(recentMax, ...averageArray.graph.slice(-this.samplesGraph));
    this.updateCounter++;
    if (this.updateCounter % (this.logsPerSecond * 2) === 0) {
      this.lastMax[panel.name] = recentMax;
      this.lastMin[panel.name] = currentValue;
    }
    if (panel.update) {
      if (currentTime >= this.prevCpuTime + 1e3 / this.logsPerSecond) {
        panel.update(
          this.lastValue[panel.name],
          currentValue,
          this.lastMax[panel.name],
          graphMax,
          precision
        );
      }
      if (currentTime >= this.prevGraphTime + 1e3 / this.graphsPerSecond) {
        panel.updateGraph(
          currentValue,
          graphMax
        );
        this.prevGraphTime = currentTime;
      }
    }
  }
  updateAverages() {
    this.addToAverage(this.totalCpuDuration, this.averageCpu);
    this.addToAverage(this.totalGpuDuration, this.averageGpu);
    if (this.info && this.totalGpuDurationCompute !== void 0) {
      this.addToAverage(this.totalGpuDurationCompute, this.averageGpuCompute);
    }
  }
  addToAverage(value, averageArray) {
    averageArray.logs.push(value);
    if (averageArray.logs.length > this.samplesLog) {
      averageArray.logs = averageArray.logs.slice(-this.samplesLog);
    }
    averageArray.graph.push(value);
    if (averageArray.graph.length > this.samplesGraph) {
      averageArray.graph = averageArray.graph.slice(-this.samplesGraph);
    }
  }
  get domElement() {
    return this.dom;
  }
  patchThreeWebGPU(renderer) {
    const originalAnimationLoop = renderer.info.reset;
    const statsInstance = this;
    renderer.info.reset = function() {
      statsInstance.beginProfiling("cpu-started");
      originalAnimationLoop.call(this);
    };
  }
  patchThreeRenderer(renderer) {
    const originalRenderMethod = renderer.render;
    const statsInstance = this;
    renderer.render = function(scene, camera) {
      statsInstance.begin();
      originalRenderMethod.call(this, scene, camera);
      statsInstance.end();
    };
    this.threeRendererPatched = true;
  }
};
_Stats.Panel = Panel;
let Stats = _Stats;
export {
  Stats as default
};
//# sourceMappingURL=main.js.map

type Point = {
  x: number;
  y: number;
  z?: number;
  space: 'image' | 'pdf' | 'dxf' | 'ifc';
};

type CalibrationState = {
  scaleMode: boolean;
  pointA: Point | null;
  pointB: Point | null;
  realWorldDistance: number | null;
  unit: string;
  scaleFactor: number | null;
};

let state: CalibrationState = {
  scaleMode: false,
  pointA: null,
  pointB: null,
  realWorldDistance: null,
  unit: 'm',
  scaleFactor: null,
};

const distance = (a: Point, b: Point) => {
  if (!a || !b) return 0;
  return Math.sqrt((b.x - a.x) ** 2 + (b.y - a.y) ** 2);
};

export const CalibrationManager = {
  enable() {
    state.scaleMode = true;
    state.pointA = null;
    state.pointB = null;
    state.scaleFactor = null;
  },

  disable() {
    state.scaleMode = false;
  },

  reset() {
    state.pointA = null;
    state.pointB = null;
    state.realWorldDistance = null;
    state.scaleFactor = null;
  },

  addPoint(point: Point) {
    if (!state.pointA) {
      state.pointA = point;
    } else if (!state.pointB) {
      state.pointB = point;
    } else {
      state.pointA = point;
      state.pointB = null;
    }
  },

  setRealWorldDistance(value: number, unit: string) {
    state.realWorldDistance = value;
    state.unit = unit;
    this.compute();
  },

  compute() {
    if (!state.pointA || !state.pointB || !state.realWorldDistance) return;

    const px = distance(state.pointA, state.pointB);
    if (px === 0) return;

    state.scaleFactor = state.realWorldDistance / px;
  },

  getState() {
    return state;
  },
};
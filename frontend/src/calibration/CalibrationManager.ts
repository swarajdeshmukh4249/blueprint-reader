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

const listeners = new Set<(nextState: CalibrationState) => void>();
const notify = () => listeners.forEach(listener => listener(state));

const distance = (a: Point, b: Point) => {
  if (!a || !b) return 0;
  return Math.sqrt(
    (b.x - a.x) ** 2 +
    (b.y - a.y) ** 2 +
    ((b.z ?? 0) - (a.z ?? 0)) ** 2
  );
};

export const CalibrationManager = {
  enable() {
    state.scaleMode = true;
    state.pointA = null;
    state.pointB = null;
    state.scaleFactor = null;
    notify();
  },

  disable() {
    state.scaleMode = false;
    notify();
  },

  reset() {
    state.scaleMode = false;
    state.pointA = null;
    state.pointB = null;
    state.realWorldDistance = null;
    state.scaleFactor = null;
    notify();
  },

  setScaleMode(value: boolean) {
    state.scaleMode = value;

    if (!value) {
      state.pointA = null;
      state.pointB = null;
      state.realWorldDistance = null;
      state.scaleFactor = null;
    }
    notify();
  },

  addPoint(point: Point) {
    if (!state.pointA) {
      state.pointA = point;
    } else if (!state.pointB) {
      state.pointB = point;
    } else {
      // A completed reference is deliberately immutable.  Changing it by
      // accident would invalidate the distance the user just entered.
      return;
    }
    notify();
  },

  reselectPoints() {
    state.pointA = null;
    state.pointB = null;
    state.scaleFactor = null;
    notify();
  },

  setRealWorldDistance(value: number, unit: string) {
    state.realWorldDistance = value;
    state.unit = unit;
    this.compute();
    notify();
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

  subscribe(listener: (nextState: CalibrationState) => void) {
    listeners.add(listener);
    return () => {
      listeners.delete(listener);
    };
  },
};

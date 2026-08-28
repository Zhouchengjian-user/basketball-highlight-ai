(function exposeTimelineUtilities(root, factory) {
  const utilities = factory();
  if (typeof module === "object" && module.exports) module.exports = utilities;
  root.CourtCastTimeline = utilities;
})(typeof globalThis === "object" ? globalThis : window, () => {
  const TICKS_PER_SECOND = 10;
  const MINIMUM_TICK = 1;

  function toTick(value) {
    if (value === "" || value === null || value === undefined) return null;
    const number = Number(value);
    return Number.isFinite(number) ? Math.round(number * TICKS_PER_SECOND) : null;
  }

  function fromTick(tick) {
    return tick / TICKS_PER_SECOND;
  }

  function maximumTick(duration) {
    const number = Number(duration);
    if (!Number.isFinite(number) || number <= 0.2) return MINIMUM_TICK;
    return Math.max(
      MINIMUM_TICK,
      Math.floor((number - 0.1 + Number.EPSILON) * TICKS_PER_SECOND),
    );
  }

  function clampTime(value, duration) {
    const maximum = maximumTick(duration);
    const tick = toTick(value);
    return fromTick(Math.min(maximum, Math.max(MINIMUM_TICK, tick ?? MINIMUM_TICK)));
  }

  function findInsertionTime({ previous, next, duration, fallback } = {}) {
    const maximum = maximumTick(duration);
    const previousTick = toTick(previous);
    const nextTick = toTick(next);

    if (previousTick !== null && nextTick !== null) {
      if (nextTick - previousTick <= 1) return null;
      return fromTick(Math.floor((previousTick + nextTick) / 2));
    }
    if (nextTick !== null) {
      if (nextTick <= MINIMUM_TICK) return null;
      return fromTick(MINIMUM_TICK);
    }
    if (previousTick !== null) {
      if (previousTick >= maximum) return null;
      const distance = maximum - previousTick;
      return fromTick(Math.min(maximum, previousTick + Math.max(1, Math.floor(distance / 2))));
    }
    return clampTime(fallback ?? fromTick(Math.floor((MINIMUM_TICK + maximum) / 2)), duration);
  }

  function validateTimes(values, duration) {
    const maximum = maximumTick(duration);
    const seen = new Set();
    const normalized = [];
    for (let index = 0; index < values.length; index += 1) {
      const tick = toTick(values[index]);
      if (tick === null || tick < MINIMUM_TICK || tick > maximum) {
        return {
          ok: false,
          normalized,
          message: `第 ${index + 1} 个事件时间需要在 00:00.1 到 ${formatTick(maximum)} 之间。`,
        };
      }
      if (seen.has(tick)) {
        return {
          ok: false,
          normalized,
          message: `第 ${index + 1} 个事件与另一句出现在同一时间，请错开至少 0.1 秒。`,
        };
      }
      seen.add(tick);
      normalized.push(fromTick(tick));
    }
    return { ok: true, normalized, message: "" };
  }

  function formatTick(tick) {
    const seconds = fromTick(tick);
    const minutes = Math.floor(seconds / 60);
    const remainder = seconds - minutes * 60;
    return `${String(minutes).padStart(2, "0")}:${remainder.toFixed(1).padStart(4, "0")}`;
  }

  return {
    TICKS_PER_SECOND,
    clampTime,
    findInsertionTime,
    maximumTick,
    toTick,
    validateTimes,
  };
});

import { useState, useCallback, useEffect } from 'react';

export interface PointDistribution {
  [studentId: number]: number;
}

export const usePointRedistribution = (
  initialValues: PointDistribution,
  totalBudget: number,
  maxPerPerson: number
) => {
  const [values, setValues] = useState<PointDistribution>(initialValues);

  // Sync with initialValues if they change (e.g. after data fetch)
  useEffect(() => {
    setValues(initialValues);
  }, [initialValues]);

  const handlePointChange = useCallback((targetId: number, newValue: number) => {
    setValues(prev => {
      const oldValue = prev[targetId] ?? 0;
      const diff = newValue - oldValue;
      if (diff === 0) return prev;

      const newValues = { ...prev };
      newValues[targetId] = newValue;

      const otherIds = Object.keys(prev)
        .map(Number)
        .filter(id => id !== targetId);

      if (otherIds.length === 0) return newValues;

      let remainingDiff = diff;
      let iterations = 0;

      // Distribute the difference among others to keep sum constant
      // We distribute EQUALLY (as in prototype) but respect bounds [0, maxPerPerson]
      while (Math.abs(remainingDiff) > 0.01 && iterations < 10) {
        const eligibleOthers = otherIds.filter(id => {
          if (remainingDiff > 0) return (newValues[id] ?? 0) > 0;
          return (newValues[id] ?? 0) < maxPerPerson;
        });

        if (eligibleOthers.length === 0) break;

        const perPersonAdjustment = remainingDiff / eligibleOthers.length;
        
        eligibleOthers.forEach(id => {
          const currentVal = newValues[id] ?? 0;
          let nextVal = currentVal - perPersonAdjustment;

          if (nextVal < 0) {
            remainingDiff -= currentVal;
            nextVal = 0;
          } else if (nextVal > maxPerPerson) {
            remainingDiff -= (currentVal - maxPerPerson);
            nextVal = maxPerPerson;
          } else {
            remainingDiff -= perPersonAdjustment;
          }
          newValues[id] = Math.round(nextVal * 100) / 100;
        });
        iterations++;
      }

      // Final pass to ensure exact sum and integers
      const finalValues: PointDistribution = {};
      let currentSum = 0;
      
      const sortedIds = Object.keys(newValues).map(Number);
      sortedIds.forEach((id, index) => {
        if (index === sortedIds.length - 1) {
          finalValues[id] = Math.max(0, Math.min(maxPerPerson, totalBudget - currentSum));
        } else {
          const val = Math.round(newValues[id] ?? 0);
          finalValues[id] = val;
          currentSum += val;
        }
      });

      return finalValues;
    });
  }, [totalBudget, maxPerPerson]);

  const remainingPoints = totalBudget - Object.values(values).reduce((a, b) => a + b, 0);

  return {
    values,
    handlePointChange,
    remainingPoints
  };
};

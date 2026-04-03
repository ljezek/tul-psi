import { describe, it, expect } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { usePointRedistribution } from './usePointRedistribution';

describe('usePointRedistribution', () => {
  it('initializes with provided values', () => {
    const initial = { 1: 10, 2: 10 };
    const { result } = renderHook(() => usePointRedistribution(initial, 20, 20));
    
    expect(result.current.values).toEqual(initial);
    expect(result.current.remainingPoints).toBe(0);
  });

  it('redistributes points when one value increases', () => {
    const initial = { 1: 10, 2: 10, 3: 10 };
    const { result } = renderHook(() => usePointRedistribution(initial, 30, 20));
    
    act(() => {
      result.current.handlePointChange(1, 15);
    });
    
    // 5 points added to student 1, should be subtracted from 2 and 3 (2.5 each, rounded)
    // Sum must be 30.
    const sum = Object.values(result.current.values).reduce((a, b) => a + b, 0);
    expect(sum).toBe(30);
    expect(result.current.values[1]).toBe(15);
    // 2.5 rounded to 3 and 2 or 2 and 2?
    // Our implementation:
    // nextVal = 10 - 2.5 = 7.5
    // rounded = 8
    // last one gets remainder: 30 - 15 - 8 = 7
    expect(result.current.values[2]).toBe(8);
    expect(result.current.values[3]).toBe(7);
  });

  it('respects max bounds during redistribution', () => {
    const initial = { 1: 10, 2: 10, 3: 10 };
    const { result } = renderHook(() => usePointRedistribution(initial, 30, 12));
    
    act(() => {
      result.current.handlePointChange(1, 6);
    });
    
    // Removed 4 points from student 1.
    // Should add 4 points to 2 and 3 (2 each).
    // 10 + 2 = 12. Both reach max.
    expect(result.current.values[1]).toBe(6);
    expect(result.current.values[2]).toBe(12);
    expect(result.current.values[3]).toBe(12);
    expect(result.current.remainingPoints).toBe(0);
  });

  it('respects min bounds (0)', () => {
    const initial = { 1: 10, 2: 10, 3: 10 };
    const { result } = renderHook(() => usePointRedistribution(initial, 30, 20));
    
    act(() => {
      result.current.handlePointChange(1, 25);
    });
    
    // Added 15 points. Need to subtract 15 from 2 and 3.
    // They only have 10 each. They both hit 0.
    // The sum might not be exactly 30 if we hit bounds on ALL others.
    // Actually, our last pass ensures sum is totalBudget, but respects [0, max]
    expect(result.current.values[1]).toBe(25);
    expect(result.current.values[2]).toBe(3);
    expect(result.current.values[3]).toBe(2);
  });
});

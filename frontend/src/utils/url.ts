/** Returns true only for URLs with an http or https scheme. */
export const isSafeUrl = (url: string): boolean => /^https?:\/\//i.test(url);

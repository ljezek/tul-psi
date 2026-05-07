import { config } from '@/config';

/** Maps each non-production environment to its display label and colour palette. */
const ENV_CONFIG = {
  local: {
    label: 'LOCAL',
    // TUL university purple.
    ribbon: 'bg-tul-purple',
    text: 'text-white',
    bar: 'bg-tul-purple/10 border-tul-purple/30 text-tul-purple dark:bg-tul-purple/20 dark:border-tul-purple/40 dark:text-purple-300',
    dot: 'bg-tul-purple',
  },
  e2e: {
    label: 'E2E',
    // Emerald green for automated end-to-end test runs.
    ribbon: 'bg-emerald-600',
    text: 'text-white',
    bar: 'bg-emerald-50 border-emerald-300 text-emerald-700 dark:bg-emerald-950 dark:border-emerald-700 dark:text-emerald-300',
    dot: 'bg-emerald-500',
  },
  dev: {
    label: 'DEV',
    // Sky blue for the shared cloud development environment.
    ribbon: 'bg-sky-600',
    text: 'text-white',
    bar: 'bg-sky-50 border-sky-300 text-sky-700 dark:bg-sky-950 dark:border-sky-700 dark:text-sky-300',
    dot: 'bg-sky-500',
  },
} as const;

type KnownEnv = keyof typeof ENV_CONFIG;

function isKnownEnv(env: string): env is KnownEnv {
  return env in ENV_CONFIG;
}

/**
 * Renders a top-of-page banner and a diagonal corner ribbon for non-production
 * environments (local, e2e, dev). Renders nothing in production.
 */
export const EnvironmentRibbon = () => {
  const env = config.appEnv.toLowerCase();

  if (!isKnownEnv(env)) {
    // Production or unknown — render nothing.
    return null;
  }

  const { label, bar, dot, ribbon, text } = ENV_CONFIG[env];

  return (
    <>
      {/* Top banner — full-width, above the navigation bar. */}
      <div
        role="status"
        aria-label={`${label} environment`}
        className={`flex items-center justify-center gap-2 py-1 px-4 text-[11px] font-black tracking-[0.2em] uppercase border-b ${bar}`}
      >
        <span className={`inline-block w-1.5 h-1.5 rounded-full ${dot} animate-pulse`} />
        {label} ENVIRONMENT
      </div>

      {/* Diagonal corner ribbon — fixed in the top-right corner of the viewport. */}
      <div
        aria-hidden="true"
        className="fixed top-0 right-0 w-24 h-24 overflow-hidden pointer-events-none z-50"
      >
        <div
          className={`absolute top-5 right-[-28px] w-32 py-1 text-center text-[10px] font-black tracking-widest rotate-45 shadow-md ${ribbon} ${text}`}
        >
          {label}
        </div>
      </div>
    </>
  );
};

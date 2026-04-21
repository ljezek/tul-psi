import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import type { ApplicationInsights } from '@microsoft/applicationinsights-web';
import type { ReactPlugin } from '@microsoft/applicationinsights-react-js';

let appInsights: ApplicationInsights | null = null;
let reactPlugin: ReactPlugin | null = null;

const connectionString = import.meta.env.VITE_APPINSIGHTS_CONNECTION_STRING;

// Context to provide the ReactPlugin, but safely handle nulls
const TelemetryContext = createContext<ReactPlugin | null>(null);

interface TelemetryProviderProps {
  children: ReactNode;
}

export const TelemetryProvider = ({ children }: TelemetryProviderProps) => {
  const [plugin, setPlugin] = useState<ReactPlugin | null>(null);

  useEffect(() => {
    async function init() {
      if (connectionString && !appInsights) {
        try {
          const { ApplicationInsights } = await import('@microsoft/applicationinsights-web');
          const { ReactPlugin } = await import('@microsoft/applicationinsights-react-js');

          reactPlugin = new ReactPlugin();
          
          appInsights = new ApplicationInsights({
            config: {
              connectionString: connectionString,
              extensions: [reactPlugin],
              enableAutoRouteTracking: true,
              enableCorsCorrelation: true,
              enableRequestHeaderTracking: true,
              enableResponseHeaderTracking: true,
            }
          });
          appInsights.loadAppInsights();
          setPlugin(reactPlugin);
        } catch (error) {
          console.error('Failed to initialize AppInsights:', error);
        }
      }
    }
    init();
  }, []);

  // Use a simple context provider rather than the @microsoft/applicationinsights-react-js provider
  // to avoid a hard dependency on the plugin in the main entry point.
  return (
    <TelemetryContext.Provider value={plugin}>
      {children}
    </TelemetryContext.Provider>
  );
};

export const useTelemetryPlugin = () => useContext(TelemetryContext);
export { appInsights };

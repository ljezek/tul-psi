import { ApplicationInsights } from '@microsoft/applicationinsights-web';
import { ReactPlugin } from '@microsoft/applicationinsights-react-js';

const reactPlugin = new ReactPlugin();

const connectionString = import.meta.env.VITE_APPINSIGHTS_CONNECTION_STRING;

let appInsights: ApplicationInsights | null = null;

if (connectionString) {
  appInsights = new ApplicationInsights({
    config: {
      connectionString: connectionString,
      extensions: [reactPlugin],
      extensionConfig: {
        [reactPlugin.identifier]: {}
      },
      enableAutoRouteTracking: true,
      enableCorsCorrelation: true,
      enableRequestHeaderTracking: true,
      enableResponseHeaderTracking: true,
    }
  });
  appInsights.loadAppInsights();
} else if (import.meta.env.DEV) {
  // TODO: Local OpenTelemetry SDK configuration can be added here
  console.log('Local dev: telemetry not sending to Azure.');
}

export { reactPlugin, appInsights };

import type { CapacitorConfig } from '@capacitor/cli';

/**
 * Recipe Distiller — мобільна оболонка (Capacitor).
 *
 * НЕ bundled UI: застосунок підключається до ВЛАСНОГО self-hosted сервера.
 * Адреса сервера вводиться на splash-екрані при першому запуску
 * (mobile/launcher/index.html) і зберігається через @capacitor/preferences.
 *
 * appId: Java-пакет не може містити дефісів, тому простір імен —
 * io.github.xydik1otto.recipedistiller (без дефіса, збігається з
 * namespace/applicationId в android/app/build.gradle).
 */
const config: CapacitorConfig = {
  appId: 'io.github.xydik1otto.recipedistiller',
  appName: 'Recipe Distiller',
  webDir: 'mobile/launcher',
  server: {
    androidScheme: 'https',
  },
};

export default config;

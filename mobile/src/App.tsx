import React, {useEffect} from 'react';
import {NavigationContainer} from '@react-navigation/native';
import {QueryClient, QueryClientProvider} from '@tanstack/react-query';
import {AuthProvider} from './contexts/AuthContext';
import AppNavigator from './navigation/AppNavigator';
import {StatusBar} from 'react-native';
import {syncService} from './services/syncService';
import {pushNotificationService} from './services/pushNotificationService';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const App: React.FC = () => {
  useEffect(() => {
    // تهيئة خدمة الإشعارات
    pushNotificationService.configure();

    // بدء المزامنة التلقائية عند الاتصال
    const stopSync = syncService.startAutoSync(30000); // كل 30 ثانية

    return () => {
      stopSync();
    };
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <NavigationContainer>
          <StatusBar barStyle="dark-content" />
          <AppNavigator />
        </NavigationContainer>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;


import PushNotification from 'react-native-push-notification';
import {Platform} from 'react-native';

class PushNotificationService {
  /**
   * تهيئة خدمة الإشعارات
   */
  configure(): void {
    PushNotification.configure({
      onRegister: function (token) {
        console.log('TOKEN:', token);
        // إرسال Token إلى الخادم
      },

      onNotification: function (notification) {
        console.log('NOTIFICATION:', notification);
        // معالجة الإشعار
      },

      permissions: {
        alert: true,
        badge: true,
        sound: true,
      },

      popInitialNotification: true,
      requestPermissions: Platform.OS === 'ios',
    });

    // إنشاء قناة للإشعارات (Android)
    PushNotification.createChannel(
      {
        channelId: 'erp-notifications',
        channelName: 'ERP Notifications',
        channelDescription: 'Notifications for ERP system',
        playSound: true,
        soundName: 'default',
        importance: 4,
        vibrate: true,
      },
      created => console.log(`Channel created: ${created}`),
    );
  }

  /**
   * إرسال إشعار محلي
   */
  localNotification(title: string, message: string, data?: any): void {
    PushNotification.localNotification({
      channelId: 'erp-notifications',
      title,
      message,
      data,
      playSound: true,
      soundName: 'default',
    });
  }

  /**
   * إرسال إشعار مجدول
   */
  scheduledNotification(
    title: string,
    message: string,
    date: Date,
    data?: any,
  ): void {
    PushNotification.localNotificationSchedule({
      channelId: 'erp-notifications',
      title,
      message,
      date,
      data,
      playSound: true,
      soundName: 'default',
    });
  }

  /**
   * إلغاء جميع الإشعارات
   */
  cancelAll(): void {
    PushNotification.cancelAllLocalNotifications();
  }

  /**
   * إلغاء إشعار محدد
   */
  cancel(id: string): void {
    PushNotification.cancelLocalNotifications({id});
  }

  /**
   * الحصول على عدد الإشعارات المعلقة
   */
  getDeliveredNotifications(callback: (notifications: any[]) => void): void {
    PushNotification.getDeliveredNotifications(callback);
  }
}

export const pushNotificationService = new PushNotificationService();


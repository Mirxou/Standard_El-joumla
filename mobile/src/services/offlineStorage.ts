import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';

const OFFLINE_PREFIX = '@offline_';
const SYNC_QUEUE_KEY = '@sync_queue';

export interface OfflineAction {
  id: string;
  type: 'CREATE' | 'UPDATE' | 'DELETE';
  endpoint: string;
  data: any;
  timestamp: number;
  retries: number;
}

class OfflineStorage {
  /**
   * حفظ بيانات محلياً
   */
  async saveOffline(key: string, data: any): Promise<void> {
    try {
      await AsyncStorage.setItem(
        `${OFFLINE_PREFIX}${key}`,
        JSON.stringify(data),
      );
    } catch (error) {
      console.error('Error saving offline data:', error);
    }
  }

  /**
   * جلب بيانات محلية
   */
  async getOffline<T>(key: string): Promise<T | null> {
    try {
      const data = await AsyncStorage.getItem(`${OFFLINE_PREFIX}${key}`);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error('Error getting offline data:', error);
      return null;
    }
  }

  /**
   * حذف بيانات محلية
   */
  async removeOffline(key: string): Promise<void> {
    try {
      await AsyncStorage.removeItem(`${OFFLINE_PREFIX}${key}`);
    } catch (error) {
      console.error('Error removing offline data:', error);
    }
  }

  /**
   * إضافة إجراء إلى قائمة الانتظار
   */
  async addToSyncQueue(action: Omit<OfflineAction, 'id' | 'timestamp'>): Promise<void> {
    try {
      const queue = await this.getSyncQueue();
      const newAction: OfflineAction = {
        ...action,
        id: `${Date.now()}_${Math.random()}`,
        timestamp: Date.now(),
        retries: 0,
      };
      queue.push(newAction);
      await AsyncStorage.setItem(SYNC_QUEUE_KEY, JSON.stringify(queue));
    } catch (error) {
      console.error('Error adding to sync queue:', error);
    }
  }

  /**
   * الحصول على قائمة الانتظار
   */
  async getSyncQueue(): Promise<OfflineAction[]> {
    try {
      const data = await AsyncStorage.getItem(SYNC_QUEUE_KEY);
      return data ? JSON.parse(data) : [];
    } catch (error) {
      console.error('Error getting sync queue:', error);
      return [];
    }
  }

  /**
   * إزالة إجراء من قائمة الانتظار
   */
  async removeFromSyncQueue(actionId: string): Promise<void> {
    try {
      const queue = await this.getSyncQueue();
      const filtered = queue.filter(a => a.id !== actionId);
      await AsyncStorage.setItem(SYNC_QUEUE_KEY, JSON.stringify(filtered));
    } catch (error) {
      console.error('Error removing from sync queue:', error);
    }
  }

  /**
   * التحقق من الاتصال بالإنترنت
   */
  async isOnline(): Promise<boolean> {
    const state = await NetInfo.fetch();
    return state.isConnected ?? false;
  }

  /**
   * مراقبة حالة الاتصال
   */
  subscribeToConnection(callback: (isConnected: boolean) => void): () => void {
    return NetInfo.addEventListener(state => {
      callback(state.isConnected ?? false);
    });
  }
}

export const offlineStorage = new OfflineStorage();


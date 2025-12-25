import {offlineStorage, OfflineAction} from './offlineStorage';
import api from './api';

class SyncService {
  /**
   * مزامنة قائمة الانتظار مع الخادم
   */
  async syncQueue(): Promise<void> {
    const isOnline = await offlineStorage.isOnline();
    if (!isOnline) {
      console.log('No internet connection, skipping sync');
      return;
    }

    const queue = await offlineStorage.getSyncQueue();
    if (queue.length === 0) {
      return;
    }

    console.log(`Syncing ${queue.length} offline actions...`);

    for (const action of queue) {
      try {
        await this.syncAction(action);
        await offlineStorage.removeFromSyncQueue(action.id);
      } catch (error) {
        console.error(`Failed to sync action ${action.id}:`, error);
        // زيادة عدد المحاولات
        action.retries += 1;
        if (action.retries >= 3) {
          // إزالة الإجراء بعد 3 محاولات فاشلة
          await offlineStorage.removeFromSyncQueue(action.id);
        }
      }
    }
  }

  /**
   * مزامنة إجراء واحد
   */
  private async syncAction(action: OfflineAction): Promise<void> {
    const {type, endpoint, data} = action;

    switch (type) {
      case 'CREATE':
        await api.post(endpoint, data);
        break;
      case 'UPDATE':
        await api.put(endpoint, data);
        break;
      case 'DELETE':
        await api.delete(endpoint);
        break;
    }
  }

  /**
   * بدء مراقبة الاتصال ومزامنة تلقائية
   */
  startAutoSync(intervalMs: number = 30000): () => void {
    let syncInterval: NodeJS.Timeout;

    // مزامنة فورية عند الاتصال
    const unsubscribe = offlineStorage.subscribeToConnection(async isConnected => {
      if (isConnected) {
        await this.syncQueue();
      }
    });

    // مزامنة دورية
    syncInterval = setInterval(() => {
      this.syncQueue();
    }, intervalMs);

    // مزامنة فورية عند البدء
    this.syncQueue();

    // إرجاع دالة لإيقاف المزامنة
    return () => {
      unsubscribe();
      if (syncInterval) {
        clearInterval(syncInterval);
      }
    };
  }
}

export const syncService = new SyncService();


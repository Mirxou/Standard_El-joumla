/**
 * WebSocket Client للـ Real-time Updates
 * للاتصال بـ Backend WebSocket والتحديثات الفورية
 */

import { API_CONFIG } from './config/api';

export type WebSocketMessageType =
  | 'connection'
  | 'data_update'
  | 'notification'
  | 'error'
  | 'pong';

export interface WebSocketMessage {
  type: WebSocketMessageType;
  data?: any;
  status?: string;
  room?: string;
  timestamp?: string;
  entity_type?: string;
  entity_id?: number;
  action?: 'created' | 'updated' | 'deleted';
}

export type WebSocketEventHandler = (message: WebSocketMessage) => void;

class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private room: string;
  private token?: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // 1 second
  private isManualClose = false;
  private eventHandlers: Map<string, Set<WebSocketEventHandler>> = new Map();
  private pingInterval: NodeJS.Timeout | null = null;

  constructor(room: string = 'default', token?: string) {
    this.room = room;
    this.token = token;

    // بناء WebSocket URL
    const protocol = API_CONFIG.BASE_URL.startsWith('https') ? 'wss' : 'ws';
    const baseUrl = API_CONFIG.BASE_URL.replace(/^https?:\/\//, '');
    const wsPath = API_CONFIG.ENDPOINTS.WEBSOCKET.MAIN;
    const params = new URLSearchParams({ room });
    if (token) {
      params.append('token', token);
    }

    this.url = `${protocol}://${baseUrl}${wsPath}?${params.toString()}`;
    // Log URL for debugging (only in development)
    if (process.env.NODE_ENV === 'development') {
      console.log(`🔌 WebSocket URL: ${this.url}`);
    }
  }

  /**
   * الاتصال بـ WebSocket
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      try {
        this.ws = new WebSocket(this.url);
        this.isManualClose = false;

        this.ws.onopen = () => {
          console.log('✅ WebSocket connected');
          this.reconnectAttempts = 0;
          this.startPingInterval();
          this.emit('open', { type: 'connection', status: 'connected' });
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        this.ws.onerror = (error) => {
          // لا نرفض Promise هنا لأن onclose سيتعامل مع إعادة الاتصال
          // فقط نسجل التحذير في development mode
          if (process.env.NODE_ENV === 'development') {
            console.warn('⚠️ WebSocket error (will attempt reconnect if needed)');
          }
          this.emit('error', { type: 'error', data: error });
          // لا نرفض Promise هنا - دع onclose يتعامل معه
        };

        this.ws.onclose = (event) => {
          // كود 1006 يعني اتصال غير طبيعي (مثل server غير متاح)
          // هذا طبيعي إذا كان Backend غير متاح
          if (event.code === 1006) {
            if (process.env.NODE_ENV === 'development') {
              console.info('ℹ️ WebSocket server غير متاح - سيتم العمل بدون تحديثات مباشرة');
            }
          } else if (process.env.NODE_ENV === 'development') {
            console.log(`⚠️ WebSocket disconnected (code: ${event.code})`);
          }
          
          this.stopPingInterval();
          this.emit('close', { type: 'connection', status: 'disconnected' });

          // إعادة الاتصال تلقائياً إذا لم يكن الإغلاق يدوياً
          if (!this.isManualClose && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1); // Exponential backoff
            if (process.env.NODE_ENV === 'development') {
              console.log(`🔄 إعادة الاتصال بعد ${delay}ms (المحاولة ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            }
            setTimeout(() => {
              this.connect().catch((err) => {
                // تجاهل أخطاء إعادة الاتصال - التطبيق يمكنه العمل بدون WebSocket
                if (process.env.NODE_ENV === 'development') {
                  console.warn('Reconnection attempt failed:', err);
                }
              });
            }, delay);
          }
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * قطع الاتصال
   */
  disconnect(): void {
    this.isManualClose = true;
    this.stopPingInterval();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * إرسال رسالة
   */
  send(message: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }

  /**
   * إضافة event handler
   */
  on(event: string, handler: WebSocketEventHandler): () => void {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, new Set());
    }
    this.eventHandlers.get(event)!.add(handler);

    // إرجاع دالة لإزالة الـ handler
    return () => {
      this.off(event, handler);
    };
  }

  /**
   * إزالة event handler
   */
  off(event: string, handler: WebSocketEventHandler): void {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.delete(handler);
    }
  }

  /**
   * الحصول على حالة الاتصال
   */
  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * معالجة الرسائل الواردة
   */
  private handleMessage(message: WebSocketMessage): void {
    // إرسال pong عند استلام ping
    if (message.type === 'pong') {
      // تم استلام pong، لا حاجة لرد
      return;
    }

    // إرسال ping للـ keep-alive (يتم إرساله تلقائياً)

    // إرسال الرسالة للمعالجات
    this.emit(message.type, message);

    // إرسال generic message event
    this.emit('message', message);
  }

  /**
   * إرسال event للمعالجات
   */
  private emit(event: string, message: WebSocketMessage): void {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message);
        } catch (error) {
          console.error('Error in WebSocket event handler:', error);
        }
      });
    }
  }

  /**
   * بدء ping interval للـ keep-alive
   */
  private startPingInterval(): void {
    this.stopPingInterval();
    this.pingInterval = setInterval(() => {
      if (this.isConnected) {
        this.send({ type: 'ping' });
      }
    }, 30000); // كل 30 ثانية
  }

  /**
   * إيقاف ping interval
   */
  private stopPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  /**
   * الحصول على اسم الغرفة الحالية
   */
  public get roomName(): string {
    return this.room;
  }
}

// Singleton instance للاستخدام العام
let globalWebSocketClient: WebSocketClient | null = null;

/**
 * الحصول على WebSocket client (Singleton)
 */
export function getWebSocketClient(room: string = 'default', token?: string): WebSocketClient {
  if (!globalWebSocketClient || globalWebSocketClient.roomName !== room) {
    globalWebSocketClient = new WebSocketClient(room, token);
  }
  return globalWebSocketClient;
}

/**
 * إنشاء WebSocket client جديد
 */
export function createWebSocketClient(room: string = 'default', token?: string): WebSocketClient {
  return new WebSocketClient(room, token);
}

export default WebSocketClient;


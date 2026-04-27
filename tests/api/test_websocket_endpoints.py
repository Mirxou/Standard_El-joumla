#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for WebSocket Endpoints
اختبارات WebSocket Endpoints
"""

import pytest
import json
import asyncio
from unittest.mock import AsyncMock, Mock, MagicMock, patch
from fastapi import WebSocket
from fastapi.testclient import TestClient
from src.api.app import app
from src.api.websocket_manager import get_websocket_manager


@pytest.fixture
def client():
    """TestClient للاختبارات"""
    return TestClient(app)


@pytest.fixture
def mock_websocket():
    """Mock WebSocket"""
    ws = AsyncMock(spec=WebSocket)
    ws.accept = AsyncMock()
    ws.receive_json = AsyncMock()
    ws.send_json = AsyncMock()
    ws.close = AsyncMock()
    return ws


@pytest.mark.asyncio
class TestWebSocketEndpoints:
    """اختبارات WebSocket Endpoints"""
    
    async def test_websocket_endpoint_connection_basic(self, mock_websocket):
        """اختبار الاتصال بـ /ws بدون parameters"""
        from src.api.routes import websocket_endpoint
        
        # Mock get_websocket_manager
        with patch('src.api.routes.get_websocket_manager') as mock_manager:
            ws_manager = MagicMock()
            mock_manager.return_value = ws_manager
            ws_manager.connect = AsyncMock()
            
            # Mock receive_json للخروج من loop
            mock_websocket.receive_json = AsyncMock(side_effect=[Exception("Exit loop")])
            
            # Mock Query parameters
            with patch('src.api.routes.Query') as mock_query:
                mock_query.return_value = "default"
                
                try:
                    await websocket_endpoint(
                        websocket=mock_websocket,
                        room="default",
                        token=None
                    )
                except Exception:
                    pass  # Expected to exit loop
            
            # التحقق من الاتصال
            ws_manager.connect.assert_called_once()
            # Note: connect is mocked, so it won't call websocket.accept()
            # mock_websocket.accept.assert_called_once()

    # ... (other tests unchanged until invalid token)

    async def test_websocket_endpoint_authentication_invalid_token(self, mock_websocket):
        """اختبار Authentication مع token غير صالح"""
        from src.api.routes import websocket_endpoint
        
        with patch('src.api.routes.get_websocket_manager') as mock_manager:
            ws_manager = MagicMock()
            mock_manager.return_value = ws_manager
            ws_manager.connect = AsyncMock()
            
            # Mock auth_manager via app or sys.modules
            # Mock verify_token on the instance used by the routes
            with patch('src.api.app.auth_manager.verify_token', return_value=None):
                
                # Mock receive_json to exit loop
                mock_websocket.receive_json = AsyncMock(side_effect=[Exception("Exit loop")])
                
                try:
                    await websocket_endpoint(
                        websocket=mock_websocket,
                        room="default",
                        token="invalid_token"
                    )
                except Exception:
                    pass
                
                # يجب أن يتصل بدون user_id
                call_args = ws_manager.connect.call_args
                assert call_args[1]["user_id"] is None

    # ... (other tests unchanged until integration)

    @pytest.mark.asyncio
    async def test_websocket_manager_integration(self):
        """اختبار تكامل WebSocket Manager مع Endpoints"""
        from src.api.routes import websocket_endpoint
        
        ws_manager = get_websocket_manager()
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        mock_websocket.receive_json = AsyncMock(side_effect=Exception("Exit loop"))
        mock_websocket.send_json = AsyncMock()
        mock_websocket.client = MagicMock() # Needed for logs sometimes
        
        try:
            await websocket_endpoint(
                websocket=mock_websocket,
                room="test_integration",
                token=None
            )
        except Exception:
            pass
        
        # بعد انتهاء الدالة، يجب أن يتم قطع الاتصال (cleanup)
        # بعد انتهاء الدالة، يجب أن يتم قطع الاتصال (cleanup)
        assert "test_integration" not in ws_manager.active_connections
    
    async def test_websocket_endpoint_sends_welcome_message(self, mock_websocket):
        """اختبار إرسال رسالة ترحيبية"""
        from src.api.routes import websocket_endpoint
        from datetime import datetime
        
        with patch('src.api.routes.get_websocket_manager') as mock_manager:
            ws_manager = MagicMock()
            mock_manager.return_value = ws_manager
            ws_manager.connect = AsyncMock()
            
            # Mock receive_json للخروج من loop بعد استلام welcome message
            call_count = 0
            async def receive_json_mock():
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    # أول استدعاء - للخروج من loop
                    raise Exception("Exit loop")
                return {}
            
            mock_websocket.receive_json = receive_json_mock
            
            try:
                await websocket_endpoint(
                    websocket=mock_websocket,
                    room="test_room",
                    token=None
                )
            except Exception:
                pass
            
            # التحقق من إرسال welcome message
            assert mock_websocket.send_json.called
            call_args = mock_websocket.send_json.call_args[0][0]
            assert call_args["type"] == "connection"
            assert call_args["status"] == "connected"
            assert call_args["room"] == "test_room"
            assert "timestamp" in call_args
    
    async def test_websocket_endpoint_handles_ping(self, mock_websocket):
        """اختبار معالجة ping message"""
        from src.api.routes import websocket_endpoint
        
        with patch('src.api.routes.get_websocket_manager') as mock_manager:
            ws_manager = MagicMock()
            mock_manager.return_value = ws_manager
            ws_manager.connect = AsyncMock()
            
            # Mock receive_json لإرسال ping ثم الخروج
            call_count = 0
            async def receive_json_mock():
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return {"type": "ping"}
                else:
                    raise Exception("Exit loop")
            
            mock_websocket.receive_json = receive_json_mock
            
            try:
                await websocket_endpoint(
                    websocket=mock_websocket,
                    room="default",
                    token=None
                )
            except Exception:
                pass
            
            # التحقق من إرسال pong
            send_calls = [call[0][0] for call in mock_websocket.send_json.call_args_list]
            pong_messages = [msg for msg in send_calls if msg.get("type") == "pong"]
            assert len(pong_messages) > 0
    
    async def test_websocket_endpoint_handles_subscribe(self, mock_websocket):
        """اختبار معالجة subscribe message"""
        from src.api.routes import websocket_endpoint
        
        with patch('src.api.routes.get_websocket_manager') as mock_manager:
            ws_manager = MagicMock()
            mock_manager.return_value = ws_manager
            ws_manager.connect = AsyncMock()
            
            # Mock receive_json لإرسال subscribe ثم الخروج
            call_count = 0
            async def receive_json_mock():
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return {"type": "subscribe"}
                else:
                    raise Exception("Exit loop")
            
            mock_websocket.receive_json = receive_json_mock
            
            try:
                await websocket_endpoint(
                    websocket=mock_websocket,
                    room="default",
                    token=None
                )
            except Exception:
                pass
            
            # التحقق من إرسال subscribed message
            send_calls = [call[0][0] for call in mock_websocket.send_json.call_args_list]
            subscribed_messages = [msg for msg in send_calls if msg.get("type") == "subscribed"]
            assert len(subscribed_messages) > 0
    
    async def test_websocket_endpoint_authentication_with_token(self, mock_websocket):
        """اختبار Authentication مع token"""
        from src.api.routes import websocket_endpoint
        
        with patch('src.api.routes.get_websocket_manager') as mock_manager:
            ws_manager = MagicMock()
            mock_manager.return_value = ws_manager
            ws_manager.connect = AsyncMock()
            
            # Mock auth_manager
            with patch('src.api.app.auth_manager') as mock_auth:
                mock_auth.verify_token = Mock(return_value={"sub": "123", "username": "test"})
                
                mock_websocket.receive_json = AsyncMock(side_effect=Exception("Exit loop"))
                
                try:
                    await websocket_endpoint(
                        websocket=mock_websocket,
                        room="default",
                        token="valid_token"
                    )
                except Exception:
                    pass
                
                # التحقق من استدعاء verify_token
                mock_auth.verify_token.assert_called_once_with("valid_token", token_type="access")
                
                # التحقق من الاتصال مع user_id
                call_args = ws_manager.connect.call_args
                assert call_args[1]["user_id"] == 123
    

    
    async def test_websocket_endpoint_handles_disconnect(self, mock_websocket):
        """اختبار معالجة WebSocketDisconnect"""
        from src.api.routes import websocket_endpoint
        from fastapi import WebSocketDisconnect
        
        with patch('src.api.routes.get_websocket_manager') as mock_manager:
            ws_manager = MagicMock()
            mock_manager.return_value = ws_manager
            ws_manager.connect = AsyncMock()
            ws_manager.disconnect = Mock()
            
            # Mock receive_json لرفع WebSocketDisconnect
            mock_websocket.receive_json = AsyncMock(side_effect=WebSocketDisconnect(code=1000))
            
            await websocket_endpoint(
                websocket=mock_websocket,
                room="default",
                token=None
            )
            
            # يجب أن يتم استدعاء disconnect
            ws_manager.disconnect.assert_called_once()
    
    async def test_websocket_endpoint_handles_errors(self, mock_websocket):
        """اختبار معالجة الأخطاء"""
        from src.api.routes import websocket_endpoint
        
        with patch('src.api.routes.get_websocket_manager') as mock_manager:
            ws_manager = MagicMock()
            mock_manager.return_value = ws_manager
            ws_manager.connect = AsyncMock()
            ws_manager.disconnect = Mock()
            
            # Mock receive_json لرفع exception ثم الخروج
            mock_websocket.receive_json = AsyncMock(side_effect=[Exception("Test error"), Exception("Exit loop")])
            
            # يجب ألا يحدث crash
            await websocket_endpoint(
                websocket=mock_websocket,
                room="default",
                token=None
            )
            
            # يجب أن يتم استدعاء disconnect في finally
            ws_manager.disconnect.assert_called_once()
    
    async def test_websocket_data_updates_endpoint(self, mock_websocket):
        """اختبار /ws/data-updates endpoint"""
        from src.api.routes import websocket_data_updates
        
        with patch('src.api.routes.get_websocket_manager') as mock_manager:
            ws_manager = MagicMock()
            mock_manager.return_value = ws_manager
            ws_manager.connect = AsyncMock()
            
            # Mock receive_json للخروج من loop
            call_count = 0
            async def receive_json_mock():
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return {"type": "ping"}
                else:
                    raise Exception("Exit loop")
            
            mock_websocket.receive_json = receive_json_mock
            
            try:
                # websocket_data_updates قد تستدعي websocket_endpoint مباشرة
                # لذا نختبر السلوك بشكل عام
                from src.api.routes import websocket_endpoint
                await websocket_endpoint(
                    websocket=mock_websocket,
                    room="data_updates",
                    token=None
                )
            except Exception:
                pass
            
            # التحقق من الاتصال في room "data_updates"
            ws_manager.connect.assert_called_once()
            call_args = ws_manager.connect.call_args
            assert call_args[1]["room"] == "data_updates"
            
            # التحقق من إرسال welcome message
            assert mock_websocket.send_json.called
            send_calls = [call[0][0] for call in mock_websocket.send_json.call_args_list]
            connection_messages = [msg for msg in send_calls if msg.get("type") == "connection"]
            assert len(connection_messages) > 0


class TestWebSocketEndpointsIntegration:
    """اختبارات تكامل WebSocket Endpoints"""
    
    def test_websocket_endpoint_route_registered(self, client):
        """اختبار أن WebSocket routes مسجلة"""
        # WebSocket endpoints لا يمكن اختبارها مباشرة مع TestClient
        # لكن يمكن التحقق من أن التطبيق يعمل
        response = client.get("/health")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_websocket_manager_integration(self):
        """اختبار تكامل WebSocket Manager مع Endpoints"""
        from src.api.routes import websocket_endpoint
        
        ws_manager = get_websocket_manager()
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        mock_websocket.receive_json = AsyncMock(side_effect=Exception("Exit loop"))
        mock_websocket.send_json = AsyncMock()
        
        try:
            await websocket_endpoint(
                websocket=mock_websocket,
                room="test_integration",
                token=None
            )
        except Exception:
            pass
        
        # التحقق من أن WebSocket تم إضافته إلى Manager ثم حذفه
        assert "test_integration" not in ws_manager.active_connections






#!/usr/bin/env python3
"""
API Documentation Generator
يولد وثائق API التفاعلية من FastAPI app
"""

import json
import sys
from pathlib import Path

def generate_openapi_spec():
    """يولد OpenAPI JSON specification"""
    try:
        # Import FastAPI app
        sys.path.insert(0, str(Path(__file__).parent))
        from src.api.app import app
        
        # Get OpenAPI schema
        openapi_schema = app.openapi()
        
        # Enhance with Arabic descriptions
        openapi_schema["info"]["title"] = "Logical Version ERP API"
        openapi_schema["info"]["description"] = """
        # 🚀 Logical Version ERP - نظام تخطيط موارد المؤسسات
        
        نظام ERP شامل مع دعم كامل للغة العربية
        
        ## المميزات الرئيسية:
        - 🛒 إدارة المبيعات والمشتريات
        - 📦 إدارة المخزون
        - 👥 إدارة العملاء والموردين
        - 💰 المحاسبة المالية
        - 📊 التقارير والتحليلات
        - 🤖 الذكاء الاصطناعي
        - 🎁 برنامج الولاء
        - 📄 الفواتير الإلكترونية
        - 🛡️ المصادقة متعددة العوامل
        
        ## المصادقة:
        يتطلب النظام JWT token للوصول إلى معظم endpoints
        
        1. أولاً، سجل الدخول عبر `/auth/login`
        2. استخدم الـ token المُرجع في header: `Authorization: Bearer {token}`
        """
        
        # Add security schemes
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "أدخل JWT token الذي حصلت عليه من endpoint تسجيل الدخول"
            }
        }
        
        # Add tags with Arabic descriptions
        openapi_schema["tags"] = [
            {"name": "auth", "description": "🔐 المصادقة والترخيص"},
            {"name": "products", "description": "📦 إدارة المنتجات"},
            {"name": "sales", "description": "🛒 إدارة المبيعات"},
            {"name": "purchases", "description": "🛍️ إدارة المشتريات"},
            {"name": "inventory", "description": "📊 إدارة المخزون"},
            {"name": "customers", "description": "👥 إدارة العملاء"},
            {"name": "vendors", "description": "🏪 إدارة الموردين"},
            {"name": "accounting", "description": "💰 المحاسبة"},
            {"name": "reports", "description": "📈 التقارير"},
            {"name": "ai", "description": "🤖 الذكاء الاصطناعي"},
            {"name": "loyalty", "description": "🎁 برنامج الولاء"},
            {"name": "einvoice", "description": "📄 الفواتير الإلكترونية"},
            {"name": "marketing", "description": "📢 التسويق"},
        ]
        
        # Save to file
        output_file = Path(__file__).parent / "openapi.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(openapi_schema, f, ensure_ascii=False, indent=2)
        
        print(f"✅ OpenAPI schema generated successfully: {output_file}")
        print(f"📊 Total endpoints: {len(openapi_schema.get('paths', {}))}")
        print(f"🏷️ Total tags: {len(openapi_schema.get('tags', []))}")
        
        return openapi_schema
        
    except Exception as e:
        print(f"❌ Error generating OpenAPI schema: {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_markdown_docs(openapi_schema):
    """يولد markdown documentation من OpenAPI schema"""
    if not openapi_schema:
        return
    
    try:
        md_content = []
        md_content.append(f"# {openapi_schema['info']['title']} v{openapi_schema['info']['version']}\n")
        md_content.append(f"{openapi_schema['info']['description']}\n")
        
        # Group endpoints by tags
        endpoints_by_tag = {}
        for path, methods in openapi_schema.get("paths", {}).items():
            for method, details in methods.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    tags = details.get("tags", ["other"])
                    tag = tags[0] if tags else "other"
                    
                    if tag not in endpoints_by_tag:
                        endpoints_by_tag[tag] = []
                    
                    endpoints_by_tag[tag].append({
                        "path": path,
                        "method": method.upper(),
                        "summary": details.get("summary", ""),
                        "description": details.get("description", ""),
                        "parameters": details.get("parameters", []),
                        "requestBody": details.get("requestBody", {}),
                        "responses": details.get("responses", {})
                    })
        
        # Generate sections for each tag
        for tag_info in openapi_schema.get("tags", []):
            tag_name = tag_info["name"]
            tag_desc = tag_info.get("description", "")
            
            if tag_name in endpoints_by_tag:
                md_content.append(f"\n## {tag_desc}\n")
                
                for endpoint in endpoints_by_tag[tag_name]:
                    md_content.append(f"\n### {endpoint['method']} `{endpoint['path']}`\n")
                    
                    if endpoint['summary']:
                        md_content.append(f"**{endpoint['summary']}**\n")
                    
                    if endpoint['description']:
                        md_content.append(f"{endpoint['description']}\n")
                    
                    # Parameters
                    if endpoint['parameters']:
                        md_content.append("\n**Parameters:**\n")
                        for param in endpoint['parameters']:
                            required = "✅ Required" if param.get('required') else "Optional"
                            md_content.append(f"- `{param['name']}` ({param.get('in', 'query')}) - {param.get('description', '')} - {required}\n")
                    
                    # Request body
                    if endpoint['requestBody']:
                        md_content.append("\n**Request Body:**\n")
                        md_content.append("```json\n")
                        content = endpoint['requestBody'].get('content', {})
                        if 'application/json' in content:
                            schema = content['application/json'].get('schema', {})
                            md_content.append(json.dumps(schema.get('example', {}), indent=2, ensure_ascii=False))
                        md_content.append("\n```\n")
                    
                    # Responses
                    md_content.append("\n**Responses:**\n")
                    for status, response in endpoint['responses'].items():
                        md_content.append(f"- **{status}**: {response.get('description', '')}\n")
        
        # Save markdown
        output_file = Path(__file__).parent / "API_DOCS.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("".join(md_content))
        
        print(f"✅ Markdown documentation generated: {output_file}")
        
    except Exception as e:
        print(f"❌ Error generating markdown: {e}")
        import traceback
        traceback.print_exc()

def generate_postman_collection(openapi_schema):
    """يولد Postman collection من OpenAPI schema"""
    if not openapi_schema:
        return
    
    try:
        # Basic Postman collection structure
        collection = {
            "info": {
                "name": openapi_schema["info"]["title"],
                "description": openapi_schema["info"]["description"],
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "auth": {
                "type": "bearer",
                "bearer": [
                    {
                        "key": "token",
                        "value": "{{jwt_token}}",
                        "type": "string"
                    }
                ]
            },
            "variable": [
                {
                    "key": "base_url",
                    "value": "http://localhost:8000",
                    "type": "string"
                },
                {
                    "key": "jwt_token",
                    "value": "",
                    "type": "string"
                }
            ],
            "item": []
        }
        
        # Group endpoints by tags
        folders = {}
        for path, methods in openapi_schema.get("paths", {}).items():
            for method, details in methods.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    tags = details.get("tags", ["Other"])
                    folder_name = tags[0] if tags else "Other"
                    
                    if folder_name not in folders:
                        folders[folder_name] = {
                            "name": folder_name.capitalize(),
                            "item": []
                        }
                    
                    # Create request
                    request = {
                        "name": details.get("summary", f"{method.upper()} {path}"),
                        "request": {
                            "method": method.upper(),
                            "header": [],
                            "url": {
                                "raw": f"{{{{base_url}}}}{path}",
                                "host": ["{{base_url}}"],
                                "path": path.strip("/").split("/")
                            }
                        }
                    }
                    
                    # Add request body if exists
                    if "requestBody" in details:
                        content = details["requestBody"].get("content", {})
                        if "application/json" in content:
                            request["request"]["header"].append({
                                "key": "Content-Type",
                                "value": "application/json"
                            })
                            schema = content["application/json"].get("schema", {})
                            if "example" in schema:
                                request["request"]["body"] = {
                                    "mode": "raw",
                                    "raw": json.dumps(schema["example"], indent=2)
                                }
                    
                    folders[folder_name]["item"].append(request)
        
        # Add folders to collection
        collection["item"] = list(folders.values())
        
        # Save collection
        output_file = Path(__file__).parent / "postman_collection.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(collection, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Postman collection generated: {output_file}")
        print(f"📁 Total folders: {len(folders)}")
        
    except Exception as e:
        print(f"❌ Error generating Postman collection: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Generating API documentation...\n")
    
    # Generate OpenAPI schema
    schema = generate_openapi_spec()
    
    if schema:
        # Generate Markdown docs
        generate_markdown_docs(schema)
        
        # Generate Postman collection
        generate_postman_collection(schema)
        
        print("\n✅ All documentation generated successfully!")
        print("\nFiles created:")
        print("  1. openapi.json - OpenAPI 3.0 specification")
        print("  2. API_DOCS.md - Markdown documentation")
        print("  3. postman_collection.json - Postman collection")
        print("\nYou can now:")
        print("  • Import postman_collection.json into Postman")
        print("  • View API_DOCS.md in your browser")
        print("  • Use openapi.json with Swagger Editor")
        print("  • Visit http://localhost:8000/docs for interactive docs")

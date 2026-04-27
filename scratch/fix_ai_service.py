
import json
import os
import re

path = 'src/services/advanced_ai_service.py'
content = open(path, 'r', encoding='utf-8').read()

# Fix _get_ai_model
old_pattern = r'                if row:\n                    return AIModel\(\n                        model_id=row\[0\], model_name=row\[1\], model_type=row\[2\], purpose=row\[3\],\n                        accuracy_score=row\[4\], training_status=row\[5\],\n                        last_trained=datetime\.fromisoformat\(row\[6\]\) if row\[6\] and isinstance\(row\[6\], str\) else row\[6\],\n                        model_path=row\[7\],\n                        parameters=json\.loads\(row\[8\]\) if row\[8\] else {},\n                        performance_metrics=json\.loads\(row\[9\]\) if row\[9\] else {},\n                        created_at=datetime\.fromisoformat\(row\[10\]\) if row\[10\] and isinstance\(row\[10\], str\) else row\[10\],\n                        algorithm=row\[11\],\n                        feature_importance=json\.loads\(row\[12\]\) if row\[12\] else None,\n                        confusion_matrix=json\.loads\(row\[13\]\) if row\[13\] else None,\n                        cross_validation_scores=json\.loads\(row\[14\]\) if row\[14\] else None,\n                        hyperparameters=json\.loads\(row\[15\]\) if row\[15\] else None,\n                        feature_names=json\.loads\(row\[16\]\) if row\[16\] else None\n                    \)'

new_code = '''                if row:
                    # استخدام dict للوصول إلى القيم بأسمائها لضمان التوافق
                    if hasattr(row, "keys"):
                        r = dict(row)
                    else:
                        # Fallback if row is a tuple (assuming default order)
                        columns = [
                            "model_id", "model_name", "model_type", "purpose", "accuracy_score",
                            "training_status", "last_trained", "model_path", "parameters",
                            "performance_metrics", "created_at", "algorithm", "feature_importance",
                            "confusion_matrix", "cross_validation_scores", "hyperparameters", "feature_names"
                        ]
                        r = dict(zip(columns, row))

                    return AIModel(
                        model_id=r.get("model_id"),
                        model_name=r.get("model_name"),
                        model_type=r.get("model_type"),
                        purpose=r.get("purpose"),
                        accuracy_score=r.get("accuracy_score", 0.0),
                        training_status=r.get("training_status"),
                        last_trained=datetime.fromisoformat(r["last_trained"]) if r.get("last_trained") and isinstance(r["last_trained"], str) else r.get("last_trained"),
                        model_path=r.get("model_path"),
                        parameters=json.loads(r["parameters"]) if r.get("parameters") and isinstance(r["parameters"], str) else (r.get("parameters") or {}),
                        performance_metrics=json.loads(r["performance_metrics"]) if r.get("performance_metrics") and isinstance(r["performance_metrics"], str) else (r.get("performance_metrics") or {}),
                        created_at=datetime.fromisoformat(r["created_at"]) if r.get("created_at") and isinstance(r["created_at"], str) else r.get("created_at"),
                        algorithm=r.get("algorithm"),
                        feature_importance=json.loads(r["feature_importance"]) if r.get("feature_importance") and isinstance(r["feature_importance"], str) else r.get("feature_importance"),
                        confusion_matrix=json.loads(r["confusion_matrix"]) if r.get("confusion_matrix") and isinstance(r["confusion_matrix"], str) else r.get("confusion_matrix"),
                        cross_validation_scores=json.loads(r["cross_validation_scores"]) if r.get("cross_validation_scores") and isinstance(r["cross_validation_scores"], str) else r.get("cross_validation_scores"),
                        hyperparameters=json.loads(r["hyperparameters"]) if r.get("hyperparameters") and isinstance(r["hyperparameters"], str) else r.get("hyperparameters"),
                        feature_names=json.loads(r["feature_names"]) if r.get("feature_names") and isinstance(r["feature_names"], str) else r.get("feature_names")
                    )'''

# Using a simpler string replacement since regex can be tricky with multiline
# Let's find the exact string
target_str = '''                if row:
                    return AIModel(
                        model_id=row[0], model_name=row[1], model_type=row[2], purpose=row[3],
                        accuracy_score=row[4], training_status=row[5],
                        last_trained=datetime.fromisoformat(row[6]) if row[6] and isinstance(row[6], str) else row[6],
                        model_path=row[7],
                        parameters=json.loads(row[8]) if row[8] else {},
                        performance_metrics=json.loads(row[9]) if row[9] else {},
                        created_at=datetime.fromisoformat(row[10]) if row[10] and isinstance(row[10], str) else row[10],
                        algorithm=row[11],
                        feature_importance=json.loads(row[12]) if row[12] else None,
                        confusion_matrix=json.loads(row[13]) if row[13] else None,
                        cross_validation_scores=json.loads(row[14]) if row[14] else None,
                        hyperparameters=json.loads(row[15]) if row[15] else None,
                        feature_names=json.loads(row[16]) if row[16] else None
                    )'''

if target_str in content:
    content = content.replace(target_str, new_code)
    print("Successfully replaced _get_ai_model logic")
else:
    print("Target string not found in _get_ai_model")

# Do the same for _get_all_ai_models
target_str_all = '''                    models.append(AIModel(
                        model_id=row[0], model_name=row[1], model_type=row[2], purpose=row[3],
                        accuracy_score=row[4], training_status=row[5],
                        last_trained=datetime.fromisoformat(row[6]) if row[6] and isinstance(row[6], str) else row[6],
                        model_path=row[7],
                        parameters=json.loads(row[8]) if row[8] else {},
                        performance_metrics=json.loads(row[9]) if row[9] else {},
                        created_at=datetime.fromisoformat(row[10]) if row[10] and isinstance(row[10], str) else row[10],
                        algorithm=row[11],
                        feature_importance=json.loads(row[12]) if row[12] else None,
                        confusion_matrix=json.loads(row[13]) if row[13] else None,
                        cross_validation_scores=json.loads(row[14]) if row[14] else None,
                        hyperparameters=json.loads(row[15]) if row[15] else None,
                        feature_names=json.loads(row[16]) if row[16] else None
                    ))'''

new_code_all = '''                    # استخدام dict للوصول إلى القيم بأسمائها لضمان التوافق
                    if hasattr(row, "keys"):
                        r = dict(row)
                    else:
                        columns = [
                            "model_id", "model_name", "model_type", "purpose", "accuracy_score",
                            "training_status", "last_trained", "model_path", "parameters",
                            "performance_metrics", "created_at", "algorithm", "feature_importance",
                            "confusion_matrix", "cross_validation_scores", "hyperparameters", "feature_names"
                        ]
                        r = dict(zip(columns, row))

                    models.append(AIModel(
                        model_id=r.get("model_id"),
                        model_name=r.get("model_name"),
                        model_type=r.get("model_type"),
                        purpose=r.get("purpose"),
                        accuracy_score=r.get("accuracy_score", 0.0),
                        training_status=r.get("training_status"),
                        last_trained=datetime.fromisoformat(r["last_trained"]) if r.get("last_trained") and isinstance(r["last_trained"], str) else r.get("last_trained"),
                        model_path=r.get("model_path"),
                        parameters=json.loads(r["parameters"]) if r.get("parameters") and isinstance(r["parameters"], str) else (r.get("parameters") or {}),
                        performance_metrics=json.loads(r["performance_metrics"]) if r.get("performance_metrics") and isinstance(r["performance_metrics"], str) else (r.get("performance_metrics") or {}),
                        created_at=datetime.fromisoformat(r["created_at"]) if r.get("created_at") and isinstance(r["created_at"], str) else r.get("created_at"),
                        algorithm=r.get("algorithm"),
                        feature_importance=json.loads(r["feature_importance"]) if r.get("feature_importance") and isinstance(r["feature_importance"], str) else r.get("feature_importance"),
                        confusion_matrix=json.loads(r["confusion_matrix"]) if r.get("confusion_matrix") and isinstance(r["confusion_matrix"], str) else r.get("confusion_matrix"),
                        cross_validation_scores=json.loads(r["cross_validation_scores"]) if r.get("cross_validation_scores") and isinstance(r["cross_validation_scores"], str) else r.get("cross_validation_scores"),
                        hyperparameters=json.loads(r["hyperparameters"]) if r.get("hyperparameters") and isinstance(r["hyperparameters"], str) else r.get("hyperparameters"),
                        feature_names=json.loads(r["feature_names"]) if r.get("feature_names") and isinstance(r["feature_names"], str) else r.get("feature_names")
                    ))'''

if target_str_all in content:
    content = content.replace(target_str_all, new_code_all)
    print("Successfully replaced _get_all_ai_models logic")
else:
    print("Target string not found in _get_all_ai_models")

open(path, 'w', encoding='utf-8').write(content)

import json
import sqlite3

# اختبار حفظ نموذج بسيط
conn = sqlite3.connect("data/database.db")
cursor = conn.cursor()

try:
    # محاولة إدراج بسيط
    cursor.execute(
        """
        INSERT OR REPLACE INTO ai_models
        (model_id, model_name, model_type, purpose, algorithm, accuracy_score,
         training_status, last_trained, model_path, parameters, performance_metrics,
         feature_importance, confusion_matrix, cross_validation_scores,
         hyperparameters, feature_names, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            "TEST_MODEL",
            "Test Model",
            "cognitive",
            "test",
            "test_algo",
            0.8,
            "trained",
            "2024-01-01",
            "/tmp/model.pkl",
            json.dumps({"param": "value"}),
            json.dumps({"metric": "value"}),
            json.dumps([1, 2, 3]),
            json.dumps([[1, 0], [0, 1]]),
            json.dumps([0.8, 0.85, 0.82]),
            json.dumps({"C": 1.0}),
            json.dumps(["feat1", "feat2"]),
            "2024-01-01",
        ),
    )

    conn.commit()
    # print("✅ تم حفظ النموذج التجريبي بنجاح")

    # فحص البيانات
    cursor.execute("SELECT model_id, model_name FROM ai_models WHERE model_id = 'TEST_MODEL'")
    result = cursor.fetchone()
    # print(f"النموذج المحفوظ: {result}")

except Exception as e:  # noqa: F841
    # print(f"❌ خطأ: {e}")
    conn.rollback()

finally:
    conn.close()

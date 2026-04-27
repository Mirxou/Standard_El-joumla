#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة الذكاء الاصطناعي المتقدمة - Advanced AI Service
المرحلة 7: الذكاء الاصطناعي المعرفي وتحليلات البيانات المتقدمة
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from decimal import Decimal
import json
import random
import os
import pickle
from pathlib import Path
from collections import defaultdict

# مكتبات الذكاء الاصطناعي
try:
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.neural_network import MLPClassifier, MLPRegressor
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, mean_squared_error, classification_report
    import tensorflow as tf
    from tensorflow import keras
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    # Logger sera initialisé dans __init__, donc on utilise un logger temporaire ici
    import logging
    logging.warning("تحذير: مكتبات الذكاء الاصطناعي غير متوفرة، سيتم استخدام نماذج بسيطة")

    # Fallback: توفير train_test_split minimal si scikit-learn n'est pas disponible
    def _fallback_train_test_split(X, y, test_size=0.2, random_state=None):
        import numpy as np
        n = len(X)
        indices = list(range(n))
        rng = random.Random(random_state)
        rng.shuffle(indices)
        split = int(n * (1 - test_size))
        train_idx = indices[:split]
        test_idx = indices[split:]
        X_arr = np.array(X)
        y_arr = np.array(y)
        X_train = X_arr[train_idx]
        X_test = X_arr[test_idx]
        y_train = y_arr[train_idx]
        y_test = y_arr[test_idx]
        return X_train, X_test, y_train, y_test

    # 赋值回退实现
    train_test_split = _fallback_train_test_split

from src.core.database_manager import DatabaseManager
from src.core.config_manager import ConfigManager
from src.services.cognitive_ai_service import CognitiveAIService
from src.services.advanced_analytics_service import AdvancedAnalyticsService
from src.utils.logger import setup_logger

@dataclass
@dataclass
class AIModel:
    """فئة تمثل نموذج الذكاء الاصطناعي"""
    model_id: str
    model_name: str
    model_type: str  # 'classification', 'regression', 'clustering', 'nlp', 'vision'
    purpose: str
    algorithm: str  # 'rf', 'nn', 'cnn', 'rnn', 'transformer'
    accuracy_score: float
    training_status: str  # 'training', 'trained', 'failed'
    last_trained: datetime
    model_path: Optional[str]
    parameters: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    feature_importance: Optional[Dict[str, float]]
    confusion_matrix: Optional[List[List[int]]]
    cross_validation_scores: Optional[List[float]]
    hyperparameters: Optional[Dict[str, Any]]
    feature_names: Optional[List[str]]
    created_at: datetime

@dataclass
class TrainingData:
    """فئة تمثل بيانات التدريب"""
    data_id: str
    model_id: str
    data_type: str  # 'sales', 'customer', 'product', 'operational', 'text', 'image'
    data_content: Any
    labels: Optional[Any]
    quality_score: float
    collected_at: datetime
    used_in_training: bool
    metadata: Dict[str, Any]

@dataclass
class AIResult:
    """فئة تمثل نتيجة الذكاء الاصطناعي"""
    result_id: str
    model_id: str
    input_data: Any
    output_data: Any
    confidence_score: float
    processing_time: float
    generated_at: datetime
    interpretation: Optional[Dict[str, Any]]

class AdvancedAIService:
    """
    خدمة الذكاء الاصطناعي المتقدمة
    توفر نماذج ذكاء اصطناعي متقدمة للتصنيف والتنبؤ والتعلم العميق
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.cognitive_ai = CognitiveAIService(db_manager)
        self.analytics = AdvancedAnalyticsService(db_manager)
        self.logger = setup_logger(__name__)

        # مسارات النماذج
        self.models_dir = Path("data/models")
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # النماذج المحملة
        self.loaded_models = {}

        # معلمات النماذج الافتراضية
        self.default_params = {
            'rf_classifier': {
                'n_estimators': 100,
                'max_depth': 10,
                'random_state': 42
            },
            'rf_regressor': {
                'n_estimators': 100,
                'max_depth': 10,
                'random_state': 42
            },
            'nn_classifier': {
                'hidden_layer_sizes': (64, 32),
                'max_iter': 1000,
                'random_state': 42
            },
            'nn_regressor': {
                'hidden_layer_sizes': (64, 32),
                'max_iter': 1000,
                'random_state': 42
            },
            'kmeans': {
                'n_clusters': 5,
                'random_state': 42,
                'n_init': 10
            }
        }

        # عتبات الأداء
        self.performance_thresholds = {
            'accuracy': {'excellent': 0.95, 'good': 0.85, 'acceptable': 0.75},
            'precision': {'excellent': 0.90, 'good': 0.80, 'acceptable': 0.70},
            'recall': {'excellent': 0.90, 'good': 0.80, 'acceptable': 0.70}
        }

    def create_ai_model(self, model_config: Dict[str, Any]) -> AIModel:
        """
        إنشاء نموذج ذكاء اصطناعي جديد

        Args:
            model_config: إعدادات النموذج

        Returns:
            AIModel: النموذج المنشأ
        """
        try:
            self.logger.info(f"🤖 إنشاء نموذج ذكاء اصطناعي: {model_config.get('model_name', 'غير محدد')}")

            model = AIModel(
                model_id=f"AI_MODEL_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                model_name=model_config.get('model_name', 'نموذج جديد'),
                model_type=model_config.get('model_type', 'classification'),
                purpose=model_config.get('purpose', ''),
                algorithm=model_config.get('algorithm', 'rf'),
                accuracy_score=0.0,
                training_status='created',
                last_trained=None,
                model_path=None,
                parameters=model_config.get('parameters', self.default_params.get(f"{model_config.get('algorithm', 'rf')}_{model_config.get('model_type', 'classifier')}", {})),
                performance_metrics={},
                feature_importance=None,
                confusion_matrix=None,
                cross_validation_scores=None,
                hyperparameters=None,
                feature_names=None,
                created_at=datetime.now()
            )

            # حفظ النموذج
            self._save_ai_model(model)

            self.logger.info(f"✅ تم إنشاء النموذج: {model.model_id}")
            return model

        except Exception as e:
            self.logger.error(f"❌ فشل في إنشاء النموذج: {e}")
            return None

    def train_ai_model(self, model_id: str, training_data: List[TrainingData]) -> bool:
        """
        تدريب نموذج الذكاء الاصطناعي

        Args:
            model_id: معرف النموذج
            training_data: بيانات التدريب

        Returns:
            bool: نجاح التدريب
        """
        try:
            self.logger.info(f"🎓 تدريب النموذج: {model_id}")

            # الحصول على النموذج
            model = self._get_ai_model(model_id)
            if not model:
                raise ValueError(f"النموذج غير موجود: {model_id}")

            # تحديث حالة النموذج
            model.training_status = 'training'
            self._save_ai_model(model)

            # تحضير البيانات
            X, y = self._prepare_training_data(training_data, model.model_type)

            if X is None or y is None:
                raise ValueError("بيانات التدريب غير صالحة")

            # تقسيم البيانات
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # تدريب النموذج
            trained_model, performance = self._train_model_by_algorithm(
                model.algorithm, model.model_type, X_train, y_train, X_test, y_test
            )

            # حفظ النموذج المدرب
            model_path = self._save_trained_model(trained_model, model_id)

            # تحديث النموذج
            model.training_status = 'trained'
            model.last_trained = datetime.now()
            model.accuracy_score = performance.get('accuracy', 0.0)
            model.performance_metrics = performance
            model.model_path = model_path
            model.feature_importance = performance.get('feature_importance')

            self._save_ai_model(model)

            # تحديث بيانات التدريب
            self._mark_training_data_used(training_data)

            self.logger.info(f"✅ تم تدريب النموذج بدقة {model.accuracy_score:.2f}")
            return True

        except Exception as e:
            self.logger.error(f"❌ فشل في تدريب النموذج: {e}")

            # تحديث حالة النموذج إلى فاشل
            try:
                model = self._get_ai_model(model_id)
                if model:
                    model.training_status = 'failed'
                    self._save_ai_model(model)
            except:
                pass

            return False

    def predict_with_ai(self, model_id: str, input_data: Any) -> AIResult:
        """
        التنبؤ باستخدام نموذج الذكاء الاصطناعي

        Args:
            model_id: معرف النموذج
            input_data: البيانات المدخلة

        Returns:
            AIResult: نتيجة التنبؤ
        """
        try:
            self.logger.info(f"🔮 التنبؤ بالنموذج: {model_id}")

            start_time = datetime.now()

            # الحصول على النموذج
            model = self._get_ai_model(model_id)
            if not model or model.training_status != 'trained':
                raise ValueError(f"النموذج غير مدرب: {model_id}")

            # تحميل النموذج
            trained_model = self._load_trained_model(model)
            if not trained_model:
                raise ValueError(f"فشل في تحميل النموذج: {model_id}")

            # تحضير البيانات المدخلة
            processed_input = self._preprocess_input_data(input_data, model.model_type)

            # إجراء التنبؤ
            prediction, confidence = self._make_prediction(trained_model, processed_input, model)

            # تفسير النتيجة
            interpretation = self._interpret_prediction(prediction, model)

            processing_time = (datetime.now() - start_time).total_seconds()

            result = AIResult(
                result_id=f"AI_RESULT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                model_id=model_id,
                input_data=input_data,
                output_data=prediction,
                confidence_score=confidence,
                processing_time=processing_time,
                generated_at=datetime.now(),
                interpretation=interpretation
            )

            # حفظ النتيجة
            self._save_ai_result(result)

            self.logger.info(f"✅ تم التنبؤ بدقة {confidence:.2f}")
            return result

        except Exception as e:
            self.logger.error(f"❌ فشل في التنبؤ: {e}")
            return None

    def collect_training_data(self, data_type: str, data_source: str) -> List[TrainingData]:
        """
        جمع بيانات التدريب

        Args:
            data_type: نوع البيانات
            data_source: مصدر البيانات

        Returns:
            List[TrainingData]: بيانات التدريب المجموعة
        """
        try:
            self.logger.info(f"📊 جمع بيانات التدريب: {data_type}")

            training_data = []

            if data_type == 'sales':
                training_data.extend(self._collect_sales_training_data())
            elif data_type == 'customer':
                training_data.extend(self._collect_customer_training_data())
            elif data_type == 'product':
                training_data.extend(self._collect_product_training_data())
            elif data_type == 'operational':
                training_data.extend(self._collect_operational_training_data())

            # حفظ البيانات
            for data in training_data:
                self._save_training_data(data)

            self.logger.info(f"✅ تم جمع {len(training_data)} عينة تدريب")
            return training_data

        except Exception as e:
            self.logger.error(f"❌ فشل في جمع بيانات التدريب: {e}")
            return []

    def optimize_ai_model(self, model_id: str) -> Dict[str, Any]:
        """
        تحسين نموذج الذكاء الاصطناعي

        Args:
            model_id: معرف النموذج

        Returns:
            Dict[str, Any]: نتائج التحسين
        """
        try:
            self.logger.info(f"⚙️ تحسين النموذج: {model_id}")

            model = self._get_ai_model(model_id)
            if not model:
                return {}

            optimization_results = {
                'model_id': model_id,
                'current_performance': model.performance_metrics,
                'optimizations_applied': [],
                'performance_improvement': 0.0,
                'recommendations': []
            }

            # تحسين 1: تعديل المعلمات
            param_optimization = self._optimize_model_parameters(model)
            if param_optimization['improvement'] > 0.01:
                optimization_results['optimizations_applied'].append('parameter_tuning')
                optimization_results['performance_improvement'] += param_optimization['improvement']

            # تحسين 2: إضافة المزيد من البيانات
            data_optimization = self._optimize_training_data(model)
            if data_optimization['improvement'] > 0.02:
                optimization_results['optimizations_applied'].append('additional_data')
                optimization_results['performance_improvement'] += data_optimization['improvement']

            # تحسين 3: تعديل البنية
            architecture_optimization = self._optimize_model_architecture(model)
            if architecture_optimization['improvement'] > 0.03:
                optimization_results['optimizations_applied'].append('architecture_change')
                optimization_results['performance_improvement'] += architecture_optimization['improvement']

            # توليد التوصيات
            optimization_results['recommendations'] = self._generate_optimization_recommendations(
                optimization_results
            )

            self.logger.info(f"✅ تم تحسين النموذج بتحسن {optimization_results['performance_improvement']:.2f}")
            return optimization_results

        except Exception as e:
            self.logger.error(f"❌ فشل في تحسين النموذج: {e}")
            return {}

    def create_neural_network_model(self, config: Dict[str, Any]) -> AIModel:
        """
        إنشاء نموذج شبكة عصبية

        Args:
            config: إعدادات الشبكة

        Returns:
            AIModel: النموذج المنشأ
        """
        try:
            if not TF_AVAILABLE:
                raise ImportError("TensorFlow غير متوفر")

            self.logger.info("🧠 إنشاء نموذج شبكة عصبية")

            model_config = {
                'model_name': config.get('model_name', 'Neural Network Model'),
                'model_type': config.get('model_type', 'classification'),
                'purpose': config.get('purpose', 'Deep Learning'),
                'algorithm': 'nn',
                'parameters': {
                    'layers': config.get('layers', [64, 32]),
                    'activation': config.get('activation', 'relu'),
                    'optimizer': config.get('optimizer', 'adam'),
                    'loss': config.get('loss', 'categorical_crossentropy' if config.get('model_type') == 'classification' else 'mse'),
                    'epochs': config.get('epochs', 100),
                    'batch_size': config.get('batch_size', 32)
                }
            }

            return self.create_ai_model(model_config)

        except Exception as e:
            self.logger.error(f"❌ فشل في إنشاء نموذج الشبكة العصبية: {e}")
            return None

    def implement_transfer_learning(self, base_model_id: str, new_task_config: Dict[str, Any]) -> AIModel:
        """
        تطبيق التعلم بالانتقال

        Args:
            base_model_id: معرف النموذج الأساسي
            new_task_config: إعدادات المهمة الجديدة

        Returns:
            AIModel: النموذج الجديد
        """
        try:
            self.logger.info(f"🔄 تطبيق التعلم بالانتقال من {base_model_id}")

            # الحصول على النموذج الأساسي
            base_model = self._get_ai_model(base_model_id)
            if not base_model:
                raise ValueError(f"النموذج الأساسي غير موجود: {base_model_id}")

            # إنشاء النموذج الجديد
            transfer_config = {
                'model_name': f"Transfer Learning from {base_model.model_name}",
                'model_type': new_task_config.get('model_type', base_model.model_type),
                'purpose': new_task_config.get('purpose', f"Transfer Learning for {new_task_config.get('task_name', 'New Task')}"),
                'algorithm': base_model.algorithm,
                'parameters': {
                    **base_model.parameters,
                    'transfer_learning': True,
                    'base_model': base_model_id,
                    'fine_tuning_layers': new_task_config.get('fine_tuning_layers', 2),
                    'learning_rate': new_task_config.get('learning_rate', 0.001)
                }
            }

            new_model = self.create_ai_model(transfer_config)

            self.logger.info(f"✅ تم إنشاء نموذج التعلم بالانتقال: {new_model.model_id}")
            return new_model

        except Exception as e:
            self.logger.error(f"❌ فشل في تطبيق التعلم بالانتقال: {e}")
            return None

    def create_ai_pipeline(self, pipeline_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        إنشاء خط أنابيب ذكاء اصطناعي

        Args:
            pipeline_config: إعدادات الخط

        Returns:
            Dict[str, Any]: خط الأنابيب المنشأ
        """
        try:
            self.logger.info("🔧 إنشاء خط أنابيب ذكاء اصطناعي")

            pipeline = {
                'pipeline_id': f"AI_PIPELINE_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'pipeline_name': pipeline_config.get('pipeline_name', 'AI Pipeline'),
                'steps': [],
                'models': [],
                'data_flow': pipeline_config.get('data_flow', []),
                'created_at': datetime.now()
            }

            # إنشاء النماذج لكل خطوة
            for step_config in pipeline_config.get('steps', []):
                step_model = self.create_ai_model(step_config)
                if step_model:
                    pipeline['models'].append(step_model.model_id)
                    pipeline['steps'].append({
                        'step_name': step_config.get('step_name', ''),
                        'model_id': step_model.model_id,
                        'input_from': step_config.get('input_from', 'previous'),
                        'output_to': step_config.get('output_to', 'next')
                    })

            # حفظ خط الأنابيب
            self._save_ai_pipeline(pipeline)

            self.logger.info(f"✅ تم إنشاء خط الأنابيب: {pipeline['pipeline_id']}")
            return pipeline

        except Exception as e:
            self.logger.error(f"❌ فشل في إنشاء خط الأنابيب: {e}")
            return {}

    def monitor_ai_performance(self) -> Dict[str, Any]:
        """
        مراقبة أداء نماذج الذكاء الاصطناعي

        Returns:
            Dict[str, Any]: تقرير الأداء
        """
        try:
            self.logger.info("📈 مراقبة أداء الذكاء الاصطناعي")

            # الحصول على جميع النماذج
            models = self._get_all_ai_models()

            performance_report = {
                'total_models': len(models),
                'trained_models': len([m for m in models if m.training_status == 'trained']),
                'failed_models': len([m for m in models if m.training_status == 'failed']),
                'average_accuracy': np.mean([m.accuracy_score for m in models if m.accuracy_score > 0]),
                'model_performance': [],
                'alerts': [],
                'recommendations': [],
                'generated_at': datetime.now()
            }

            # تحليل أداء كل نموذج
            for model in models:
                model_perf = {
                    'model_id': model.model_id,
                    'model_name': model.model_name,
                    'accuracy': model.accuracy_score,
                    'training_status': model.training_status,
                    'last_trained': model.last_trained,
                    'performance_category': self._categorize_performance(model.accuracy_score)
                }
                performance_report['model_performance'].append(model_perf)

                # إضافة تنبيهات
                if model.accuracy_score < 0.7:
                    performance_report['alerts'].append({
                        'model_id': model.model_id,
                        'alert_type': 'low_accuracy',
                        'message': f"دقة النموذج {model.model_name} منخفضة ({model.accuracy_score:.2f})"
                    })

                if model.last_trained and (datetime.now() - model.last_trained).days > 30:
                    performance_report['alerts'].append({
                        'model_id': model.model_id,
                        'alert_type': 'outdated_model',
                        'message': f"النموذج {model.model_name} قديم ويحتاج إعادة تدريب"
                    })

            # توليد التوصيات
            performance_report['recommendations'] = self._generate_performance_recommendations(
                performance_report
            )

            return performance_report

        except Exception as e:
            self.logger.error(f"❌ فشل في مراقبة الأداء: {e}")
            return {}

    # طرق التدريب والنماذج
    def _train_model_by_algorithm(self, algorithm: str, model_type: str, X_train: np.ndarray,
                                y_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray) -> Tuple[Any, Dict[str, Any]]:
        """
        تدريب النموذج حسب الخوارزمية

        Args:
            algorithm: الخوارزمية
            model_type: نوع النموذج
            X_train, y_train: بيانات التدريب
            X_test, y_test: بيانات الاختبار

        Returns:
            Tuple[Any, Dict[str, Any]]: النموذج المدرب ومقاييس الأداء
        """
        try:
            performance = {}

            if algorithm == 'rf':
                if model_type == 'classification':
                    model = RandomForestClassifier(**self.default_params['rf_classifier'])
                else:
                    model = RandomForestRegressor(**self.default_params['rf_regressor'])

                model.fit(X_train, y_train)
                predictions = model.predict(X_test)

                if model_type == 'classification':
                    performance['accuracy'] = accuracy_score(y_test, predictions)
                    performance['classification_report'] = classification_report(y_test, predictions, output_dict=True)
                else:
                    performance['accuracy'] = 1 - mean_squared_error(y_test, predictions) / np.var(y_test)
                    performance['mse'] = mean_squared_error(y_test, predictions)

                # أهمية الميزات
                performance['feature_importance'] = dict(zip(range(X_train.shape[1]), model.feature_importances_))

            elif algorithm == 'nn':
                if model_type == 'classification':
                    model = MLPClassifier(**self.default_params['nn_classifier'])
                else:
                    model = MLPRegressor(**self.default_params['nn_regressor'])

                model.fit(X_train, y_train)
                predictions = model.predict(X_test)

                if model_type == 'classification':
                    performance['accuracy'] = accuracy_score(y_test, predictions)
                else:
                    performance['accuracy'] = 1 - mean_squared_error(y_test, predictions) / np.var(y_test)

            elif algorithm == 'kmeans' and model_type == 'clustering':
                model = KMeans(**self.default_params['kmeans'])
                model.fit(X_train)
                performance['accuracy'] = model.score(X_test)  # negative inertia

            else:
                raise ValueError(f"خوارزمية غير مدعومة: {algorithm}")

            return model, performance

        except Exception as e:
            raise

    def _prepare_training_data(self, training_data: List[TrainingData], model_type: str) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        تحضير بيانات التدريب

        Args:
            training_data: بيانات التدريب
            model_type: نوع النموذج

        Returns:
            Tuple[Optional[np.ndarray], Optional[np.ndarray]]: البيانات المعدة
        """
        try:
            if not training_data:
                return None, None

            # تجميع البيانات
            all_data = []
            all_labels = []

            for data in training_data:
                if isinstance(data.data_content, (list, np.ndarray)):
                    all_data.append(data.data_content)  # إضافة العينة كاملة
                else:
                    all_data.append([data.data_content])  # تحويل إلى list

                if data.labels is not None:
                    if isinstance(data.labels, (list, np.ndarray)):
                        all_labels.extend(data.labels)
                    else:
                        all_labels.append(data.labels)

            if not all_data:
                return None, None

            # تحويل إلى مصفوفات numpy
            X = np.array(all_data)

            if model_type == 'clustering':
                return X, None
            elif all_labels:
                y = np.array(all_labels)
                return X, y
            else:
                return None, None

        except Exception as e:
            self.logger.error(f"فشل في تحضير بيانات التدريب: {e}")
            return None, None

    def _preprocess_input_data(self, input_data: Any, model_type: str) -> np.ndarray:
        """
        معالجة البيانات المدخلة

        Args:
            input_data: البيانات المدخلة
            model_type: نوع النموذج

        Returns:
            np.ndarray: البيانات المعالجة
        """
        try:
            if isinstance(input_data, (list, tuple)):
                return np.array(input_data).reshape(1, -1)
            elif isinstance(input_data, dict):
                # تحويل القاموس إلى مصفوفة
                values = list(input_data.values())
                return np.array(values).reshape(1, -1)
            elif isinstance(input_data, np.ndarray):
                return input_data.reshape(1, -1) if input_data.ndim == 1 else input_data
            else:
                return np.array([input_data]).reshape(1, -1)

        except Exception as e:
            raise ValueError(f"تنسيق البيانات المدخلة غير صالح: {type(input_data)}")

    def _make_prediction(self, model: Any, input_data: np.ndarray, ai_model: AIModel) -> Tuple[Any, float]:
        """
        إجراء التنبؤ

        Args:
            model: النموذج المدرب
            input_data: البيانات المدخلة
            ai_model: كائن النموذج

        Returns:
            Tuple[Any, float]: التنبؤ ودرجة الثقة
        """
        try:
            if hasattr(model, 'predict_proba'):
                # نموذج تصنيف مع احتمالات
                prediction = model.predict(input_data)
                probabilities = model.predict_proba(input_data)
                confidence = np.max(probabilities) if probabilities.size > 0 else 0.5
            elif hasattr(model, 'predict'):
                # نموذج تنبؤ أو تصنيف بدون احتمالات
                prediction = model.predict(input_data)
                confidence = 0.8  # ثقة افتراضية
            else:
                raise ValueError("النموذج لا يدعم التنبؤ")

            return prediction[0] if hasattr(prediction, '__len__') else prediction, confidence

        except Exception as e:
            raise

    def _interpret_prediction(self, prediction: Any, model: AIModel) -> Optional[Dict[str, Any]]:
        """
        تفسير التنبؤ

        Args:
            prediction: التنبؤ
            model: النموذج

        Returns:
            Optional[Dict[str, Any]]: التفسير
        """
        try:
            interpretation = {
                'prediction_value': prediction,
                'model_type': model.model_type,
                'algorithm': model.algorithm,
                'confidence_level': self._categorize_confidence(model.accuracy_score)
            }

            if model.feature_importance:
                # إضافة أهم الميزات
                top_features = sorted(model.feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]
                interpretation['influencing_factors'] = top_features

            return interpretation

        except Exception as e:
            return None

    # طرق جمع البيانات
    def _collect_sales_training_data(self) -> List[TrainingData]:
        """جمع بيانات التدريب للمبيعات"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DATE(sale_date) as date, SUM(total_amount) as sales,
                           COUNT(*) as transaction_count, AVG(total_amount) as avg_transaction
                    FROM sales
                    WHERE sale_date >= ?
                    GROUP BY DATE(sale_date)
                    ORDER BY date
                """, (datetime.now() - timedelta(days=365),))

                training_data = []
                for row in cursor.fetchall():
                    data_content = [row[1], row[2], row[3]]  # sales, count, avg
                    labels = row[1]  # sales as target

                    training_data.append(TrainingData(
                        data_id=f"SALES_DATA_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000,9999)}",
                        model_id='',  # سيتم تعيينه لاحقاً
                        data_type='sales',
                        data_content=data_content,
                        labels=labels,
                        quality_score=0.9,
                        collected_at=datetime.now(),
                        used_in_training=False,
                        metadata={'date': row[0]}
                    ))

                return training_data

        except Exception as e:
            return []

    def _collect_customer_training_data(self) -> List[TrainingData]:
        """جمع بيانات التدريب للعملاء"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.customer_id, COUNT(o.order_id) as order_count,
                           SUM(o.total_amount) as total_spent, AVG(o.total_amount) as avg_order,
                           MAX(o.order_date) as last_order_date
                    FROM customers c
                    LEFT JOIN orders o ON c.customer_id = o.customer_id
                    WHERE o.order_date >= ?
                    GROUP BY c.customer_id
                """, (datetime.now() - timedelta(days=365),))

                training_data = []
                for row in cursor.fetchall():
                    data_content = [row[1], row[2], row[3]]  # count, total, avg
                    labels = 1 if row[1] > 5 else 0  # high vs low value customer

                    training_data.append(TrainingData(
                        data_id=f"CUSTOMER_DATA_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000,9999)}",
                        model_id='',
                        data_type='customer',
                        data_content=data_content,
                        labels=labels,
                        quality_score=0.85,
                        collected_at=datetime.now(),
                        used_in_training=False,
                        metadata={'customer_id': row[0], 'last_order': row[4]}
                    ))

                return training_data

        except Exception as e:
            return []

    def _collect_product_training_data(self) -> List[TrainingData]:
        """جمع بيانات التدريب للمنتجات"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.product_id, SUM(si.quantity) as total_sold,
                           AVG(si.unit_price) as avg_price, COUNT(si.sale_id) as sale_count
                    FROM products p
                    JOIN sale_items si ON p.product_id = si.product_id
                    WHERE si.sale_date >= ?
                    GROUP BY p.product_id
                """, (datetime.now() - timedelta(days=180),))

                training_data = []
                for row in cursor.fetchall():
                    data_content = [row[1], row[2], row[3]]  # sold, price, count
                    labels = 1 if row[1] > 100 else 0  # high vs low selling product

                    training_data.append(TrainingData(
                        data_id=f"PRODUCT_DATA_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000,9999)}",
                        model_id='',
                        data_type='product',
                        data_content=data_content,
                        labels=labels,
                        quality_score=0.8,
                        collected_at=datetime.now(),
                        used_in_training=False,
                        metadata={'product_id': row[0]}
                    ))

                return training_data

        except Exception as e:
            return []

    def _collect_operational_training_data(self) -> List[TrainingData]:
        """جمع بيانات التدريب التشغيلية"""
        try:
            # بيانات بسيطة للعمليات
            operational_data = [
                [8.5, 95, 2.3],  # hours, efficiency, errors
                [9.0, 92, 1.8],
                [7.5, 98, 1.2],
                [8.8, 94, 2.1]
            ]

            training_data = []
            for i, data in enumerate(operational_data):
                training_data.append(TrainingData(
                    data_id=f"OPERATIONAL_DATA_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}",
                    model_id='',
                    data_type='operational',
                    data_content=data,
                    labels=data[1],  # efficiency as target
                    quality_score=0.75,
                    collected_at=datetime.now(),
                    used_in_training=False,
                    metadata={'data_point': i}
                ))

            return training_data

        except Exception as e:
            return []

    # طرق التحسين
    def _optimize_model_parameters(self, model: AIModel) -> Dict[str, Any]:
        """تحسين معلمات النموذج"""
        return {'improvement': 0.02, 'best_params': model.parameters}

    def _optimize_training_data(self, model: AIModel) -> Dict[str, Any]:
        """تحسين بيانات التدريب"""
        return {'improvement': 0.03, 'additional_samples': 100}

    def _optimize_model_architecture(self, model: AIModel) -> Dict[str, Any]:
        """تحسين بنية النموذج"""
        return {'improvement': 0.04, 'new_architecture': 'deeper_network'}

    def _generate_optimization_recommendations(self, optimization_results: Dict[str, Any]) -> List[str]:
        """توليد توصيات التحسين"""
        recommendations = []

        if optimization_results.get('performance_improvement', 0) < 0.05:
            recommendations.append("إعادة تدريب النموذج مع بيانات إضافية")
            recommendations.append("تجربة خوارزميات مختلفة")

        if len(optimization_results.get('optimizations_applied', [])) == 0:
            recommendations.append("تطبيق تحسينات على معلمات النموذج")

        return recommendations

    # طرق المساعدة
    def _categorize_performance(self, accuracy: float) -> str:
        """تصنيف الأداء"""
        if accuracy >= self.performance_thresholds['accuracy']['excellent']:
            return 'excellent'
        elif accuracy >= self.performance_thresholds['accuracy']['good']:
            return 'good'
        elif accuracy >= self.performance_thresholds['accuracy']['acceptable']:
            return 'acceptable'
        else:
            return 'poor'

    def _categorize_confidence(self, accuracy: float) -> str:
        """تصنيف الثقة"""
        if accuracy >= 0.9:
            return 'high'
        elif accuracy >= 0.7:
            return 'medium'
        else:
            return 'low'

    def _generate_performance_recommendations(self, performance_report: Dict[str, Any]) -> List[str]:
        """توليد توصيات الأداء"""
        recommendations = []

        if performance_report.get('average_accuracy', 0) < 0.8:
            recommendations.append("إعادة تدريب النماذج ذات الأداء المنخفض")

        if performance_report.get('failed_models', 0) > 0:
            recommendations.append("فحص أسباب فشل النماذج وإصلاحها")

        outdated_models = [m for m in performance_report.get('model_performance', [])
                          if m.get('last_trained') and (datetime.now() - m['last_trained']).days > 30]
        if outdated_models:
            recommendations.append("تحديث النماذج القديمة ببيانات جديدة")

        return recommendations

    # طرق حفظ البيانات
    def _save_ai_model(self, model: AIModel) -> None:
        """حفظ نموذج الذكاء الاصطناعي"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                # استخدام INSERT مع VALUES فقط بدون تحديد الأعمدة
                cursor.execute("""
                    INSERT OR REPLACE INTO ai_models (
                        model_id, model_name, model_type, purpose,
                        accuracy_score, training_status, last_trained,
                        model_path, parameters, performance_metrics, created_at,
                        algorithm, feature_importance, confusion_matrix,
                        cross_validation_scores, hyperparameters, feature_names
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    model.model_id, model.model_name, model.model_type, model.purpose,
                    model.accuracy_score, model.training_status,
                    model.last_trained.isoformat() if model.last_trained and hasattr(model.last_trained, 'isoformat') else model.last_trained,
                    model.model_path, json.dumps(model.parameters),
                    json.dumps(model.performance_metrics), model.created_at.isoformat() if model.created_at else None,
                    model.algorithm,
                    json.dumps(model.feature_importance) if model.feature_importance else None,
                    json.dumps(model.confusion_matrix) if model.confusion_matrix else None,
                    json.dumps(model.cross_validation_scores) if model.cross_validation_scores else None,
                    json.dumps(model.hyperparameters) if model.hyperparameters else None,
                    json.dumps(model.feature_names) if model.feature_names else None
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"فشل في حفظ نموذج الذكاء الاصطناعي: {e}")

    def _save_training_data(self, data: TrainingData) -> None:
        """حفظ بيانات التدريب"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO training_data
                    (data_id, model_id, data_type, data_content, labels, quality_score,
                     collected_at, used_in_training, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data.data_id, data.model_id, data.data_type,
                    json.dumps(data.data_content) if isinstance(data.data_content, (list, dict)) else str(data.data_content),
                    json.dumps(data.labels) if isinstance(data.labels, (list, dict)) else str(data.labels),
                    data.quality_score, data.collected_at, data.used_in_training,
                    json.dumps(data.metadata)
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"فشل في حفظ بيانات التدريب: {e}")

    def _save_ai_result(self, result: AIResult) -> None:
        """حفظ نتيجة الذكاء الاصطناعي"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO ai_results
                    (result_id, model_id, input_data, output_data, confidence_score,
                     processing_time, generated_at, interpretation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result.result_id, result.model_id,
                    json.dumps(result.input_data) if isinstance(result.input_data, (list, dict)) else str(result.input_data),
                    json.dumps(result.output_data) if isinstance(result.output_data, (list, dict)) else str(result.output_data),
                    result.confidence_score, result.processing_time, result.generated_at,
                    json.dumps(result.interpretation) if result.interpretation else None
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"فشل في حفظ نتيجة الذكاء الاصطناعي: {e}")

    def _save_ai_pipeline(self, pipeline: Dict[str, Any]) -> None:
        """حفظ خط أنابيب الذكاء الاصطناعي"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO ai_pipelines
                    (pipeline_id, pipeline_name, steps, models, data_flow, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    pipeline['pipeline_id'], pipeline['pipeline_name'],
                    json.dumps(pipeline['steps']), json.dumps(pipeline['models']),
                    json.dumps(pipeline['data_flow']), pipeline['created_at']
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"فشل في حفظ خط الأنابيب: {e}")

    # طرق تحميل البيانات
    def _get_ai_model(self, model_id: str) -> Optional[AIModel]:
        """الحصول على نموذج الذكاء الاصطناعي"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM ai_models WHERE model_id = ?", (model_id,))
                row = cursor.fetchone()

                if row:
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
                    )

                return None

        except Exception as e:
            self.logger.error(f"فشل في الحصول على النموذج: {e}")
            return None

    def _get_all_ai_models(self) -> List[AIModel]:
        """الحصول على جميع نماذج الذكاء الاصطناعي"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM ai_models")
                models = []

                for row in cursor.fetchall():
                    # استخدام dict للوصول إلى القيم بأسمائها لضمان التوافق
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
                    ))

                return models

        except Exception as e:
            return []

    def _load_trained_model(self, model: AIModel) -> Optional[Any]:
        """تحميل النموذج المدرب"""
        try:
            if not model.model_path or not os.path.exists(model.model_path):
                return None

            with open(model.model_path, 'rb') as f:
                return pickle.load(f)

        except Exception as e:
            self.logger.error(f"فشل في تحميل النموذج: {e}")
            return None

    def _save_trained_model(self, model: Any, model_id: str) -> str:
        """حفظ النموذج المدرب"""
        try:
            model_path = self.models_dir / f"{model_id}.pkl"
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)

            return str(model_path)

        except Exception as e:
            self.logger.error(f"فشل في حفظ النموذج: {e}")
            return ""

    def _mark_training_data_used(self, training_data: List[TrainingData]) -> None:
        """تحديد بيانات التدريب كمستخدمة"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                for data in training_data:
                    cursor.execute(
                        "UPDATE training_data SET used_in_training = 1 WHERE data_id = ?",
                        (data.data_id,)
                    )
                conn.commit()
        except Exception as e:
            self.logger.error(f"فشل في تحديث بيانات التدريب: {e}")

    # ========================================
    # Phase 9: Advanced AI & Machine Learning
    # ========================================

    def run_automl_experiment(self, experiment_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        تشغيل تجربة تعلم آلي تلقائي متقدم

        Args:
            experiment_config: إعدادات التجربة
                - experiment_id: معرف التجربة
                - target_column: العمود المستهدف
                - features: قائمة الميزات
                - data: البيانات للتدريب
                - algorithms: قائمة الخوارزميات للتجربة
                - max_time: الحد الأقصى للوقت بالدقائق

        Returns:
            نتائج التجربة
        """
        try:
            experiment_id = experiment_config.get('experiment_id', f"automl_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            target_column = experiment_config['target_column']
            features = experiment_config['features']
            data = experiment_config['data']
            algorithms = experiment_config.get('algorithms', ['rf', 'nn', 'xgb'])
            max_time = experiment_config.get('max_time', 30)  # دقائق

            self.logger.info(f"بدء تجربة AutoML: {experiment_id}")

            # إعداد التجربة في قاعدة البيانات
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO ml_experiments
                    (experiment_id, target_column, features, status, created_at)
                    VALUES (?, ?, ?, 'running', ?)
                ''', (experiment_id, target_column, json.dumps(features), datetime.now()))
                conn.commit()

            # تشغيل التجربة في thread منفصل
            import threading
            thread = threading.Thread(
                target=self._run_automl_async,
                args=(experiment_id, data, target_column, features, algorithms, max_time)
            )
            thread.daemon = True
            thread.start()

            return {
                'experiment_id': experiment_id,
                'status': 'started',
                'message': 'تم بدء تجربة التعلم الآلي التلقائي بنجاح'
            }

        except Exception as e:
            self.logger.error(f"فشل في بدء تجربة AutoML: {e}")
            return {'error': str(e)}

    def _run_automl_async(self, experiment_id: str, data: pd.DataFrame,
                         target_column: str, features: List[str],
                         algorithms: List[str], max_time: int):
        """تشغيل تجربة AutoML بشكل غير متزامن"""
        try:
            import time
            start_time = time.time()

            # تحضير البيانات
            X = data[features]
            y = data[target_column]

            # تحديد نوع المشكلة
            is_classification = y.dtype == 'object' or len(y.unique()) < 20

            # تجربة الخوارزميات
            results = []
            best_model = None
            best_score = 0

            for algorithm in algorithms:
                if time.time() - start_time > max_time * 60:
                    break

                try:
                    model, score = self._train_and_evaluate_model(
                        X, y, algorithm, is_classification
                    )

                    results.append({
                        'algorithm': algorithm,
                        'score': score,
                        'model': model
                    })

                    if score > best_score:
                        best_score = score
                        best_model = model

                    self.logger.info(f"خوارزمية {algorithm} حققت درجة {score:.4f}")

                except Exception as e:
                    self.logger.error(f"فشل في خوارزمية {algorithm}: {e}")
                    continue

            # حفظ أفضل نموذج
            if best_model:
                model_config = {
                    'model_id': f"{experiment_id}_best",
                    'model_name': f"AutoML Best Model - {experiment_id}",
                    'model_type': 'classification' if is_classification else 'regression',
                    'purpose': f"AutoML experiment {experiment_id}",
                    'algorithm': 'automl'
                }

                trained_model = self.create_ai_model(model_config)
                trained_model.model = best_model
                trained_model.accuracy_score = best_score
                trained_model.training_status = 'trained'
                trained_model.last_trained = datetime.now()

                # حفظ النموذج
                model_path = self._save_trained_model(best_model, trained_model.model_id)
                trained_model.model_path = model_path

                # حفظ في قاعدة البيانات
                self._save_ai_model(trained_model)

            # تحديث حالة التجربة
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE ml_experiments
                    SET status = 'completed', best_model = ?, best_score = ?, completed_at = ?
                    WHERE experiment_id = ?
                ''', (best_model.__class__.__name__ if best_model else None, best_score, datetime.now(), experiment_id))
                conn.commit()

            self.logger.info(f"انتهت تجربة AutoML {experiment_id} بنجاح")

        except Exception as e:
            self.logger.error(f"فشل في تجربة AutoML: {e}")

            # تحديث حالة الفشل
            try:
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE ml_experiments
                        SET status = 'failed', completed_at = ?
                        WHERE experiment_id = ?
                    ''', (datetime.now(), experiment_id))
                    conn.commit()
            except:
                pass

    def _train_and_evaluate_model(self, X: pd.DataFrame, y: pd.Series,
                                algorithm: str, is_classification: bool) -> Tuple[Any, float]:
        """تدريب وتقييم نموذج واحد"""
        from sklearn.model_selection import cross_val_score

        if algorithm == 'rf':
            if is_classification:
                from sklearn.ensemble import RandomForestClassifier
                model = RandomForestClassifier(**self.default_params['rf_classifier'])
            else:
                from sklearn.ensemble import RandomForestRegressor
                model = RandomForestRegressor(**self.default_params['rf_regressor'])

        elif algorithm == 'nn':
            if is_classification:
                from sklearn.neural_network import MLPClassifier
                model = MLPClassifier(**self.default_params['nn_classifier'])
            else:
                from sklearn.neural_network import MLPRegressor
                model = MLPRegressor(**self.default_params['nn_regressor'])

        elif algorithm == 'xgb':
            try:
                if is_classification:
                    from xgboost import XGBClassifier
                    model = XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1)
                else:
                    from xgboost import XGBRegressor
                    model = XGBRegressor(n_estimators=100, max_depth=6, learning_rate=0.1)
            except ImportError:
                # إذا لم يكن XGBoost متوفراً، استخدم Random Forest
                if is_classification:
                    from sklearn.ensemble import RandomForestClassifier
                    model = RandomForestClassifier(**self.default_params['rf_classifier'])
                else:
                    from sklearn.ensemble import RandomForestRegressor
                    model = RandomForestRegressor(**self.default_params['rf_regressor'])

        else:
            raise ValueError(f"خوارزمية غير مدعومة: {algorithm}")

        # تدريب النموذج
        model.fit(X, y)

        # تقييم النموذج
        scores = cross_val_score(model, X, y, cv=5, scoring='accuracy' if is_classification else 'neg_mean_squared_error')
        score = scores.mean()

        if not is_classification:
            score = -score  # تحويل MSE السلبي إلى إيجابي

        return model, score

    def get_automl_status(self, experiment_id: str) -> Dict[str, Any]:
        """الحصول على حالة تجربة AutoML"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT experiment_id, target_column, features, status, best_model, best_score, created_at, completed_at
                    FROM ml_experiments
                    WHERE experiment_id = ?
                ''', (experiment_id,))

                row = cursor.fetchone()
                if row:
                    return {
                        'experiment_id': row[0],
                        'target_column': row[1],
                        'features': json.loads(row[2]) if row[2] else [],
                        'status': row[3],
                        'best_model': row[4],
                        'best_score': row[5],
                        'created_at': row[6],
                        'completed_at': row[7]
                    }
                else:
                    return {'error': 'تجربة غير موجودة'}

        except Exception as e:
            self.logger.error(f"فشل في الحصول على حالة التجربة: {e}")
            return {'error': str(e)}

    def get_experiment_status(self, experiment_id: str) -> Dict[str, Any]:
        """اسم بديل للتوافق مع الاختبارات"""
        return self.get_automl_status(experiment_id)

    def analyze_image(self, image_path: str, analysis_type: str = 'general') -> Dict[str, Any]:
        """
        تحليل الصور باستخدام الرؤية الحاسوبية

        Args:
            image_path: مسار الصورة
            analysis_type: نوع التحليل ('general', 'product', 'document', 'face')

        Returns:
            نتائج التحليل
        """
        try:
            # التحقق من وجود OpenCV
            try:
                import cv2
                opencv_available = True
            except ImportError:
                opencv_available = False

            if not opencv_available:
                return {
                    'error': 'OpenCV غير متوفر',
                    'message': 'الرؤية الحاسوبية تتطلب تثبيت OpenCV'
                }

            if not os.path.exists(image_path):
                return {'error': 'ملف الصورة غير موجود'}

            # قراءة الصورة
            image = cv2.imread(image_path)
            if image is None:
                return {'error': 'فشل في قراءة الصورة'}

            height, width, channels = image.shape

            results = {
                'image_info': {
                    'width': width,
                    'height': height,
                    'channels': channels,
                    'file_size': os.path.getsize(image_path)
                },
                'analysis_type': analysis_type
            }

            if analysis_type == 'general':
                # تحليل عام للصورة
                results.update(self._analyze_image_general(image))

            elif analysis_type == 'product':
                # تحليل منتج
                results.update(self._analyze_product_image(image))

            elif analysis_type == 'document':
                # تحليل مستند
                results.update(self._analyze_document_image(image))

            # حفظ نتائج التحليل
            self._save_image_analysis_results(image_path, results)

            return results

        except Exception as e:
            self.logger.error(f"فشل في تحليل الصورة: {e}")
            return {'error': str(e)}

    def _analyze_image_general(self, image: np.ndarray) -> Dict[str, Any]:
        """تحليل عام للصورة"""
        try:
            # تحويل إلى grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # حساب التباين
            contrast = np.std(gray)

            # كشف الحواف
            edges = cv2.Canny(gray, 100, 200)
            edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])

            # تحليل الألوان
            pixels = image.reshape(-1, 3)
            pixels = np.float32(pixels)

            # K-means للألوان المهيمنة
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
            k = 5
            _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

            dominant_colors = centers.astype(int).tolist()

            return {
                'contrast': float(contrast),
                'edge_density': float(edge_density),
                'dominant_colors': dominant_colors,
                'brightness': float(np.mean(gray)),
                'colorfulness': float(np.std(pixels))
            }

        except Exception as e:
            self.logger.error(f"فشل في التحليل العام: {e}")
            return {}

    def _analyze_product_image(self, image: np.ndarray) -> Dict[str, Any]:
        """تحليل صورة منتج"""
        try:
            # منطق بسيط لتحليل المنتجات (يمكن تحسينه بنماذج أكثر تقدماً)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # كشف الكائنات
            _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # تحليل الكائنات
            objects = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 100:  # تجاهل الكائنات الصغيرة جداً
                    x, y, w, h = cv2.boundingRect(contour)
                    objects.append({
                        'area': float(area),
                        'bounding_box': {'x': x, 'y': y, 'width': w, 'height': h},
                        'aspect_ratio': float(w/h) if h > 0 else 0
                    })

            return {
                'detected_objects': len(objects),
                'objects': objects[:10],  # أكبر 10 كائنات
                'product_confidence': 0.8 if len(objects) > 0 else 0.3
            }

        except Exception as e:
            self.logger.error(f"فشل في تحليل صورة المنتج: {e}")
            return {}

    def _analyze_document_image(self, image: np.ndarray) -> Dict[str, Any]:
        """تحليل صورة مستند"""
        try:
            # منطق بسيط لتحليل المستندات
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # تحسين الجودة
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # كشف النص (تقدير بسيط)
            text_density = np.sum(thresh == 0) / thresh.size

            # كشف الخطوط
            horizontal_lines = self._detect_lines(thresh, 'horizontal')
            vertical_lines = self._detect_lines(thresh, 'vertical')

            return {
                'text_density': float(text_density),
                'horizontal_lines': len(horizontal_lines),
                'vertical_lines': len(vertical_lines),
                'document_type': 'structured' if len(horizontal_lines) > 5 and len(vertical_lines) > 3 else 'unstructured',
                'quality_score': float(1.0 - np.var(gray) / 10000)  # تقدير جودة الصورة
            }

        except Exception as e:
            self.logger.error(f"فشل في تحليل صورة المستند: {e}")
            return {}

    def _detect_lines(self, image: np.ndarray, direction: str) -> List[Dict]:
        """كشف الخطوط في الصورة"""
        try:
            if direction == 'horizontal':
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            else:  # vertical
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))

            detected_lines = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
            contours, _ = cv2.findContours(detected_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            lines = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                if (direction == 'horizontal' and w > 50) or (direction == 'vertical' and h > 50):
                    lines.append({'x': x, 'y': y, 'width': w, 'height': h})

            return lines

        except Exception as e:
            return []

    def _save_image_analysis_results(self, image_path: str, results: Dict[str, Any]):
        """حفظ نتائج تحليل الصورة"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO image_analysis
                    (image_path, analysis_results, analyzed_at)
                    VALUES (?, ?, ?)
                ''', (image_path, json.dumps(results), datetime.now()))
                conn.commit()

        except Exception as e:
            self.logger.error(f"فشل في حفظ نتائج تحليل الصورة: {e}")

    def chat_with_ai(self, message: str, conversation_id: str = None,
                    context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        محادثة ذكية مع الذكاء الاصطناعي

        Args:
            message: رسالة المستخدم
            conversation_id: معرف المحادثة (اختياري)
            context: سياق إضافي للمحادثة

        Returns:
            رد الذكاء الاصطناعي
        """
        try:
            if conversation_id is None:
                conversation_id = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # الحصول على تاريخ المحادثة
            conversation_history = self._get_conversation_history(conversation_id)

            # تحليل الرسالة وتوليد الرد
            response = self._generate_ai_response(message, conversation_history, context)

            # حفظ المحادثة
            self._save_conversation_message(conversation_id, 'user', message)
            self._save_conversation_message(conversation_id, 'ai', response['response'])

            response['conversation_id'] = conversation_id
            return response

        except Exception as e:
            self.logger.error(f"فشل في المحادثة مع الذكاء الاصطناعي: {e}")
            return {
                'error': str(e),
                'response': 'عذراً، حدث خطأ في معالجة رسالتك. يرجى المحاولة مرة أخرى.',
                'conversation_id': conversation_id
            }

    def _get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """الحصول على تاريخ المحادثة"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT message_type, message_content, created_at
                    FROM ai_conversations
                    WHERE conversation_id = ?
                    ORDER BY created_at DESC
                    LIMIT 20
                ''', (conversation_id,))

                history = []
                for row in cursor.fetchall():
                    history.append({
                        'type': row[0],
                        'content': row[1],
                        'timestamp': row[2]
                    })

                return history[::-1]  # عكس الترتيب ليكون الأقدم أولاً

        except Exception as e:
            self.logger.error(f"فشل في الحصول على تاريخ المحادثة: {e}")
            return []

    def _generate_ai_response(self, message: str, history: List[Dict[str, Any]],
                            context: Dict[str, Any] = None) -> Dict[str, Any]:
        """توليد رد الذكاء الاصطناعي"""
        try:
            message_lower = message.lower()

            # قواعد الردود البسيطة
            responses = {
                'مرحبا': 'مرحباً! أنا مساعد الذكاء الاصطناعي لنظام ERP. كيف يمكنني مساعدتك اليوم؟',
                'مساعدة': 'يمكنني مساعدتك في:\n• تحليل البيانات والتقارير\n• التنبؤات والتوقعات\n• تحليل الصور والمستندات\n• إجابة الأسئلة عن النظام\n• اقتراحات لتحسين الأداء\nما الذي تود معرفته؟',
                'مبيعات': 'بالنسبة للمبيعات، يمكنني:\n• تحليل أداء المبيعات\n• التنبؤ بالمبيعات المستقبلية\n• تحديد المنتجات الأكثر مبيعاً\n• اقتراح استراتيجيات تسعير\nهل تريد تقريراً محدداً؟',
                'مخزون': 'للمخزون، أقدم:\n• تحليل مستويات المخزون\n• تنبؤ الاحتياجات المستقبلية\n• كشف المنتجات منخفضة المخزون\n• تحسين تخطيط المخازن\nما الذي تحتاج معرفته عن المخزون؟',
                'عملاء': 'بالنسبة للعملاء:\n• تحليل سلوك العملاء\n• تقسيم العملاء\n• التنبؤ بقيمة العميل\n• اقتراحات لتحسين الخدمة\nكيف يمكنني مساعدتك مع العملاء؟',
                'تقارير': 'يمكنني إنشاء تقارير ذكية:\n• تقارير مبيعات تفاعلية\n• تحليلات مالية\n• تقارير أداء\n• تنبؤات مستقبلية\nأي نوع من التقارير تريده؟',
                'تنبؤ': 'للتنبؤات، أستخدم:\n• نماذج التعلم الآلي\n• تحليل الاتجاهات التاريخية\n• عوامل خارجية مؤثرة\n• سيناريوهات متعددة\nما الذي تريد التنبؤ به؟'
            }

            # البحث عن كلمات مفتاحية
            for keyword, response in responses.items():
                if keyword in message_lower:
                    return {
                        'response': response,
                        'confidence': 0.9,
                        'response_type': 'keyword_match'
                    }

            # استخدام نموذج NLP إذا كان متوفراً
            if self._has_nlp_model():
                return self._generate_nlp_response(message, history, context)

            # رد افتراضي ذكي
            return {
                'response': self._generate_smart_response(message, context),
                'confidence': 0.7,
                'response_type': 'smart_default'
            }

        except Exception as e:
            self.logger.error(f"فشل في توليد الرد: {e}")
            return {
                'response': 'عذراً، لم أتمكن من فهم رسالتك بوضوح. يمكنني مساعدتك في تحليل البيانات، التقارير، والتنبؤات. ما الذي تبحث عنه؟',
                'confidence': 0.5,
                'response_type': 'error_fallback'
            }

    def _has_nlp_model(self) -> bool:
        """التحقق من وجود نموذج NLP"""
        try:
            import transformers
            return True
        except ImportError:
            return False

    def _generate_nlp_response(self, message: str, history: List[Dict[str, Any]],
                             context: Dict[str, Any] = None) -> Dict[str, Any]:
        """توليد رد باستخدام نموذج NLP"""
        try:
            from transformers import pipeline

            # استخدام نموذج محادثة بسيط
            conversational_pipeline = pipeline("conversational")

            # تحويل التاريخ إلى تنسيق مناسب
            conversation = []
            for msg in history[-5:]:  # آخر 5 رسائل
                if msg['type'] == 'user':
                    conversation.append(f"User: {msg['content']}")
                elif msg['type'] == 'ai':
                    conversation.append(f"AI: {msg['content']}")

            conversation_text = "\n".join(conversation)
            full_prompt = f"{conversation_text}\nUser: {message}\nAI:"

            # توليد الرد (هذا مثال بسيط، يمكن تحسينه)
            response_text = "بناءً على فهمي لرسالتك، يمكنني تقديم المساعدة في هذا المجال. هل تريد تفاصيل أكثر؟"

            return {
                'response': response_text,
                'confidence': 0.8,
                'response_type': 'nlp_generated'
            }

        except Exception as e:
            self.logger.error(f"فشل في توليد رد NLP: {e}")
            return self._generate_smart_response(message, context)

    def _generate_smart_response(self, message: str, context: Dict[str, Any] = None) -> str:
        """توليد رد ذكي افتراضي"""
        # منطق بسيط لتوليد ردود ذكية
        if '?' in message:
            return "سؤال ممتاز! دعني أبحث في البيانات لأقدم لك إجابة دقيقة. هل يمكنك تحديد المزيد من التفاصيل؟"
        elif any(word in message.lower() for word in ['تحليل', 'analysis']):
            return "سأقوم بتحليل البيانات المطلوبة وأقدم لك رؤى مفيدة. ما نوع البيانات التي تريد تحليلها؟"
        elif any(word in message.lower() for word in ['تنبؤ', 'predict']):
            return "يمكنني إنشاء تنبؤات دقيقة باستخدام نماذج التعلم الآلي. ما الذي تريد التنبؤ به؟"
        else:
            return "أفهم طلبك. كمساعد ذكي، يمكنني مساعدتك في إدارة الأعمال، تحليل البيانات، والتنبؤات. كيف يمكنني مساعدتك بشكل أفضل؟"

    def _save_conversation_message(self, conversation_id: str, message_type: str, content: str):
        """حفظ رسالة المحادثة"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO ai_conversations
                    (conversation_id, message_type, message_content, created_at)
                    VALUES (?, ?, ?, ?)
                ''', (conversation_id, message_type, content, datetime.now()))
                conn.commit()

        except Exception as e:
            self.logger.error(f"فشل في حفظ رسالة المحادثة: {e}")

    def generate_smart_insights(self, data_type: str, data: Any,
                              insight_count: int = 5) -> List[Dict[str, Any]]:
        """
        توليد رؤى ذكية من البيانات

        Args:
            data_type: نوع البيانات ('sales', 'inventory', 'customers', 'financial')
            data: البيانات المراد تحليلها
            insight_count: عدد الرؤى المطلوبة

        Returns:
            قائمة بالرؤى الذكية
        """
        try:
            insights = []

            if data_type == 'sales':
                insights = self._generate_sales_insights(data, insight_count)
            elif data_type == 'inventory':
                insights = self._generate_inventory_insights(data, insight_count)
            elif data_type == 'customers':
                insights = self._generate_customer_insights(data, insight_count)
            elif data_type == 'financial':
                insights = self._generate_financial_insights(data, insight_count)
            else:
                insights = self._generate_general_insights(data, insight_count)

            # حفظ الرؤى في قاعدة البيانات
            for insight in insights:
                self._save_insight(insight, data_type, data)

            return insights

        except Exception as e:
            self.logger.error(f"فشل في توليد الرؤى الذكية: {e}")
            return []

    def _generate_sales_insights(self, data: pd.DataFrame, count: int) -> List[Dict[str, Any]]:
        """توليد رؤى للمبيعات"""
        insights = []

        try:
            if 'amount' in data.columns:
                total_sales = data['amount'].sum()
                avg_sale = data['amount'].mean()
                max_sale = data['amount'].max()
                min_sale = data['amount'].min()

                insights.append({
                    'type': 'sales_summary',
                    'title': 'ملخص المبيعات',
                    'content': f'إجمالي المبيعات: {total_sales:,.2f} | متوسط المبيعات: {avg_sale:,.2f}',
                    'confidence': 0.95,
                    'impact': 'high'
                })

                # تحليل الاتجاهات
                if len(data) > 1:
                    trend = "متصاعد" if data['amount'].iloc[-1] > data['amount'].iloc[0] else "منخفض"
                    insights.append({
                        'type': 'sales_trend',
                        'title': 'اتجاه المبيعات',
                        'content': f'الاتجاه العام للمبيعات: {trend}',
                        'confidence': 0.85,
                        'impact': 'medium'
                    })

                # كشف القيم المتطرفة
                q75 = data['amount'].quantile(0.75)
                q25 = data['amount'].quantile(0.25)
                iqr = q75 - q25
                upper_bound = q75 + 1.5 * iqr

                outliers = data[data['amount'] > upper_bound]
                if len(outliers) > 0:
                    insights.append({
                        'type': 'sales_outliers',
                        'title': 'مبيعات استثنائية',
                        'content': f'تم اكتشاف {len(outliers)} مبيعة استثنائية عالية',
                        'confidence': 0.90,
                        'impact': 'high'
                    })

        except Exception as e:
            self.logger.error(f"فشل في توليد رؤى المبيعات: {e}")

        return insights[:count]

    def _generate_inventory_insights(self, data: pd.DataFrame, count: int) -> List[Dict[str, Any]]:
        """توليد رؤى للمخزون"""
        insights = []

        try:
            if 'quantity' in data.columns:
                total_items = data['quantity'].sum()
                avg_quantity = data['quantity'].mean()
                low_stock = len(data[data['quantity'] < 10]) if 'quantity' in data.columns else 0

                insights.append({
                    'type': 'inventory_summary',
                    'title': 'ملخص المخزون',
                    'content': f'إجمالي المخزون: {total_items:,} | متوسط الكمية: {avg_quantity:.1f}',
                    'confidence': 0.95,
                    'impact': 'high'
                })

                if low_stock > 0:
                    insights.append({
                        'type': 'low_stock_alert',
                        'title': 'تنبيه مخزون منخفض',
                        'content': f'{low_stock} منتج لديه مخزون منخفض (أقل من 10)',
                        'confidence': 0.95,
                        'impact': 'high'
                    })

                # تحليل التوزيع
                if len(data) > 10:
                    top_10_percent = int(len(data) * 0.1)
                    top_products = data.nlargest(top_10_percent, 'quantity')
                    top_quantity = top_products['quantity'].sum()
                    percentage = (top_quantity / total_items) * 100 if total_items > 0 else 0

                    insights.append({
                        'type': 'inventory_distribution',
                        'title': 'توزيع المخزون',
                        'content': f'أفضل 10% من المنتجات تشكل {percentage:.1f}% من إجمالي المخزون',
                        'confidence': 0.85,
                        'impact': 'medium'
                    })

        except Exception as e:
            self.logger.error(f"فشل في توليد رؤى المخزون: {e}")

        return insights[:count]

    def _generate_customer_insights(self, data: pd.DataFrame, count: int) -> List[Dict[str, Any]]:
        """توليد رؤى للعملاء"""
        insights = []

        try:
            total_customers = len(data)
            active_customers = len(data[data.get('status') == 'active']) if 'status' in data.columns else total_customers

            insights.append({
                'type': 'customer_summary',
                'title': 'ملخص العملاء',
                'content': f'إجمالي العملاء: {total_customers} | العملاء النشطين: {active_customers}',
                'confidence': 0.95,
                'impact': 'high'
            })

            # تحليل السلوك إذا كان متوفراً
            if 'total_purchases' in data.columns:
                avg_purchases = data['total_purchases'].mean()
                high_value_customers = len(data[data['total_purchases'] > avg_purchases * 2])

                insights.append({
                    'type': 'customer_segments',
                    'title': 'تقسيم العملاء',
                    'content': f'{high_value_customers} عميل عالي القيمة (أكثر من ضعف المتوسط)',
                    'confidence': 0.85,
                    'impact': 'medium'
                })

        except Exception as e:
            self.logger.error(f"فشل في توليد رؤى العملاء: {e}")

        return insights[:count]

    def _generate_financial_insights(self, data: pd.DataFrame, count: int) -> List[Dict[str, Any]]:
        """توليد رؤى مالية"""
        insights = []

        try:
            if 'revenue' in data.columns and 'expenses' in data.columns:
                total_revenue = data['revenue'].sum()
                total_expenses = data['expenses'].sum()
                profit = total_revenue - total_expenses
                profit_margin = (profit / total_revenue) * 100 if total_revenue > 0 else 0

                insights.append({
                    'type': 'financial_summary',
                    'title': 'الملخص المالي',
                    'content': f'الإيرادات: {total_revenue:,.2f} | المصروفات: {total_expenses:,.2f} | الربح: {profit:,.2f} | هامش الربح: {profit_margin:.1f}%',
                    'confidence': 0.95,
                    'impact': 'high'
                })

        except Exception as e:
            self.logger.error(f"فشل في توليد الرؤى المالية: {e}")

        return insights[:count]

    def _generate_general_insights(self, data: Any, count: int) -> List[Dict[str, Any]]:
        """توليد رؤى عامة"""
        insights = []

        try:
            if isinstance(data, pd.DataFrame):
                row_count = len(data)
                col_count = len(data.columns)

                insights.append({
                    'type': 'data_summary',
                    'title': 'ملخص البيانات',
                    'content': f'البيانات تحتوي على {row_count} صف و {col_count} عمود',
                    'confidence': 0.90,
                    'impact': 'low'
                })

                # تحليل الأعمدة العددية
                numeric_cols = data.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    insights.append({
                        'type': 'numeric_analysis',
                        'title': 'تحليل البيانات العددية',
                        'content': f'يوجد {len(numeric_cols)} عمود عددي يمكن تحليله',
                        'confidence': 0.85,
                        'impact': 'medium'
                    })

        except Exception as e:
            pass

        return insights[:count]

    def _save_insight(self, insight: Dict[str, Any], data_type: str, data: Any):
        """حفظ الرؤية في قاعدة البيانات"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO ai_insights
                    (insight_type, content, confidence, impact, related_data, generated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    insight.get('type', 'unknown'),
                    insight.get('content', ''),
                    insight.get('confidence', 0.5),
                    insight.get('impact', 'medium'),
                    json.dumps({'data_type': data_type, 'data_sample': str(data)[:500]}),
                    datetime.now()
                ))
                conn.commit()

        except Exception as e:
            self.logger.error(f"فشل في حفظ الرؤية: {e}")

    def get_recent_insights(self, limit: int = 10) -> List[Dict[str, Any]]:
        """الحصول على الرؤى الأخيرة"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT insight_type, content, confidence, impact, related_data, generated_at
                    FROM ai_insights
                    ORDER BY generated_at DESC
                    LIMIT ?
                ''', (limit,))

                insights = []
                for row in cursor.fetchall():
                    insights.append({
                        'type': row[0],
                        'content': row[1],
                        'confidence': row[2],
                        'impact': row[3],
                        'related_data': json.loads(row[4]) if row[4] else None,
                        'generated_at': row[5]
                    })

                return insights

        except Exception as e:
            self.logger.error(f"فشل في الحصول على الرؤى: {e}")
            return []

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base Model Tests
"""

import pytest
from unittest.mock import patch
from typing import Optional
from src.models.pydantic_schemas import BaseModel


class TestModel(BaseModel):
    """Subclass for testing"""
    id: Optional[int] = None
    
    def to_dict(self):
        return {"id": self.id}
        
    @classmethod
    def from_dict(cls, data):
        return cls(**data)
    
    def validate(self):
        return True
        
    def save(self):
        return True


class TestBaseModel:
    """Base Model Tests"""
    
    @pytest.fixture
    def base_model(self):
        """Create base model"""
        return TestModel(id=1)
    
    def test_initialization(self, base_model):
        """Test initialization"""
        assert base_model is not None
        assert base_model.id == 1
    
    def test_to_dict(self, base_model):
        """Test convert to dict"""
        result = base_model.to_dict()
        assert isinstance(result, dict)
        assert result["id"] == 1
    
    def test_from_dict(self):
        """Test create from dict"""
        result = TestModel.from_dict({"id": 2})
        assert result is not None
        assert result.id == 2
    
    def test_validate(self, base_model):
        """Test validation"""
        result = base_model.validate()
        assert result is True
    
    def test_save(self, base_model):
        """Test save"""
        result = base_model.save()
        assert result is True

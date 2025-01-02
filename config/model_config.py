from typing import Dict, Optional

class ModelConfig:
    _instance = None
    _initialized = False
    
    @classmethod
    def initialize(cls) -> None:
        if not cls._initialized:
            cls._initialized = True
            
    @classmethod
    def get_response_format(cls) -> Dict[str, str]:
        return {
            "type": "structured",
            "format": "therapeutic",
            "style": "empathetic"
        }
        
    @staticmethod
    def get_model_parameters() -> Dict[str, any]:
        return {
            "attention_slicing": True,
            "gradient_checkpointing": True,
            "torch_dtype": "float16",
            "device_map": "auto",
        }

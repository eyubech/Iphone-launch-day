import json
import os
from datetime import datetime

class ConfigManager:
    """Manages configuration loading, saving, and validation"""
    
    def __init__(self):
        self.default_config_path = "default_config.json"
        self.supported_models = {
            "14": ["Standard", "Plus", "Pro", "Pro Max"],
            "15": ["Standard", "Plus", "Pro", "Pro Max"],
            "16": ["Standard", "Plus", "Pro", "Pro Max"]
        }
    
    def create_default_config(self):
        """Create a default configuration file"""
        default_config = [
            {
                "version": "16 Pro",
                "color": 1,
                "storage": 1,
                "pieces": 1,
                "created_at": datetime.now().isoformat(),
                "description": "Default iPhone 16 Pro configuration"
            }
        ]
        
        try:
            with open(self.default_config_path, 'w', encoding='utf-8') as file:
                json.dump(default_config, file, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error creating default config: {e}")
            return False
    
    def load_config(self, file_path):
        """Load configuration from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # Validate configuration
            if self.validate_config(data):
                return data
            else:
                raise ValueError("Invalid configuration format")
                
        except FileNotFoundError:
            print(f"Configuration file not found: {file_path}")
            return None
        except json.JSONDecodeError:
            print(f"Invalid JSON format in file: {file_path}")
            return None
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return None
    
    def save_config(self, config_data, file_path):
        """Save configuration to JSON file"""
        try:
            # Add metadata
            enhanced_config = []
            for item in config_data:
                enhanced_item = item.copy()
                enhanced_item["created_at"] = datetime.now().isoformat()
                enhanced_item["description"] = f"iPhone {item.get('version', 'Unknown')} configuration"
                enhanced_config.append(enhanced_item)
            
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(enhanced_config, file, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def validate_config(self, config_data):
        """Validate configuration data structure"""
        if not isinstance(config_data, list):
            return False
        
        required_fields = ['version', 'color', 'storage', 'pieces']
        
        for item in config_data:
            if not isinstance(item, dict):
                return False
            
            # Check required fields
            for field in required_fields:
                if field not in item:
                    return False
            
            # Validate field types and ranges
            try:
                if not isinstance(item['version'], str):
                    return False
                
                color = int(item['color'])
                storage = int(item['storage'])
                pieces = int(item['pieces'])
                
                if not (1 <= color <= 3):
                    return False
                if not (1 <= storage <= 3):
                    return False
                if not (1 <= pieces <= 10):
                    return False
                    
            except (ValueError, TypeError):
                return False
        
        return True
    
    def validate_model_version(self, version):
        """Validate if the model version is supported"""
        try:
            parts = version.split()
            if len(parts) < 2:
                return False
            
            model = parts[0]  # e.g., "16"
            variant = " ".join(parts[1:])  # e.g., "Pro Max"
            
            if model not in self.supported_models:
                return False
            
            if variant not in self.supported_models[model]:
                return False
            
            return True
            
        except Exception:
            return False
    
    def generate_all_combinations_config(self, model, variant):
        """Generate configuration for all color/storage combinations"""
        if not self.validate_model_version(f"{model} {variant}"):
            return None
        
        configurations = []
        version = f"{model} {variant}"
        
        for color in [1, 2, 3]:
            for storage in [1, 2, 3]:
                config = {
                    "version": version,
                    "color": color,
                    "storage": storage,
                    "pieces": 1,
                    "description": f"Auto-generated: {version} Color-{color} Storage-{storage}"
                }
                configurations.append(config)
        
        return configurations
    
    def get_model_info(self):
        """Get information about supported models"""
        return {
            "supported_models": self.supported_models,
            "total_models": sum(len(variants) for variants in self.supported_models.values()),
            "latest_model": "16",
            "available_variants": ["Standard", "Plus", "Pro", "Pro Max"],
            "color_options": {"1": "First Color", "2": "Second Color", "3": "Third Color"},
            "storage_options": {"1": "Base Storage", "2": "Mid Storage", "3": "Max Storage"}
        }
    
    def create_sample_configs(self):
        """Create sample configuration files for testing"""
        samples = {
            "sample_single.json": [
                {
                    "version": "16 Pro",
                    "color": 1,
                    "storage": 2,
                    "pieces": 1,
                    "description": "Single iPhone 16 Pro configuration"
                }
            ],
            "sample_multiple.json": [
                {
                    "version": "16 Pro",
                    "color": 1,
                    "storage": 1,
                    "pieces": 1,
                    "description": "iPhone 16 Pro - Space Black, 128GB"
                },
                {
                    "version": "16 Pro Max",
                    "color": 2,
                    "storage": 3,
                    "pieces": 2,
                    "description": "iPhone 16 Pro Max - Blue Titanium, 1TB (x2)"
                }
            ],
            "sample_all_combinations.json": self.generate_all_combinations_config("15", "Pro")
        }
        
        created_files = []
        for filename, config in samples.items():
            if config and self.save_config(config, filename):
                created_files.append(filename)
        
        return created_files
    
    def get_config_summary(self, config_data):
        """Generate a summary of the configuration"""
        if not config_data:
            return "No configuration data"
        
        total_items = len(config_data)
        total_pieces = sum(item.get('pieces', 1) for item in config_data)
        
        models = {}
        for item in config_data:
            version = item.get('version', 'Unknown')
            models[version] = models.get(version, 0) + 1
        
        summary = {
            "total_configurations": total_items,
            "total_devices": total_pieces,
            "models_breakdown": models,
            "estimated_time_minutes": total_items * 2,  # Rough estimate
        }
        
        return summary
    
    def merge_configs(self, *config_files):
        """Merge multiple configuration files"""
        merged_config = []
        
        for file_path in config_files:
            config = self.load_config(file_path)
            if config:
                merged_config.extend(config)
        
        return merged_config if merged_config else None
    
    def filter_config(self, config_data, **filters):
        """Filter configuration based on criteria"""
        if not config_data:
            return []
        
        filtered = []
        for item in config_data:
            match = True
            
            for key, value in filters.items():
                if key in item and item[key] != value:
                    match = False
                    break
            
            if match:
                filtered.append(item)
        
        return filtered
    
    def export_config_report(self, config_data, output_path):
        """Export configuration as a detailed report"""
        if not config_data:
            return False
        
        try:
            report = {
                "report_generated": datetime.now().isoformat(),
                "summary": self.get_config_summary(config_data),
                "configurations": config_data,
                "model_info": self.get_model_info()
            }
            
            with open(output_path, 'w', encoding='utf-8') as file:
                json.dump(report, file, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Error exporting report: {e}")
            return False
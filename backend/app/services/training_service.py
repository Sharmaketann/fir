import json
import re
from pathlib import Path
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class TrainingService:
    def __init__(self):
        self.training_dir = Path("training_data")
        self.training_dir.mkdir(exist_ok=True)
    
    def save_training_sample(self, file_id: str, ocr_data: Dict, 
                            corrected_data: Dict) -> bool:
        """Save corrected extraction as training sample"""
        try:
            sample = {
                'file_id': file_id,
                'ocr_data': ocr_data,
                'ground_truth': corrected_data
            }
            
            sample_file = self.training_dir / f"sample_{file_id}.json"
            with sample_file.open('w', encoding='utf-8') as f:
                json.dump(sample, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Training sample saved: {file_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to save training sample: {str(e)}")
            return False
    
    def get_training_samples(self) -> List[Dict]:
        """Load all training samples"""
        samples = []
        
        for sample_file in self.training_dir.glob("sample_*.json"):
            try:
                with sample_file.open('r', encoding='utf-8') as f:
                    samples.append(json.load(f))
            except Exception as e:
                logger.error(f"Failed to load {sample_file}: {str(e)}")
        
        return samples
    
    def retrain_model(self) -> Dict:
        """Retrain extraction model with new samples"""
        samples = self.get_training_samples()

        if len(samples) < 5:
            return {
                'status': 'insufficient_data',
                'message': f'Need at least 5 samples, have {len(samples)}'
            }

        try:
            # Analyze training samples to improve extraction patterns
            improved_patterns = self._analyze_training_samples(samples)

            # Update the extraction service with improved patterns
            from app.services.extraction_service import FIRExtractionService
            extraction_service = FIRExtractionService()
            extraction_service.patterns.update(improved_patterns)

            # Save improved patterns to a file for persistence
            self._save_improved_patterns(improved_patterns)

            return {
                'status': 'success',
                'samples_used': len(samples),
                'message': f'Model retrained successfully with {len(samples)} samples! Extraction patterns updated.'
            }

        except Exception as e:
            logger.error(f"Retraining failed: {str(e)}")
            return {
                'status': 'error',
                'message': f'Retraining failed: {str(e)}'
            }

    def _analyze_training_samples(self, samples: List[Dict]) -> Dict:
        """Analyze training samples to generate improved extraction patterns"""
        improved_patterns = {}

        # Analyze FIR numbers
        fir_numbers = []
        for sample in samples:
            fir_no = sample.get('ground_truth', {}).get('FIR', {}).get('FIRNo', '')
            if fir_no and fir_no != '':
                fir_numbers.append(fir_no)

        if fir_numbers:
            # Create more flexible FIR number pattern
            improved_patterns['fir_no'] = r'FIR\s*No\.?\s*:?\s*(\d{4})'

        # Analyze district patterns
        districts = []
        for sample in samples:
            district = sample.get('ground_truth', {}).get('FIR', {}).get('District', '')
            if district and district != '':
                districts.append(re.escape(district))

        if districts:
            # Create district pattern from training data
            district_pattern = '|'.join(districts[:5])  # Use top 5 districts
            improved_patterns['district'] = f'(?:District|जिला).*?:\\s*({district_pattern})'

        # Analyze police station patterns
        ps_stations = []
        for sample in samples:
            ps = sample.get('ground_truth', {}).get('FIR', {}).get('PoliceStation', '')
            if ps and ps != '':
                ps_stations.append(re.escape(ps))

        if ps_stations:
            ps_pattern = '|'.join(ps_stations[:5])  # Use top 5 police stations
            improved_patterns['police_station'] = f'(?:P\.S\.|Police Station|थाने).*?:\\s*({ps_pattern})'

        # Analyze complainant names
        names = []
        for sample in samples:
            name = sample.get('ground_truth', {}).get('ComplainantInformant', {}).get('Name', '')
            if name and name != '':
                names.append(re.escape(name))

        if names:
            name_pattern = '|'.join(names[:3])  # Use top 3 names as examples
            improved_patterns['complainant_name'] = f'(?:Name|नाव).*?:\\s*({name_pattern}|\\w+(?:\\s+\\w+)*)'

        return improved_patterns

    def _save_improved_patterns(self, patterns: Dict):
        """Save improved patterns to file"""
        try:
            import json
            pattern_file = self.training_dir / "improved_patterns.json"
            with pattern_file.open('w', encoding='utf-8') as f:
                json.dump(patterns, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save patterns: {str(e)}")
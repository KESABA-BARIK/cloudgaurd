"""
Simple Autoencoder for Anomaly Detection

Uses PyTorch to train an autoencoder on normal configurations.
Reconstruction error serves as anomaly score.
"""

import torch
import torch.nn as nn
import numpy as np
from typing import List, Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class SimpleAutoencoder(nn.Module):
    """
    Simple autoencoder for anomaly detection.
    
    Architecture:
    - Input -> Dense(64) -> Dense(32) -> Dense(32) -> Dense(64) -> Output
    """
    
    def __init__(self, input_dim: int, encoding_dim: int = 32):
        super(SimpleAutoencoder, self).__init__()
        
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, encoding_dim),
            nn.ReLU()
        )
        
        self.decoder = nn.Sequential(
            nn.Linear(encoding_dim, 64),
            nn.ReLU(),
            nn.Linear(64, input_dim)
        )
    
    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded
    
    def encode(self, x):
        """Get latent representation."""
        return self.encoder(x)


class AutoencoderAnomalyDetector:
    """
    Autoencoder-based anomaly detector for configurations.
    
    Training process:
    1. Extract features from normal configs
    2. Train autoencoder to reconstruct
    3. Calculate reconstruction error as anomaly score
    
    Reconstruction error = ||input - reconstructed||^2
    High error = anomaly, Low error = normal
    """
    
    def __init__(self, input_dim: int = 12, encoding_dim: int = 6, device: str = 'cpu'):
        self.input_dim = input_dim
        self.encoding_dim = encoding_dim
        self.device = torch.device(device)
        self.model = None
        self.threshold = None
        self.reconstruction_errors = []
        self.scaler_mean = None
        self.scaler_std = None
    
    def extract_features(self, config: Dict) -> np.ndarray:
        """
        Extract 12-dimensional feature vector from config.
        
        Features:
        1. Privilege level (0-4)
        2. Is public (0-1)
        3. Sensitive resources count (0-10)
        4. Action count
        5. Resource count
        6. Principal count
        7. Has conditions (0-1)
        8. Sensitivity score (0-10)
        9. Resource depth (slashes count)
        10. Principal diversity (unique principals)
        11. K8s exposure (0-1)
        12. Volume sensitivity count
        """
        privilege_map = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}
        privilege_level = privilege_map.get(config.get('privilege_level', 'low'), 0)
        
        is_public = float(config.get('is_public', False))
        
        sensitive_resources = len(config.get('sensitive_resources', []))
        actions = len(config.get('actions', []))
        resources = len(config.get('resources', []))
        principals = len(config.get('principal', []))
        
        has_conditions = float(bool(config.get('conditions')))
        
        # Calculate sensitivity score
        text_content = str(config.get('raw_config', {}))
        sensitivity_keywords = ['secret', 'password', 'token', 'key', 'admin', 'private']
        sensitivity_score = sum(1 for kw in sensitivity_keywords if kw in text_content.lower())
        sensitivity_score = min(10, sensitivity_score)
        
        # Resource depth
        resource_list = config.get('resources', [])
        avg_depth = np.mean([str(r).count('/') for r in resource_list]) if resource_list else 0
        
        # Principal diversity
        principal_list = config.get('principal', [])
        principal_diversity = len(set(principal_list)) if principal_list else 0
        
        # K8s exposure
        k8s_exposure = float(config.get('network_exposure', {}).get('is_exposed', False))
        
        # Volume sensitivity
        volumes = config.get('volumes', [])
        volume_sensitivity = sum(1 for v in volumes if v.get('is_sensitive', False))
        
        features = np.array([
            privilege_level,           # 0
            is_public,                 # 1
            sensitive_resources,       # 2
            min(actions, 10),          # 3 (capped)
            min(resources, 10),        # 4 (capped)
            min(principals, 10),       # 5 (capped)
            has_conditions,            # 6
            sensitivity_score,         # 7
            min(avg_depth, 10),        # 8 (capped)
            min(principal_diversity, 10),  # 9 (capped)
            k8s_exposure,              # 10
            min(volume_sensitivity, 10)    # 11 (capped)
        ], dtype=np.float32)
        
        return features
    
    def extract_batch_features(self, configs: List[Dict]) -> np.ndarray:
        """Extract features from multiple configs."""
        features = [self.extract_features(cfg) for cfg in configs]
        return np.array(features, dtype=np.float32)
    
    def normalize(self, X: np.ndarray, fit: bool = False) -> np.ndarray:
        """Normalize features using z-score with numerical stability."""
        if fit:
            self.scaler_mean = X.mean(axis=0)
            # Add small epsilon to avoid division by zero
            self.scaler_std = X.std(axis=0) + 1e-8
        
        # Ensure scaler is set
        if self.scaler_mean is None or self.scaler_std is None:
            self.scaler_mean = np.zeros(X.shape[1])
            self.scaler_std = np.ones(X.shape[1])
        
        X_norm = (X - self.scaler_mean) / self.scaler_std
        
        # Clip extreme values for numerical stability
        X_norm = np.clip(X_norm, -10, 10)
        
        return X_norm
    
    def train(self, configs: List[Dict], epochs: int = 50, 
              learning_rate: float = 0.001, batch_size: int = 32) -> Dict[str, float]:
        """
        Train autoencoder on normal configurations.
        
        Args:
            configs: List of normal configuration dicts
            epochs: Training epochs
            learning_rate: Learning rate
            batch_size: Batch size
        
        Returns:
            Training history
        """
        # Extract and normalize features
        X = self.extract_batch_features(configs)
        X_norm = self.normalize(X, fit=True)
        
        # Create model
        self.model = SimpleAutoencoder(self.input_dim, self.encoding_dim).to(self.device)
        
        # Training setup
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
        
        # Convert to tensor
        X_tensor = torch.FloatTensor(X_norm).to(self.device)
        
        history = {'loss': []}
        
        # Training loop
        for epoch in range(epochs):
            epoch_loss = 0.0
            
            # Mini-batch training
            for i in range(0, len(X_tensor), batch_size):
                batch = X_tensor[i:i+batch_size]
                
                # Forward pass
                output = self.model(batch)
                loss = criterion(output, batch)
                
                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item()
            
            avg_loss = epoch_loss / max(1, len(X_tensor) // batch_size)
            history['loss'].append(avg_loss)
            
            if (epoch + 1) % 10 == 0:
                print(f'Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.6f}')
        
        # Calculate reconstruction errors for threshold
        self._update_threshold(X_norm)
        
        return history
    
    def _update_threshold(self, X_norm: np.ndarray):
        """Calculate anomaly threshold based on training data."""
        self.model.eval()
        
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X_norm).to(self.device)
            reconstructed = self.model(X_tensor)
            
            # Calculate MSE for each sample
            mse = ((X_tensor - reconstructed) ** 2).mean(axis=1)
            self.reconstruction_errors = mse.cpu().numpy()
        
        # Set threshold as 95th percentile of training errors
        # But ensure minimum threshold to avoid numerical issues
        percentile_95 = np.percentile(self.reconstruction_errors, 95)
        min_threshold = np.mean(self.reconstruction_errors) + 2 * np.std(self.reconstruction_errors)
        
        self.threshold = max(percentile_95, min_threshold, 0.001)
        
        print(f'Anomaly threshold set to: {self.threshold:.6f}')
        print(f'  Mean training error: {np.mean(self.reconstruction_errors):.6f}')
        print(f'  Std training error: {np.std(self.reconstruction_errors):.6f}')
    
    def predict(self, config: Dict) -> Dict[str, float]:
        """
        Detect anomaly in a single config.
        
        Returns:
            Dict with reconstruction_error and anomaly_score (0-10)
        """
        if self.model is None:
            return {
                'reconstruction_error': 0.0,
                'anomaly_score': 0.0,
                'is_anomaly': False,
                'error': 'Model not trained'
            }
        
        self.model.eval()
        
        with torch.no_grad():
            try:
                # Extract and normalize features
                features = self.extract_features(config)
                features_norm = self.normalize(np.array([features]))[0]
                
                # Get reconstruction
                X_tensor = torch.FloatTensor([features_norm]).to(self.device)
                reconstructed = self.model(X_tensor)
                
                # Calculate reconstruction error
                mse = ((X_tensor - reconstructed) ** 2).mean().item()
                
                # Handle numerical overflow
                if np.isnan(mse) or np.isinf(mse) or mse > 1e6:
                    # Likely very anomalous - set to max
                    mse = 1e6
                    anomaly_score = 10.0
                    is_anomaly = True
                else:
                    # Convert to anomaly score (0-10)
                    if self.threshold is not None and self.threshold > 0:
                        anomaly_score = min(10.0, (mse / self.threshold) * 5)
                    else:
                        anomaly_score = min(10.0, mse * 10)
                    
                    is_anomaly = mse > (self.threshold or 0.1)
                
                return {
                    'reconstruction_error': float(mse) if not np.isnan(mse) else 0.0,
                    'anomaly_score': anomaly_score,
                    'threshold': self.threshold,
                    'is_anomaly': bool(is_anomaly)
                }
            
            except Exception as e:
                return {
                    'reconstruction_error': 0.0,
                    'anomaly_score': 0.0,
                    'is_anomaly': False,
                    'error': str(e)
                }
    
    def predict_batch(self, configs: List[Dict]) -> List[Dict]:
        """Detect anomalies in multiple configs."""
        return [self.predict(cfg) for cfg in configs]
    
    def get_latent_representation(self, config: Dict) -> np.ndarray:
        """Get latent (compressed) representation of config."""
        if self.model is None:
            return np.zeros(self.encoding_dim)
        
        self.model.eval()
        
        with torch.no_grad():
            features = self.extract_features(config)
            features_norm = self.normalize(np.array([features]))[0]
            
            X_tensor = torch.FloatTensor([features_norm]).to(self.device)
            latent = self.model.encode(X_tensor)
        
        return latent.cpu().numpy()[0]
    
    def save_model(self, filepath: str):
        """Save trained model."""
        if self.model is None:
            return False
        
        checkpoint = {
            'model_state': self.model.state_dict(),
            'input_dim': self.input_dim,
            'encoding_dim': self.encoding_dim,
            'threshold': self.threshold,
            'scaler_mean': self.scaler_mean,
            'scaler_std': self.scaler_std
        }
        
        torch.save(checkpoint, filepath)
        print(f'Model saved to {filepath}')
        return True
    
    def load_model(self, filepath: str) -> bool:
        """Load trained model."""
        checkpoint = torch.load(filepath, map_location=self.device)
        
        self.input_dim = checkpoint['input_dim']
        self.encoding_dim = checkpoint['encoding_dim']
        self.threshold = checkpoint['threshold']
        self.scaler_mean = checkpoint['scaler_mean']
        self.scaler_std = checkpoint['scaler_std']
        
        self.model = SimpleAutoencoder(self.input_dim, self.encoding_dim).to(self.device)
        self.model.load_state_dict(checkpoint['model_state'])
        self.model.eval()
        
        print(f'Model loaded from {filepath}')
        return True
    
    def get_model_info(self) -> Dict:
        """Get information about the trained model."""
        if self.model is None:
            return {'status': 'not_trained'}
        
        total_params = sum(p.numel() for p in self.model.parameters())
        
        return {
            'status': 'trained',
            'input_dim': self.input_dim,
            'encoding_dim': self.encoding_dim,
            'total_parameters': total_params,
            'threshold': self.threshold,
            'mean_training_error': float(np.mean(self.reconstruction_errors)) if self.reconstruction_errors is not None else None,
            'max_training_error': float(np.max(self.reconstruction_errors)) if self.reconstruction_errors is not None else None
        }

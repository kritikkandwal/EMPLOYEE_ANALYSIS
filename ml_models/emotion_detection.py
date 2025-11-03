"""
Optional emotion detection module using webcam and computer vision
Note: This is an optional module that requires additional dependencies
"""
import logging
from typing import Dict, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

class EmotionDetector:
    """
    Detect emotions and focus levels using computer vision (optional module)
    """
    
    def __init__(self):
        self.is_initialized = False
        self.face_detector = None
        self.emotion_model = None
        
        try:
            self._initialize_detection()
        except ImportError as e:
            logger.warning(f"Emotion detection dependencies not available: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize emotion detector: {e}")
    
    def _initialize_detection(self):
        """
        Initialize face detection and emotion recognition models
        """
        try:
            # These imports are optional and only required if using emotion detection
            import cv2
            from deepface import DeepFace
            
            self.is_initialized = True
            logger.info("Emotion detection initialized successfully")
            
        except ImportError:
            logger.warning("Emotion detection dependencies not installed")
            self.is_initialized = False
    
    def detect_emotion_from_frame(self, frame: np.ndarray) -> Dict[str, float]:
        """
        Detect emotions from a video frame
        """
        if not self.is_initialized:
            return self._get_default_emotions()
        
        try:
            import cv2
            from deepface import DeepFace
            
            # Analyze frame for emotions
            result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
            
            if result and isinstance(result, list) and len(result) > 0:
                emotions = result[0]['emotion']
                return emotions
            
            return self._get_default_emotions()
            
        except Exception as e:
            logger.error(f"Emotion detection error: {e}")
            return self._get_default_emotions()
    
    def calculate_focus_score(self, emotions: Dict[str, float], 
                            head_pose: Optional[Tuple] = None) -> float:
        """
        Calculate focus score based on emotions and head pose
        """
        try:
            # Base focus score from emotions
            positive_emotions = emotions.get('happy', 0) + emotions.get('neutral', 0)
            negative_emotions = emotions.get('angry', 0) + emotions.get('sad', 0) + emotions.get('fear', 0)
            
            # Focus is higher with positive/neutral emotions and lower with negative emotions
            emotion_score = (positive_emotions - negative_emotions * 0.5) / 100
            
            # Adjust for head pose if available
            pose_adjustment = 0
            if head_pose:
                # Simple heuristic: looking straight ahead indicates focus
                yaw, pitch, roll = head_pose
                if abs(yaw) < 15 and abs(pitch) < 15:  # Within 15 degrees of center
                    pose_adjustment = 0.2
                else:
                    pose_adjustment = -0.1
            
            # Convert to 0-1 scale
            focus_score = max(0, min(1, 0.5 + emotion_score + pose_adjustment))
            
            return round(focus_score, 2)
            
        except Exception as e:
            logger.error(f"Focus score calculation error: {e}")
            return 0.7  # Default focus score
    
    def detect_engagement(self, emotions: Dict[str, float], 
                         duration: float) -> Dict[str, any]:
        """
        Detect engagement level based on emotional patterns over time
        """
        try:
            # Calculate engagement metrics
            neutral_level = emotions.get('neutral', 0)
            positive_level = emotions.get('happy', 0)
            negative_level = sum(emotions.get(emotion, 0) for emotion in ['angry', 'sad', 'fear'])
            
            # Engagement heuristic
            if neutral_level > 60:
                engagement = 'focused'
            elif positive_level > 40:
                engagement = 'engaged'
            elif negative_level > 40:
                engagement = 'distressed'
            else:
                engagement = 'neutral'
            
            # Calculate confidence
            confidence = min(1.0, duration / 300)  # Higher confidence with longer observation
            
            return {
                'level': engagement,
                'confidence': round(confidence, 2),
                'duration': duration,
                'emotion_breakdown': emotions
            }
            
        except Exception as e:
            logger.error(f"Engagement detection error: {e}")
            return {
                'level': 'neutral',
                'confidence': 0.5,
                'duration': duration,
                'emotion_breakdown': self._get_default_emotions()
            }
    
    def get_productivity_insights(self, engagement_data: list) -> Dict[str, any]:
        """
        Generate productivity insights from engagement data
        """
        try:
            if not engagement_data or len(engagement_data) < 5:
                return {
                    'insight': 'Insufficient data for analysis',
                    'recommendation': 'Continue tracking for personalized insights',
                    'confidence': 0.3
                }
            
            # Analyze engagement patterns
            focused_percentage = sum(1 for data in engagement_data if data['level'] == 'focused') / len(engagement_data)
            engaged_percentage = sum(1 for data in engagement_data if data['level'] == 'engaged') / len(engagement_data)
            distressed_percentage = sum(1 for data in engagement_data if data['level'] == 'distressed') / len(engagement_data)
            
            total_productive = focused_percentage + engaged_percentage
            
            # Generate insights based on patterns
            if total_productive > 0.7:
                insight = "Excellent engagement levels maintained"
                recommendation = "Continue your current work habits"
            elif total_productive > 0.5:
                insight = "Good engagement with room for improvement"
                recommendation = "Identify and minimize distractions"
            else:
                insight = "Lower than optimal engagement detected"
                recommendation = "Consider changing your work environment or taking breaks"
            
            if distressed_percentage > 0.3:
                insight += ". Higher stress levels noted."
                recommendation = "Incorporate stress-reduction techniques and regular breaks"
            
            confidence = min(0.9, len(engagement_data) / 20)  # Confidence based on data points
            
            return {
                'insight': insight,
                'recommendation': recommendation,
                'confidence': round(confidence, 2),
                'metrics': {
                    'focused_percentage': round(focused_percentage, 2),
                    'engaged_percentage': round(engaged_percentage, 2),
                    'distressed_percentage': round(distressed_percentage, 2),
                    'total_productive': round(total_productive, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Productivity insights error: {e}")
            return {
                'insight': 'Analysis unavailable',
                'recommendation': 'Continue tracking your work',
                'confidence': 0.1,
                'metrics': {}
            }
    
    def _get_default_emotions(self) -> Dict[str, float]:
        """Return default emotion distribution"""
        return {
            'angry': 0.0,
            'disgust': 0.0,
            'fear': 0.0,
            'happy': 0.0,
            'sad': 0.0,
            'surprise': 0.0,
            'neutral': 100.0
        }
    
    def is_available(self) -> bool:
        """Check if emotion detection is available"""
        return self.is_initialized
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if hasattr(self, 'face_detector'):
                self.face_detector = None
            if hasattr(self, 'emotion_model'):
                self.emotion_model = None
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

# Optional: Webcam integration for real-time emotion detection
class WebcamEmotionMonitor:
    """
    Real-time emotion monitoring using webcam (optional feature)
    """
    
    def __init__(self):
        self.is_running = False
        self.detector = EmotionDetector()
        self.current_emotions = {}
        self.engagement_history = []
    
    def start_monitoring(self, duration: int = 300):
        """Start real-time emotion monitoring"""
        if not self.detector.is_available():
            logger.warning("Emotion detection not available")
            return False
        
        try:
            import cv2
            
            self.is_running = True
            cap = cv2.VideoCapture(0)
            start_time = cv2.getTickCount()
            frame_count = 0
            
            while self.is_running:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Process frame every 10 frames to reduce load
                if frame_count % 10 == 0:
                    emotions = self.detector.detect_emotion_from_frame(frame)
                    self.current_emotions = emotions
                    
                    # Calculate focus and engagement
                    focus_score = self.detector.calculate_focus_score(emotions)
                    current_duration = (cv2.getTickCount() - start_time) / cv2.getTickFrequency()
                    
                    engagement = self.detector.detect_engagement(emotions, current_duration)
                    self.engagement_history.append(engagement)
                
                frame_count += 1
                
                # Check if duration exceeded
                if (cv2.getTickCount() - start_time) / cv2.getTickFrequency() > duration:
                    break
            
            cap.release()
            return True
            
        except Exception as e:
            logger.error(f"Webcam monitoring error: {e}")
            return False
    
    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.is_running = False
    
    def get_summary(self) -> Dict[str, any]:
        """Get monitoring session summary"""
        if not self.engagement_history:
            return {
                'status': 'no_data',
                'message': 'No emotion data collected'
            }
        
        insights = self.detector.get_productivity_insights(self.engagement_history)
        
        return {
            'status': 'completed',
            'session_duration': len(self.engagement_history),
            'insights': insights,
            'average_focus': np.mean([eng.get('confidence', 0) for eng in self.engagement_history]),
            'engagement_breakdown': {
                level: sum(1 for eng in self.engagement_history if eng['level'] == level) / len(self.engagement_history)
                for level in ['focused', 'engaged', 'neutral', 'distressed']
            }
        }
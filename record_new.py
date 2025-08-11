import datetime
import json
import uuid
from typing import Dict, Any, Optional
from enum import Enum

class ProfileType(Enum):
    CHILD = "child"
    PARENT = "parent" 
    ADMIN = "admin"

class Profile:
    """Profile class matching Flutter model"""
    
    def __init__(
        self,
        profile_id: str,
        name: str,
        profile_type: ProfileType = ProfileType.CHILD,
        auto_close: bool = True,
        daily_time_limit: int = 120,  # minutes
        bedtime: Optional[datetime.time] = None,
        allowed_days: list = None,
        avatar_url: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None
    ):
        self.id = profile_id
        self.name = name
        self.type = profile_type
        self.auto_close = auto_close
        self.daily_time_limit = daily_time_limit
        self.bedtime = bedtime
        self.allowed_days = allowed_days or [
            'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
        ]
        self.avatar_url = avatar_url
        self.created_at = datetime.datetime.now(datetime.timezone.utc)
        self.last_active = datetime.datetime.now(datetime.timezone.utc)
        self.settings = settings or {}
    
    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'Profile':
        """Create Profile from JSON data"""
        profile_type = ProfileType.CHILD
        if 'type' in data:
            try:
                profile_type = ProfileType(data['type'])
            except ValueError:
                profile_type = ProfileType.CHILD
        
        bedtime = None
        if 'bedtime' in data and data['bedtime']:
            bedtime = datetime.datetime.fromisoformat(data['bedtime']).time()
        
        created_at = datetime.datetime.now(datetime.timezone.utc)
        if 'created_at' in data and data['created_at']:
            created_at = datetime.datetime.fromisoformat(data['created_at'])
        
        last_active = datetime.datetime.now(datetime.timezone.utc)
        if 'last_active' in data and data['last_active']:
            last_active = datetime.datetime.fromisoformat(data['last_active'])
        
        profile = cls(
            profile_id=data.get('id', str(uuid.uuid4())),
            name=data.get('name', 'Untitled Profile'),
            profile_type=profile_type,
            auto_close=data.get('auto_close', True),
            daily_time_limit=data.get('daily_time_limit', 120),
            bedtime=bedtime,
            allowed_days=data.get('allowed_days', [
                'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
            ]),
            avatar_url=data.get('avatar_url'),
            settings=data.get('settings', {})
        )
        
        profile.created_at = created_at
        profile.last_active = last_active
        
        return profile
    
    def to_json(self) -> Dict[str, Any]:
        """Convert Profile to JSON"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type.value,
            'auto_close': self.auto_close,
            'daily_time_limit': self.daily_time_limit,
            'bedtime': self.bedtime.isoformat() if self.bedtime else None,
            'allowed_days': self.allowed_days,
            'avatar_url': self.avatar_url,
            'created_at': self.created_at.isoformat(),
            'last_active': self.last_active.isoformat(),
            'settings': self.settings
        }
    
    @property
    def formatted_time_limit(self) -> str:
        """Get formatted time limit string"""
        hours = self.daily_time_limit // 60
        minutes = self.daily_time_limit % 60
        
        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h"
        else:
            return f"{minutes}m"
    
    @property
    def is_admin(self) -> bool:
        return self.type == ProfileType.ADMIN
    
    @property 
    def is_parent(self) -> bool:
        return self.type == ProfileType.PARENT
    
    @property
    def is_child(self) -> bool:
        return self.type == ProfileType.CHILD

class SessionRecord:
    """Enhanced session record class matching Flutter model"""
    
    def __init__(
        self,
        child_profile: str = None,
        session_id: str = None,
        metadata: Dict[str, Any] = None
    ):
        self.session_id = session_id
        self.child_profile = child_profile
        self.time_start: Optional[datetime.datetime] = None
        self.time_end: Optional[datetime.datetime] = None
        self.duration: Optional[datetime.timedelta] = None
        self.metadata = metadata or {}
        
    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'SessionRecord':
        """Create SessionRecord from JSON data"""
        session = cls(
            child_profile=data.get('child_profile'),
            session_id=data.get('session_id'),
            metadata=data.get('metadata', {})
        )
        
        if 'time_start' in data and data['time_start']:
            session.time_start = datetime.datetime.fromisoformat(data['time_start'])
        
        if 'time_end' in data and data['time_end']:
            session.time_end = datetime.datetime.fromisoformat(data['time_end'])
        
        session._calculate_duration()
        return session
    
    def to_json(self) -> Dict[str, Any]:
        """Convert SessionRecord to JSON"""
        return {
            'time_start': self.time_start.isoformat() if self.time_start else None,
            'time_end': self.time_end.isoformat() if self.time_end else None,
            'child_profile': self.child_profile,
            'session_id': self.session_id,
            'duration_minutes': self.duration.total_seconds() // 60 if self.duration else None,
            'metadata': self.metadata
        }
    
    def start(self):
        """Start the session"""
        self.time_start = datetime.datetime.now(datetime.timezone.utc)
        if not self.session_id:
            self.session_id = f"{self.child_profile}_{int(self.time_start.timestamp() * 1000)}"
        self._calculate_duration()
    
    def end(self):
        """End the session"""
        self.time_end = datetime.datetime.now(datetime.timezone.utc)
        self._calculate_duration()
    
    def _calculate_duration(self):
        """Calculate session duration"""
        if self.time_start and self.time_end:
            self.duration = self.time_end - self.time_start
        elif self.time_start:
            self.duration = datetime.datetime.now(datetime.timezone.utc) - self.time_start
        else:
            self.duration = None
    
    @property
    def is_active(self) -> bool:
        """Check if session is currently active"""
        return self.time_start is not None and self.time_end is None
    
    @property
    def formatted_duration(self) -> str:
        """Get formatted duration string"""
        if not self.duration:
            return "0h 0m"
        
        total_seconds = int(self.duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        
        return f"{hours}h {minutes}m"
    
    @property
    def formatted_time_range(self) -> str:
        """Get formatted time range string"""
        if not self.time_start:
            return "Not started"
        
        start_local = self.time_start.astimezone()
        start_str = start_local.strftime("%H:%M")
        
        if not self.time_end:
            return f"{start_str} - Now"
        
        end_local = self.time_end.astimezone()
        end_str = end_local.strftime("%H:%M")
        
        return f"{start_str} - {end_str}"
    
    def convert_to_json(self) -> Dict[str, Any]:
        """Legacy method for backward compatibility"""
        return self.to_json()

# Legacy Record class for backward compatibility
class Record(SessionRecord):
    """Legacy Record class that extends SessionRecord for compatibility"""
    
    def __init__(self):
        super().__init__(child_profile="default_child")
        
    def convert_to_json(self) -> Dict[str, Any]:
        """Legacy JSON conversion method"""
        return {
            "time_start": self.time_start.isoformat() if self.time_start else None,
            "time_end": self.time_end.isoformat() if self.time_end else None,
            "session_id": self.session_id,
            "duration_seconds": self.duration.total_seconds() if self.duration else 0
        }

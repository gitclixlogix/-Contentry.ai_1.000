"""
SLO (Service Level Objectives) Service (ARCH-016)

Defines and tracks Service Level Objectives for critical operations.

Features:
- SLO definition and configuration
- Real-time SLO compliance tracking
- SLO violation alerting
- Historical SLO metrics
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from enum import Enum
from motor.motor_asyncio import AsyncIOMotorDatabase

from services.tracing_service import get_metrics_collector

logger = logging.getLogger(__name__)


# =============================================================================
# SLO DEFINITIONS
# =============================================================================

class SLOType(Enum):
    """Types of SLO metrics"""
    LATENCY = "latency"          # Response time requirements
    AVAILABILITY = "availability"  # Uptime requirements
    ERROR_RATE = "error_rate"     # Maximum error rate
    THROUGHPUT = "throughput"     # Minimum throughput


@dataclass
class SLODefinition:
    """
    Defines a Service Level Objective.
    
    Attributes:
        name: Unique name for this SLO
        operation: The operation this SLO applies to
        slo_type: Type of SLO (latency, availability, etc.)
        target: Target value (e.g., 99.5 for 99.5% availability)
        threshold: Warning threshold before violation
        unit: Unit of measurement (ms, percent, etc.)
        description: Human-readable description
        critical: Whether this is a critical SLO
    """
    name: str
    operation: str
    slo_type: SLOType
    target: float
    threshold: float
    unit: str
    description: str
    critical: bool = False


# =============================================================================
# PREDEFINED SLOs
# =============================================================================

DEFAULT_SLOS: List[SLODefinition] = [
    # Content Operations
    SLODefinition(
        name="content_analysis_latency_p95",
        operation="content_analysis",
        slo_type=SLOType.LATENCY,
        target=5000,  # 5 seconds
        threshold=4000,  # 4 seconds warning
        unit="ms",
        description="95% of content analysis requests complete within 5 seconds",
        critical=True
    ),
    SLODefinition(
        name="content_analysis_success_rate",
        operation="content_analysis",
        slo_type=SLOType.AVAILABILITY,
        target=99.0,  # 99% success rate
        threshold=98.0,  # 98% warning
        unit="percent",
        description="99% of content analysis requests succeed",
        critical=True
    ),
    
    # Social Posting
    SLODefinition(
        name="social_post_success_rate",
        operation="social_post",
        slo_type=SLOType.AVAILABILITY,
        target=99.5,  # 99.5% success rate
        threshold=99.0,  # 99% warning
        unit="percent",
        description="99.5% of social posts are successfully published",
        critical=True
    ),
    SLODefinition(
        name="social_post_latency_p95",
        operation="social_post",
        slo_type=SLOType.LATENCY,
        target=10000,  # 10 seconds
        threshold=8000,  # 8 seconds warning
        unit="ms",
        description="95% of social posts complete within 10 seconds",
        critical=False
    ),
    
    # Payment Processing
    SLODefinition(
        name="payment_success_rate",
        operation="payment_processing",
        slo_type=SLOType.AVAILABILITY,
        target=99.9,  # 99.9% success rate
        threshold=99.5,  # 99.5% warning
        unit="percent",
        description="99.9% of payment transactions processed successfully",
        critical=True
    ),
    SLODefinition(
        name="payment_latency_p99",
        operation="payment_processing",
        slo_type=SLOType.LATENCY,
        target=3000,  # 3 seconds
        threshold=2000,  # 2 seconds warning
        unit="ms",
        description="99% of payment transactions complete within 3 seconds",
        critical=True
    ),
    
    # Authentication
    SLODefinition(
        name="auth_latency_p99",
        operation="authentication",
        slo_type=SLOType.LATENCY,
        target=1000,  # 1 second
        threshold=500,  # 500ms warning
        unit="ms",
        description="99% of authentication requests complete within 1 second",
        critical=True
    ),
    SLODefinition(
        name="auth_success_rate",
        operation="authentication",
        slo_type=SLOType.AVAILABILITY,
        target=99.9,  # 99.9% success rate
        threshold=99.5,  # 99.5% warning
        unit="percent",
        description="99.9% of authentication requests succeed",
        critical=True
    ),
    
    # API Overall
    SLODefinition(
        name="api_latency_p95",
        operation="api_request",
        slo_type=SLOType.LATENCY,
        target=2000,  # 2 seconds
        threshold=1500,  # 1.5 seconds warning
        unit="ms",
        description="95% of API requests complete within 2 seconds",
        critical=False
    ),
    SLODefinition(
        name="api_error_rate",
        operation="api_request",
        slo_type=SLOType.ERROR_RATE,
        target=1.0,  # 1% max error rate
        threshold=0.5,  # 0.5% warning
        unit="percent",
        description="API error rate stays below 1%",
        critical=False
    ),
]


# =============================================================================
# SLO SERVICE
# =============================================================================

class SLOService:
    """
    Service for managing and tracking SLOs.
    
    Provides:
    - SLO compliance checking
    - SLO violation detection
    - Historical SLO metrics
    """
    
    def __init__(self, db: AsyncIOMotorDatabase = None):
        self.db = db
        self.slos: Dict[str, SLODefinition] = {slo.name: slo for slo in DEFAULT_SLOS}
    
    def set_db(self, db: AsyncIOMotorDatabase):
        """Set database instance."""
        self.db = db
    
    def add_slo(self, slo: SLODefinition):
        """Add a custom SLO definition."""
        self.slos[slo.name] = slo
    
    def get_slo(self, name: str) -> Optional[SLODefinition]:
        """Get an SLO by name."""
        return self.slos.get(name)
    
    def get_all_slos(self) -> List[SLODefinition]:
        """Get all SLO definitions."""
        return list(self.slos.values())
    
    def check_slo_compliance(self, slo_name: str) -> Dict[str, Any]:
        """
        Check compliance for a specific SLO.
        
        Returns:
            dict with compliance status and metrics
        """
        slo = self.slos.get(slo_name)
        if not slo:
            return {"error": f"SLO '{slo_name}' not found"}
        
        metrics = get_metrics_collector()
        stats = metrics.get_stats(slo.operation)
        
        # Calculate current value based on SLO type
        current_value = None
        is_compliant = True
        is_warning = False
        
        if slo.slo_type == SLOType.LATENCY:
            if slo.name.endswith('_p99'):
                current_value = stats.get('latency_p99_ms')
            elif slo.name.endswith('_p95'):
                current_value = stats.get('latency_p95_ms')
            else:
                current_value = stats.get('latency_p95_ms')  # Default to P95
            
            if current_value is not None:
                is_compliant = current_value <= slo.target
                is_warning = current_value > slo.threshold
                
        elif slo.slo_type == SLOType.AVAILABILITY:
            current_value = stats.get('success_rate_percent')
            if current_value is not None:
                is_compliant = current_value >= slo.target
                is_warning = current_value < slo.threshold
                
        elif slo.slo_type == SLOType.ERROR_RATE:
            success_rate = stats.get('success_rate_percent', 100)
            current_value = 100 - success_rate  # Error rate
            is_compliant = current_value <= slo.target
            is_warning = current_value > slo.threshold
        
        return {
            "slo_name": slo.name,
            "operation": slo.operation,
            "type": slo.slo_type.value,
            "target": slo.target,
            "threshold": slo.threshold,
            "current_value": current_value,
            "unit": slo.unit,
            "is_compliant": is_compliant,
            "is_warning": is_warning and is_compliant,
            "is_violation": not is_compliant,
            "critical": slo.critical,
            "description": slo.description,
            "sample_count": stats.get('sample_count', 0),
        }
    
    def check_all_slos(self) -> Dict[str, Any]:
        """
        Check compliance for all SLOs.
        
        Returns:
            dict with overall status and individual SLO results
        """
        results = [self.check_slo_compliance(name) for name in self.slos]
        
        violations = [r for r in results if r.get('is_violation')]
        warnings = [r for r in results if r.get('is_warning')]
        critical_violations = [r for r in violations if r.get('critical')]
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_slos": len(results),
            "compliant_count": len([r for r in results if r.get('is_compliant')]),
            "warning_count": len(warnings),
            "violation_count": len(violations),
            "critical_violation_count": len(critical_violations),
            "overall_status": "critical" if critical_violations else "warning" if violations or warnings else "healthy",
            "slos": results,
            "violations": violations,
            "warnings": warnings,
        }
    
    async def record_slo_snapshot(self):
        """
        Record current SLO status to database for historical tracking.
        """
        if self.db is None:
            return
        
        snapshot = self.check_all_slos()
        snapshot["recorded_at"] = datetime.now(timezone.utc).isoformat()
        
        try:
            await self.db.slo_snapshots.insert_one(snapshot)
        except Exception as e:
            logger.warning(f"Failed to record SLO snapshot: {e}")
    
    async def get_slo_history(
        self,
        slo_name: Optional[str] = None,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get historical SLO data.
        
        Args:
            slo_name: Optional specific SLO to get history for
            hours: Number of hours of history to retrieve
            
        Returns:
            List of historical snapshots
        """
        if self.db is None:
            return []
        
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        try:
            query = {"recorded_at": {"$gte": since.isoformat()}}
            
            snapshots = await self.db.slo_snapshots.find(
                query,
                {"_id": 0}
            ).sort("recorded_at", -1).limit(100).to_list(100)
            
            if slo_name:
                # Filter to specific SLO
                for snapshot in snapshots:
                    snapshot["slos"] = [
                        slo for slo in snapshot.get("slos", [])
                        if slo.get("slo_name") == slo_name
                    ]
            
            return snapshots
            
        except Exception as e:
            logger.warning(f"Failed to get SLO history: {e}")
            return []


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_slo_service: Optional[SLOService] = None


def get_slo_service() -> SLOService:
    """Get the global SLO service instance."""
    global _slo_service
    if _slo_service is None:
        _slo_service = SLOService()
    return _slo_service


def init_slo_service(db: AsyncIOMotorDatabase) -> SLOService:
    """Initialize the SLO service with database."""
    global _slo_service
    _slo_service = SLOService(db)
    return _slo_service

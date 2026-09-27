import time
from typing import List, Optional
from sqlalchemy.orm import Session
from app.modules.shadow.models import ShadowLogModel, ShadowConfigModel
from app.modules.shadow.schemas import ShadowStatusResponse, ShadowLogResponse
from app.modules.ai_categorizer.service_v2 import CategorizerV2

class ShadowService:
    def is_shadow_enabled(self, db: Session, feature_name: str) -> bool:
        cfg = db.query(ShadowConfigModel).filter(ShadowConfigModel.feature_name == feature_name).first()
        return cfg.shadow_enabled if cfg else False

    def enable_shadow_mode(
        self, db: Session, feature_name: str, shadow_version: str = "categorizer_v2"
    ) -> ShadowConfigModel:
        cfg = db.query(ShadowConfigModel).filter(ShadowConfigModel.feature_name == feature_name).first()
        if not cfg:
            cfg = ShadowConfigModel(
                feature_name=feature_name,
                shadow_enabled=True,
                shadow_version=shadow_version
            )
            db.add(cfg)
        else:
            cfg.shadow_enabled = True
            cfg.shadow_version = shadow_version
        
        db.commit()
        db.refresh(cfg)
        return cfg

    def disable_shadow_mode(self, db: Session, feature_name: str) -> ShadowConfigModel:
        cfg = db.query(ShadowConfigModel).filter(ShadowConfigModel.feature_name == feature_name).first()
        if not cfg:
            cfg = ShadowConfigModel(
                feature_name=feature_name,
                shadow_enabled=False,
                shadow_version="categorizer_v2"
            )
            db.add(cfg)
        else:
            cfg.shadow_enabled = False
        
        db.commit()
        db.refresh(cfg)
        return cfg

    def execute_shadow_evaluation(
        self,
        db: Session,
        feature_name: str,
        user_id: str,
        description: str,
        amount: float,
        prod_version: str,
        prod_category: str,
        prod_latency_ms: float
    ) -> Optional[ShadowLogModel]:
        if not self.is_shadow_enabled(db, feature_name):
            return None

        # Execute shadow version B
        start_time = time.perf_counter()
        shadow_service = CategorizerV2()
        shadow_res = shadow_service.categorize(description=description, amount=amount, is_experiment=True)
        shadow_latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        # Compare outputs
        category_matched = (prod_category.strip().lower() == shadow_res.category.strip().lower())

        log_entry = ShadowLogModel(
            feature_name=feature_name,
            user_id=user_id,
            description=description,
            amount=amount,
            prod_version=prod_version,
            prod_category=prod_category,
            prod_latency_ms=round(prod_latency_ms, 2),
            shadow_version=shadow_service.VERSION_NAME,
            shadow_category=shadow_res.category,
            shadow_latency_ms=shadow_latency_ms,
            category_matched=category_matched
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry

    def get_shadow_status(self, db: Session, feature_name: str) -> ShadowStatusResponse:
        cfg = db.query(ShadowConfigModel).filter(ShadowConfigModel.feature_name == feature_name).first()
        enabled = cfg.shadow_enabled if cfg else False
        shadow_version = cfg.shadow_version if cfg else "categorizer_v2"

        logs = db.query(ShadowLogModel).filter(ShadowLogModel.feature_name == feature_name).all()
        total = len(logs)

        if total == 0:
            return ShadowStatusResponse(
                feature_name=feature_name,
                shadow_enabled=enabled,
                shadow_version=shadow_version,
                total_shadow_evaluations=0,
                category_match_rate=0.0,
                avg_prod_latency_ms=0.0,
                avg_shadow_latency_ms=0.0
            )

        match_count = sum(1 for l in logs if l.category_matched)
        match_rate = round((match_count / total) * 100.0, 2)
        avg_prod_lat = round(sum(l.prod_latency_ms for l in logs) / total, 2)
        avg_shadow_lat = round(sum(l.shadow_latency_ms for l in logs) / total, 2)

        return ShadowStatusResponse(
            feature_name=feature_name,
            shadow_enabled=enabled,
            shadow_version=shadow_version,
            total_shadow_evaluations=total,
            category_match_rate=match_rate,
            avg_prod_latency_ms=avg_prod_lat,
            avg_shadow_latency_ms=avg_shadow_lat
        )

    def get_shadow_history(self, db: Session, feature_name: str) -> List[ShadowLogResponse]:
        records = db.query(ShadowLogModel).filter(
            ShadowLogModel.feature_name == feature_name
        ).order_by(ShadowLogModel.created_at.desc()).all()

        return [
            ShadowLogResponse(
                id=r.id,
                feature_name=r.feature_name,
                user_id=r.user_id,
                description=r.description,
                amount=r.amount,
                prod_version=r.prod_version,
                prod_category=r.prod_category,
                prod_latency_ms=r.prod_latency_ms,
                shadow_version=r.shadow_version,
                shadow_category=r.shadow_category,
                shadow_latency_ms=r.shadow_latency_ms,
                category_matched=r.category_matched,
                created_at=r.created_at
            )
            for r in records
        ]

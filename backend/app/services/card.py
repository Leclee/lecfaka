"""
卡密服务
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Card, Commodity
from ..core.exceptions import ValidationError, NotFoundError


class CardService:
    """卡密服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def import_cards(
        self,
        commodity_id: int,
        cards_text: str,
        race: Optional[str] = None,
        delimiter: str = "\n",
        owner_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        批量导入卡密
        
        Args:
            commodity_id: 商品ID
            cards_text: 卡密内容，每行一个
            race: 商品种类
            delimiter: 分隔符
            owner_id: 所属用户ID
            
        Returns:
            {"count": 导入数量, "duplicates": 重复数量}
        """
        # 验证商品
        result = await self.db.execute(
            select(Commodity).where(Commodity.id == commodity_id)
        )
        commodity = result.scalar_one_or_none()
        
        if not commodity:
            raise NotFoundError("商品不存在")
        
        # 解析卡密
        cards_list = [c.strip() for c in cards_text.split(delimiter) if c.strip()]
        
        if not cards_list:
            raise ValidationError("没有有效的卡密")
        
        # 去重
        unique_cards = list(set(cards_list))
        duplicates = len(cards_list) - len(unique_cards)
        
        # 检查已存在的卡密
        existing = await self.db.execute(
            select(Card.secret)
            .where(Card.commodity_id == commodity_id)
            .where(Card.secret.in_(unique_cards))
        )
        existing_secrets = set(row[0] for row in existing.fetchall())
        
        # 过滤已存在的
        new_cards = [c for c in unique_cards if c not in existing_secrets]
        duplicates += len(unique_cards) - len(new_cards)
        
        # 批量创建
        for secret in new_cards:
            card = Card(
                commodity_id=commodity_id,
                secret=secret,
                race=race,
                owner_id=owner_id if owner_id is not None else commodity.owner_id,
                status=0,
            )
            self.db.add(card)
        
        await self.db.flush()
        
        return {
            "count": len(new_cards),
            "duplicates": duplicates,
        }
    
    async def get_stock(
        self,
        commodity_id: int,
        race: Optional[str] = None,
    ) -> int:
        """获取库存数量"""
        query = (
            select(func.count())
            .select_from(Card)
            .where(Card.commodity_id == commodity_id)
            .where(Card.status == 0)
        )
        
        if race:
            query = query.where(Card.race == race)
        
        result = await self.db.execute(query)
        return result.scalar()
    
    async def get_draft_cards(
        self,
        commodity_id: int,
        race: Optional[str] = None,
        sku: Optional[Dict] = None,
        page: int = 1,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """获取可预选的卡密列表"""
        query = (
            select(Card)
            .where(Card.commodity_id == commodity_id)
            .where(Card.status == 0)
        )
        
        if race:
            query = query.where(Card.race == race)
        
        # TODO: SKU筛选
        
        # 统计总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # 分页
        query = query.offset((page - 1) * limit).limit(limit)
        result = await self.db.execute(query)
        cards = result.scalars().all()
        
        return {
            "total": total,
            "items": [
                {
                    "id": c.id,
                    "draft": c.draft,
                    "draft_premium": float(c.draft_premium),
                }
                for c in cards
            ],
        }
    
    async def update_card(
        self,
        card_id: int,
        secret: Optional[str] = None,
        draft: Optional[str] = None,
        draft_premium: Optional[float] = None,
        race: Optional[str] = None,
        note: Optional[str] = None,
    ) -> Card:
        """更新卡密"""
        result = await self.db.execute(
            select(Card).where(Card.id == card_id)
        )
        card = result.scalar_one_or_none()
        
        if not card:
            raise NotFoundError("卡密不存在")
        
        if card.status == 1:
            raise ValidationError("已售出的卡密不能修改")
        
        if secret is not None:
            card.secret = secret
        if draft is not None:
            card.draft = draft
        if draft_premium is not None:
            card.draft_premium = draft_premium
        if race is not None:
            card.race = race
        if note is not None:
            card.note = note
        
        return card
    
    async def delete_cards(
        self,
        card_ids: List[int],
    ) -> int:
        """批量删除卡密（仅未售出的）"""
        result = await self.db.execute(
            delete(Card)
            .where(Card.id.in_(card_ids))
            .where(Card.status == 0)
        )
        return result.rowcount
    
    async def clear_unsold(
        self,
        commodity_id: int,
        race: Optional[str] = None,
    ) -> int:
        """清空未售出的卡密"""
        query = (
            delete(Card)
            .where(Card.commodity_id == commodity_id)
            .where(Card.status == 0)
        )
        
        if race:
            query = query.where(Card.race == race)
        
        result = await self.db.execute(query)
        return result.rowcount

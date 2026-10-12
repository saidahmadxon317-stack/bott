"""
Supabase Database Access Layer for Ulashamiz Telegram Bot
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from supabase import create_client, Client
from app.config import settings

_supabase_client: Optional[Client] = None

def get_supabase() -> Client:
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
        )
    return _supabase_client


class DBService:
    @staticmethod
    async def get_or_create_user_profile(
        telegram_id: int,
        username: Optional[str] = None,
        full_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetch or create profile for Telegram user"""
        client = get_supabase()
        try:
            res = client.table("profiles").select("*").eq("telegram_id", telegram_id).execute()
            if res.data and len(res.data) > 0:
                profile = res.data[0]
                updates = {}
                if username and profile.get("telegram_username") != username:
                    updates["telegram_username"] = username
                if full_name and not profile.get("full_name"):
                    updates["full_name"] = full_name
                if updates:
                    client.table("profiles").update(updates).eq("id", profile["id"]).execute()
                return profile

            import uuid
            profile_id = str(uuid.uuid4())
            new_profile = {
                "id": profile_id,
                "telegram_id": telegram_id,
                "telegram_username": username,
                "full_name": full_name or f"Telegram foydalanuvchisi #{telegram_id}",
                "role": "user",
                "is_suspended": False
            }
            create_res = client.table("profiles").insert(new_profile).execute()
            if create_res.data:
                return create_res.data[0]
            return new_profile
        except Exception as e:
            print(f"Error in get_or_create_user_profile: {e}")
            return {
                "id": str(telegram_id),
                "telegram_id": telegram_id,
                "telegram_username": username,
                "full_name": full_name or "Foydalanuvchi"
            }

    @staticmethod
    async def update_user_profile(
        telegram_id: int,
        full_name: str,
        phone: str,
        address: str,
        username: Optional[str] = None
    ) -> bool:
        """Update user profile with registration info"""
        client = get_supabase()
        try:
            res = client.table("profiles").select("id").eq("telegram_id", telegram_id).execute()
            if not res.data:
                return False
            profile_id = res.data[0]["id"]
            updates = {
                "full_name": full_name,
                "phone": phone,
                "address": address,
            }
            if username:
                updates["telegram_username"] = username
            client.table("profiles").update(updates).eq("id", profile_id).execute()
            return True
        except Exception as e:
            print(f"Error updating user profile: {e}")
            return False

    @staticmethod
    async def count_user_daily_requests(user_id: str) -> int:
        """Count how many item requests the user sent today (UTC)"""
        client = get_supabase()
        try:
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            res = client.table("item_requests") \
                .select("id") \
                .eq("requester_id", user_id) \
                .gte("created_at", today_start) \
                .execute()
            return len(res.data or [])
        except Exception as e:
            print(f"Error counting daily requests: {e}")
            return 0

    @staticmethod
    async def get_categories() -> List[Dict[str, Any]]:
        client = get_supabase()
        try:
            res = client.table("categories").select("*").eq("is_active", True).order("sort_order").execute()
            return res.data or []
        except Exception as e:
            print(f"Error fetching categories: {e}")
            return []

    @staticmethod
    async def get_regions() -> List[Dict[str, Any]]:
        client = get_supabase()
        try:
            res = client.table("regions").select("*").order("sort_order").execute()
            return res.data or []
        except Exception as e:
            print(f"Error fetching regions: {e}")
            return []

    @staticmethod
    async def get_districts(region_id: str) -> List[Dict[str, Any]]:
        client = get_supabase()
        try:
            res = client.table("districts").select("*").eq("region_id", region_id).order("sort_order").execute()
            return res.data or []
        except Exception as e:
            print(f"Error fetching districts: {e}")
            return []

    @staticmethod
    async def upload_image_to_storage(file_bytes: bytes, filename: str) -> Optional[str]:
        """Upload image to Supabase item-photos bucket and return public URL"""
        client = get_supabase()
        try:
            client.storage.from_("item-photos").upload(
                path=filename,
                file=file_bytes,
                file_options={"content-type": "image/jpeg"}
            )
            public_url = client.storage.from_("item-photos").get_public_url(filename)
            return public_url
        except Exception as e:
            print(f"Error uploading image to storage: {e}")
            return None

    @staticmethod
    async def create_listing(
        owner_id: str,
        title: str,
        description: str,
        category_id: str,
        condition: str,
        region_id: str,
        district_id: str,
        neighborhood: Optional[str] = None,
        image_url: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        client = get_supabase()
        try:
            data = {
                "owner_id": owner_id,
                "title": title,
                "description": description,
                "category_id": category_id,
                "condition": condition,
                "region_id": region_id,
                "district_id": district_id,
                "neighborhood": neighborhood,
                "status": "approved",  # direct approval or pending for moderation
                "view_count": 0
            }
            res = client.table("listings").insert(data).execute()
            if not res.data:
                return None
            listing = res.data[0]

            if image_url:
                client.table("listing_images").insert({
                    "listing_id": listing["id"],
                    "storage_path": "telegram_uploads",
                    "url": image_url,
                    "is_primary": True,
                    "sort_order": 0
                }).execute()

            return listing
        except Exception as e:
            print(f"Error creating listing: {e}")
            return None

    @staticmethod
    async def search_listings(
        query: Optional[str] = None,
        category_id: Optional[str] = None,
        region_id: Optional[str] = None,
        district_id: Optional[str] = None,
        limit: int = 5,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        client = get_supabase()
        try:
            req = client.table("listings").select(
                "*, categories(name_uz), regions(name_uz), districts(name_uz), listing_images(url, is_primary), profiles(full_name, telegram_id, telegram_username)"
            ).eq("status", "approved")

            if category_id:
                req = req.eq("category_id", category_id)
            if region_id:
                req = req.eq("region_id", region_id)
            if district_id:
                req = req.eq("district_id", district_id)
            if query:
                req = req.ilike("title", f"%{query}%")

            res = req.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
            return res.data or []
        except Exception as e:
            print(f"Error searching listings: {e}")
            return []

    @staticmethod
    async def get_listing_by_id(listing_id: str) -> Optional[Dict[str, Any]]:
        client = get_supabase()
        try:
            res = client.table("listings").select(
                "*, categories(name_uz), regions(name_uz), districts(name_uz), listing_images(url), profiles(full_name, telegram_id, telegram_username, phone)"
            ).eq("id", listing_id).execute()
            if res.data:
                return res.data[0]
            return None
        except Exception as e:
            print(f"Error fetching listing {listing_id}: {e}")
            return None

    @staticmethod
    async def get_user_listings(owner_id: str) -> List[Dict[str, Any]]:
        client = get_supabase()
        try:
            res = client.table("listings").select(
                "*, categories(name_uz), districts(name_uz), listing_images(url)"
            ).eq("owner_id", owner_id).neq("status", "archived").order("created_at", desc=True).execute()
            return res.data or []
        except Exception as e:
            print(f"Error fetching user listings: {e}")
            return []

    @staticmethod
    async def mark_listing_given_away(listing_id: str, owner_id: str) -> bool:
        client = get_supabase()
        try:
            res = client.table("listings").update({"status": "given_away"}).eq("id", listing_id).eq("owner_id", owner_id).execute()
            return bool(res.data)
        except Exception as e:
            print(f"Error marking listing as given away: {e}")
            return False

    @staticmethod
    async def delete_listing(listing_id: str, owner_id: str) -> bool:
        client = get_supabase()
        try:
            res = client.table("listings").update({"status": "archived"}).eq("id", listing_id).eq("owner_id", owner_id).execute()
            return bool(res.data)
        except Exception as e:
            print(f"Error deleting listing: {e}")
            return False

    @staticmethod
    async def toggle_favorite(user_id: str, listing_id: str) -> bool:
        """Returns True if added, False if removed"""
        client = get_supabase()
        try:
            existing = client.table("favorites").select("*").eq("user_id", user_id).eq("listing_id", listing_id).execute()
            if existing.data and len(existing.data) > 0:
                client.table("favorites").delete().eq("user_id", user_id).eq("listing_id", listing_id).execute()
                return False
            else:
                client.table("favorites").insert({"user_id": user_id, "listing_id": listing_id}).execute()
                return True
        except Exception as e:
            print(f"Error toggling favorite: {e}")
            return False

    @staticmethod
    async def get_user_favorites(user_id: str) -> List[Dict[str, Any]]:
        client = get_supabase()
        try:
            res = client.table("favorites").select(
                "listing_id, listings(*, categories(name_uz), districts(name_uz), listing_images(url))"
            ).eq("user_id", user_id).execute()
            items = []
            for item in res.data or []:
                if item.get("listings") and item["listings"].get("status") == "approved":
                    items.append(item["listings"])
            return items
        except Exception as e:
            print(f"Error fetching favorites: {e}")
            return []

    @staticmethod
    async def create_item_request(
        listing_id: str,
        requester_id: str,
        message: str,
        phone: Optional[str] = None
    ) -> Dict[str, Any]:
        client = get_supabase()
        try:
            # Check duplicate active request
            existing = client.table("item_requests").select("*").eq("listing_id", listing_id).eq("requester_id", requester_id).execute()
            if existing.data and len(existing.data) > 0:
                return {"success": False, "error": "Siz bu e'lon uchun allaqachon so'rov yuborgansiz"}

            res = client.table("item_requests").insert({
                "listing_id": listing_id,
                "requester_id": requester_id,
                "message": message,
                "contact_phone": phone,
                "status": "pending"
            }).execute()

            if res.data:
                return {"success": True, "data": res.data[0]}
            return {"success": False, "error": "So'rov yaratishda xatolik"}
        except Exception as e:
            print(f"Error creating item request: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def accept_request_and_close_listing(
        request_id: str,
        owner_id: str,
    ) -> Dict[str, Any]:
        """Accept request, mark listing as given_away, return requester's telegram_id"""
        client = get_supabase()
        try:
            req_data = client.table("item_requests").select(
                "*, listings(owner_id, title, status), profiles(telegram_id, full_name)"
            ).eq("id", request_id).execute()

            if not req_data.data:
                return {"success": False}

            req = req_data.data[0]
            listing_info = req.get("listings", {})

            if listing_info.get("owner_id") != owner_id:
                return {"success": False}

            # Mark request accepted
            client.table("item_requests").update({"status": "accepted"}).eq("id", request_id).execute()

            # Close listing
            listing_id = req.get("listing_id")
            client.table("listings").update({"status": "given_away"}).eq("id", listing_id).execute()

            requester_profile = req.get("profiles", {})
            return {
                "success": True,
                "requester_telegram_id": requester_profile.get("telegram_id"),
                "listing_title": listing_info.get("title", "buyum"),
            }
        except Exception as e:
            print(f"Error accepting request: {e}")
            return {"success": False}

    @staticmethod
    async def reject_request(
        request_id: str,
        owner_id: str,
    ) -> Dict[str, Any]:
        """Reject request and return requester telegram_id for notification"""
        client = get_supabase()
        try:
            req_data = client.table("item_requests").select(
                "*, listings(owner_id, title), profiles(telegram_id)"
            ).eq("id", request_id).execute()

            if not req_data.data:
                return {"success": False}

            req = req_data.data[0]
            listing_info = req.get("listings", {})

            if listing_info.get("owner_id") != owner_id:
                return {"success": False}

            client.table("item_requests").update({"status": "rejected"}).eq("id", request_id).execute()

            requester_profile = req.get("profiles", {})
            return {
                "success": True,
                "requester_telegram_id": requester_profile.get("telegram_id"),
                "listing_title": listing_info.get("title", "buyum"),
            }
        except Exception as e:
            print(f"Error rejecting request: {e}")
            return {"success": False}

    @staticmethod
    async def update_listing_field(
        listing_id: str,
        owner_id: str,
        field: str,
        value: str
    ) -> bool:
        """Update a single field of a listing (only by owner)"""
        client = get_supabase()
        allowed_fields = {"title", "description", "neighborhood"}
        if field not in allowed_fields:
            return False
        try:
            res = client.table("listings").update({field: value}) \
                .eq("id", listing_id).eq("owner_id", owner_id).execute()
            return bool(res.data)
        except Exception as e:
            print(f"Error updating listing field: {e}")
            return False

    @staticmethod
    async def update_request_status(
        request_id: str,
        owner_id: str,
        new_status: str,
        response_note: Optional[str] = None
    ) -> bool:
        client = get_supabase()
        try:
            req_data = client.table("item_requests").select("*, listings(owner_id)").eq("id", request_id).execute()
            if not req_data.data:
                return False
            if req_data.data[0].get("listings", {}).get("owner_id") != owner_id:
                return False
            updates = {"status": new_status}
            if response_note:
                updates["owner_response_note"] = response_note
            res = client.table("item_requests").update(updates).eq("id", request_id).execute()
            return bool(res.data)
        except Exception as e:
            print(f"Error updating request status: {e}")
            return False

    @staticmethod
    async def create_account_link_token(telegram_id: int, telegram_username: Optional[str]) -> str:
        """Generates a secure 6-digit or random hex token, stores its SHA-256 hash, returns plain token"""
        client = get_supabase()
        # Generate 6-digit easy code for user to type on web
        raw_code = f"{secrets.randbelow(900000) + 100000}"
        token_hash = hashlib.sha256(raw_code.encode("utf-8")).hexdigest()
        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()

        # Invalidate old unused tokens for this telegram_id
        try:
            client.table("account_link_tokens").update({"is_used": True}).eq("telegram_id", telegram_id).execute()
        except Exception:
            pass

        client.table("account_link_tokens").insert({
            "token_hash": token_hash,
            "telegram_id": telegram_id,
            "telegram_username": telegram_username,
            "expires_at": expires_at,
            "is_used": False
        }).execute()

        return raw_code

    @staticmethod
    async def submit_report(reporter_id: str, listing_id: str, reason: str, details: Optional[str] = None) -> bool:
        client = get_supabase()
        try:
            res = client.table("reports").insert({
                "reporter_id": reporter_id,
                "listing_id": listing_id,
                "reason": reason,
                "details": details,
                "status": "pending"
            }).execute()
            return bool(res.data)
        except Exception as e:
            print(f"Error submitting report: {e}")
            return False

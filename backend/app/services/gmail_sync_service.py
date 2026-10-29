import datetime
import email.utils
import json
import re
import httpx
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.app.core.config import settings
from backend.app.models.entities import User, EmailEvent, EmailAnalysis, AuditLog
from backend.app.ml.email_classifier import email_classifier

async def _refresh_gmail_token(user: User, client: httpx.AsyncClient) -> bool:
    """Refreshes the OAuth 2.0 access token using the stored refresh token."""
    if not user.gmail_refresh_token:
        return False
    try:
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "refresh_token": user.gmail_refresh_token,
            "grant_type": "refresh_token"
        }
        resp = await client.post(token_url, data=data)
        if resp.status_code == 200:
            tokens = resp.json()
            new_token = tokens.get("access_token")
            if new_token:
                user.gmail_access_token = new_token
                return True
        return False
    except Exception as e:
        print(f"[Gmail Token Refresh Error]: {e}")
        return False

async def sync_user_gmail(user: User, db: Session, max_results: int = 30) -> List[EmailEvent]:
    """
    Fetches real emails from user's live Gmail inbox,
    evaluates each email through the AI Phishing Detector,
    and saves them in the database tagged with user.email and data_source='gmail'.
    """
    if not user.gmail_access_token:
        raise HTTPException(
            status_code=400,
            detail="No Gmail access token found for this account. Please click 'Grant Gmail Permission' to connect your inbox."
        )

    headers = {"Authorization": f"Bearer {user.gmail_access_token}"}
    list_url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults={max_results}"

    synced_emails = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(list_url, headers=headers)
        if resp.status_code == 401:
            refreshed = await _refresh_gmail_token(user, client)
            if refreshed:
                headers = {"Authorization": f"Bearer {user.gmail_access_token}"}
                resp = await client.get(list_url, headers=headers)
            else:
                raise HTTPException(
                    status_code=401,
                    detail="Gmail session expired. Please log out and sign in with Google again to refresh permissions."
                )

        if resp.status_code != 200:
            error_data = resp.text
            print(f"[Gmail Sync Error] Status {resp.status_code}: {error_data}")
            
            # Check for insufficient permissions
            if "ACCESS_TOKEN_SCOPE_INSUFFICIENT" in error_data or "insufficient authentication scopes" in error_data:
                raise HTTPException(
                    status_code=403,
                    detail="Permission Denied: Your Google login session did not grant Gmail read access. Please click 'Grant Gmail Permission' to allow reading your emails."
                )
            # Check for Gmail API disabled in Google Cloud Console
            elif "has not been used in project" in error_data or "is disabled" in error_data or "SERVICE_DISABLED" in error_data:
                raise HTTPException(
                    status_code=403,
                    detail="Gmail API is NOT enabled in your Google Cloud Project! Open Google Cloud Console -> APIs & Services -> Library -> Search 'Gmail API' and click 'Enable'."
                )
            else:
                try:
                    err_json = resp.json()
                    err_msg = err_json.get("error", {}).get("message", error_data)
                except Exception:
                    err_msg = error_data
                raise HTTPException(
                    status_code=resp.status_code,
                    detail=f"Gmail API error ({resp.status_code}): {err_msg}"
                )

        data = resp.json()
        msg_list = data.get("messages", [])
        
        # If no messages returned in primary list, try querying inbox specifically
        if not msg_list:
            fb_url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults={max_results}&q=in:inbox"
            fb_resp = await client.get(fb_url, headers=headers)
            if fb_resp.status_code == 200:
                msg_list = fb_resp.json().get("messages", [])

        if not msg_list:
            print(f"[Gmail Sync] No messages returned from Gmail API for {user.email}")
            return []

        print(f"[Gmail Sync] Fetching and evaluating {len(msg_list)} real Gmail messages for {user.email}...")

        for item in msg_list:
            msg_id = item["id"]
            db_email_id = f"GMAIL-{msg_id}"
            
            # Use metadata query with snippet for rapid, lightweight retrieval without heavy attachments
            detail_url = (
                f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}"
                f"?format=metadata&metadataHeaders=Subject&metadataHeaders=From&metadataHeaders=Date"
                f"&metadataHeaders=Authentication-Results&metadataHeaders=Received-SPF"
            )
            m_resp = await client.get(detail_url, headers=headers)
            if m_resp.status_code != 200:
                continue

            m_data = m_resp.json()
            snippet = m_data.get("snippet", "")
            raw_headers = m_data.get("payload", {}).get("headers", [])
            headers_dict = {h["name"].lower(): h["value"] for h in raw_headers}

            subject = headers_dict.get("subject", "No Subject")
            from_header = headers_dict.get("from", "Unknown Sender")
            
            # Parse sender details
            sender_name = from_header
            sender_email = user.email
            email_match = re.search(r'<([^>]+)>', from_header)
            if email_match:
                sender_email = email_match.group(1).strip()
                name_match = from_header.split("<")[0].strip().strip('"').strip("'")
                if name_match:
                    sender_name = name_match
                else:
                    sender_name = sender_email.split("@")[0]
            else:
                bare_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', from_header)
                if bare_match:
                    sender_email = bare_match.group(0).strip()
                    sender_name = sender_email.split("@")[0]

            sender_domain = sender_email.split("@")[1] if "@" in sender_email else "gmail.com"
            reply_to = headers_dict.get("reply-to", sender_email)

            # Date parsing
            date_header = headers_dict.get("date")
            internal_date_ms = m_data.get("internalDate")
            msg_timestamp = datetime.datetime.utcnow()
            if internal_date_ms:
                try:
                    msg_timestamp = datetime.datetime.utcfromtimestamp(int(internal_date_ms) / 1000.0)
                except Exception:
                    pass
            elif date_header:
                try:
                    parsed_tuple = email.utils.parsedate_to_datetime(date_header)
                    msg_timestamp = parsed_tuple.replace(tzinfo=None)
                except Exception:
                    pass

            body_text = snippet or "No preview content available."

            # URL extraction
            found_urls = re.findall(r'https?://[^\s<>"\'\)]+', body_text)
            urls_str = " | ".join(list(dict.fromkeys(found_urls))[:5])
            link_count = len(found_urls)

            # Authentication checks
            auth_results = headers_dict.get("authentication-results", "").lower()
            received_spf = headers_dict.get("received-spf", "").lower()

            spf_result = "pass" if ("spf=pass" in auth_results or "pass" in received_spf) else ("fail" if "spf=fail" in auth_results else "none")
            dkim_result = "pass" if "dkim=pass" in auth_results else ("fail" if "dkim=fail" in auth_results else "none")
            dmarc_result = "pass" if "dmarc=pass" in auth_results else ("fail" if "dmarc=fail" in auth_results else "none")

            # Run ML Model & Explainable Risk Engine
            model_input = {
                "email_subject": subject,
                "email_body": body_text,
                "sender_name": sender_name,
                "sender_email": sender_email,
                "sender_domain": sender_domain,
                "reply_to": reply_to,
                "urls": urls_str,
                "link_count": link_count,
                "has_attachment": 0,
                "attachment_type": "none",
                "spf_result": spf_result,
                "dkim_result": dkim_result,
                "dmarc_result": dmarc_result,
                "display_name_mismatch": 1 if any(kw in sender_name.lower() for kw in ["security", "support", "helpdesk", "billing", "verify"]) and sender_domain not in ["google.com", "microsoft.com", "apple.com"] else 0,
                "domain_age_category": "established_>1y"
            }

            analysis_result = email_classifier.analyze_email(model_input)

            # Check if record already exists in SQLite
            existing_event = db.query(EmailEvent).filter(EmailEvent.email_id == db_email_id).first()
            if existing_event:
                existing_event.email_subject = subject
                existing_event.email_body = body_text
                existing_event.sender_name = sender_name
                existing_event.sender_email = sender_email
                existing_event.sender_domain = sender_domain
                existing_event.timestamp = msg_timestamp
                existing_event.urls = urls_str
                existing_event.link_count = link_count
                existing_event.spf_result = spf_result
                existing_event.dkim_result = dkim_result
                existing_event.dmarc_result = dmarc_result
                existing_event.data_source = "gmail"
                ee = existing_event

                if existing_event.analysis:
                    existing_event.analysis.predicted_class = analysis_result["predicted_class"]
                    existing_event.analysis.phishing_probability = analysis_result["phishing_probability"]
                    existing_event.analysis.risk_score = analysis_result["risk_score"]
                    existing_event.analysis.severity = analysis_result["severity"]
                    existing_event.analysis.reasons = json.dumps(analysis_result["reasons"])
                    existing_event.analysis.recommended_actions = json.dumps(analysis_result["recommended_actions"])
                    existing_event.analysis.content_risk = analysis_result["content_risk"]
                    existing_event.analysis.url_risk = analysis_result["url_risk"]
                    existing_event.analysis.sender_risk = analysis_result["sender_risk"]
            else:
                ee = EmailEvent(
                    email_id=db_email_id,
                    user_id=user.email,
                    timestamp=msg_timestamp,
                    sender_name=sender_name,
                    sender_email=sender_email,
                    sender_domain=sender_domain,
                    reply_to=reply_to,
                    email_subject=subject,
                    email_body=body_text,
                    urls=urls_str,
                    link_count=link_count,
                    has_attachment=0,
                    attachment_type="none",
                    spf_result=spf_result,
                    dkim_result=dkim_result,
                    dmarc_result=dmarc_result,
                    display_name_mismatch=model_input["display_name_mismatch"],
                    domain_age_category="established_>1y",
                    label=analysis_result["predicted_class"],
                    data_source="gmail"
                )
                db.add(ee)

                ea = EmailAnalysis(
                    email_id=db_email_id,
                    predicted_class=analysis_result["predicted_class"],
                    phishing_probability=analysis_result["phishing_probability"],
                    risk_score=analysis_result["risk_score"],
                    severity=analysis_result["severity"],
                    reasons=json.dumps(analysis_result["reasons"]),
                    recommended_actions=json.dumps(analysis_result["recommended_actions"]),
                    content_risk=analysis_result["content_risk"],
                    url_risk=analysis_result["url_risk"],
                    sender_risk=analysis_result["sender_risk"],
                    model_version=analysis_result["model_version"]
                )
                db.add(ea)

            synced_emails.append(ee)

        # Audit log entry
        audit = AuditLog(
            action="GMAIL_INBOX_AI_SYNC",
            target_type="mailbox",
            target_id=user.email,
            actor=user.email,
            details=json.dumps({
                "count": len(synced_emails),
                "source": "gmail.readonly",
                "timestamp": datetime.datetime.utcnow().isoformat()
            }),
            is_simulated=False
        )
        db.add(audit)
        db.commit()
        print(f"[Gmail Sync] Successfully analyzed and saved {len(synced_emails)} real emails for {user.email}.")

    return synced_emails

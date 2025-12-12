import logging

from ldap3 import ALL, SUBTREE, Connection, Server

from app.core.config import settings

logger = logging.getLogger(__name__)


def authenticate(username: str, password: str) -> dict | None:
    if not settings.LDAP_ENABLED:
        logger.error("LDAP is disabled")
        return None

    if not settings.ldap_configured:
        logger.error("LDAP is not configured")
        return None

    try:
        server = Server(settings.LDAP_HOST, port=settings.LDAP_PORT, get_info=ALL)

        # Bind with service account if provided, otherwise anonymous
        if settings.LDAP_BIND_DN and settings.LDAP_BIND_PASSWORD:
            conn = Connection(
                server,
                user=settings.LDAP_BIND_DN,
                password=settings.LDAP_BIND_PASSWORD,
                auto_bind=True,
            )
        else:
            conn = Connection(server, auto_bind=True)

        # Search for the user
        conn.search(
            search_base=settings.LDAP_BASE_DN,
            search_filter=settings.LDAP_USER_FILTER.format(username=username),
            search_scope=SUBTREE,
            attributes=[
                settings.LDAP_USERNAME_ATTRIBUTE,
                settings.LDAP_EMAIL_ATTRIBUTE,
                settings.LDAP_FULLNAME_ATTRIBUTE,
            ],
        )

        if not conn.entries:
            logger.info(f"LDAP user not found: {username}")
            return None

        user_entry = conn.entries[0]
        user_dn = user_entry.entry_dn

        # Verify password by binding as the user
        user_conn = Connection(server, user=user_dn, password=password)
        if not user_conn.bind():
            logger.info(f"LDAP password verification failed for user: {username}")
            return None

        # Extract user info
        email = (
            str(user_entry[settings.LDAP_EMAIL_ATTRIBUTE])
            if settings.LDAP_EMAIL_ATTRIBUTE in user_entry
            else None
        )
        full_name = (
            str(user_entry[settings.LDAP_FULLNAME_ATTRIBUTE])
            if settings.LDAP_FULLNAME_ATTRIBUTE in user_entry
            else None
        )

        return {"username": username, "email": email, "full_name": full_name}

    except Exception as e:
        logger.error(f"LDAP authentication error: {e}")
        return None

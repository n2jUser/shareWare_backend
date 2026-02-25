import stripe
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

def init_stripe() -> bool:
    """
    Initialise Stripe. Retourne True si OK, False si non configuré.
    Ne bloque pas le démarrage — les endpoints Stripe retourneront 503.
    """
    if not settings.STRIPE_SECRET_KEY:
        logger.warning("⚠️  STRIPE_SECRET_KEY absent — paiements désactivés")
        return False

    stripe.api_key = settings.STRIPE_SECRET_KEY
    stripe.max_network_retries = 2

    try:
        stripe.Balance.retrieve()
        logger.info("✅ Stripe connecté")
        return True
    except stripe.AuthenticationError:
        logger.error("❌ Clé Stripe invalide")
        return False
    except Exception as e:
        logger.error(f"❌ Erreur Stripe au démarrage : {e}")
        return False
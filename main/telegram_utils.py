"""
Telegram notification utility for order and payment notifications
Sends notifications to the website owner via Telegram Bot API
"""
import requests
import logging
from django.conf import settings
from decouple import config

logger = logging.getLogger(__name__)


def send_telegram_message(message: str, parse_mode: str = 'HTML') -> bool:
    """
    Send a message to Telegram chat using Bot API
    
    Args:
        message: The message text to send
        parse_mode: Message parse mode ('HTML' or 'Markdown')
    
    Returns:
        bool: True if message sent successfully, False otherwise
    """
    try:
        # Get Telegram configuration from environment variables
        telegram_bot_token = config('TELEGRAM_BOT_TOKEN', default='', cast=str).strip()
        telegram_chat_id = config('TELEGRAM_CHAT_ID', default='', cast=str).strip()
        
        # Check if Telegram is configured
        if not telegram_bot_token or not telegram_chat_id:
            logger.warning("Telegram notifications not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")
            return False
        
        # Telegram Bot API endpoint
        url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
        
        # Prepare payload
        payload = {
            'chat_id': telegram_chat_id,
            'text': message,
            'parse_mode': parse_mode
        }
        
        # Send request
        response = requests.post(url, json=payload, timeout=10)
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                logger.info(f"Telegram notification sent successfully to chat {telegram_chat_id}")
                return True
            else:
                error_desc = result.get('description', 'Unknown error')
                error_code = result.get('error_code', 'N/A')
                logger.error(f"Telegram API error (code {error_code}): {error_desc}")
                # Print to console for debugging
                print(f"❌ Telegram Error: {error_desc} (Code: {error_code})")
                return False
        else:
            error_text = response.text
            logger.error(f"Telegram API HTTP error: {response.status_code} - {error_text}")
            # Print to console for debugging
            print(f"❌ Telegram HTTP Error {response.status_code}: {error_text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.exception(f"Failed to send Telegram notification: {e}")
        return False
    except Exception as e:
        logger.exception(f"Unexpected error sending Telegram notification: {e}")
        return False


def send_order_notification(order_data: dict) -> bool:
    """
    Send notification when a new order is placed
    
    Args:
        order_data: Dictionary containing order information
            - order_number: Order number
            - total_amount: Total order amount
            - payment_method: Payment method used
            - customer_name: Customer name
            - customer_email: Customer email
            - items: List of order items
            - shipping_address: Shipping address dict
    
    Returns:
        bool: True if notification sent successfully
    """
    try:
        order_number = order_data.get('order_number', 'N/A')
        total_amount = order_data.get('total_amount', 0)
        payment_method = order_data.get('payment_method', 'Unknown')
        customer_name = order_data.get('customer_name', 'Unknown')
        customer_email = order_data.get('customer_email', 'N/A')
        items = order_data.get('items', [])
        shipping_address = order_data.get('shipping_address', {})
        
        # Format items list
        items_text = ""
        for item in items[:5]:  # Show first 5 items
            item_name = item.get('name', 'Unknown Product')
            item_qty = item.get('quantity', 1)
            item_price = item.get('price', 0)
            items_text += f"  • {item_name} (Qty: {item_qty}) - ${item_price:.2f}\n"
        
        if len(items) > 5:
            items_text += f"  ... and {len(items) - 5} more item(s)\n"
        
        # Format shipping address
        address_parts = []
        if shipping_address.get('first_name') or shipping_address.get('last_name'):
            address_parts.append(f"{shipping_address.get('first_name', '')} {shipping_address.get('last_name', '')}".strip())
        if shipping_address.get('address'):
            address_parts.append(shipping_address.get('address'))
        if shipping_address.get('city'):
            address_parts.append(shipping_address.get('city'))
        if shipping_address.get('province'):
            address_parts.append(shipping_address.get('province'))
        if shipping_address.get('postal_code'):
            address_parts.append(shipping_address.get('postal_code'))
        if shipping_address.get('country'):
            address_parts.append(shipping_address.get('country'))
        address_text = "\n".join(address_parts) if address_parts else "N/A"
        
        # Build message
        message = f"""
🛒 <b>New Order Placed!</b>

📦 Order Number: <code>{order_number}</code>
💰 Total Amount: <b>${total_amount:.2f}</b>
💳 Payment Method: {payment_method}
⏳ Payment Status: Pending

👤 Customer:
  Name: {customer_name}
  Email: {customer_email}

📦 Items ({len(items)}):
{items_text}

📍 Shipping Address:
{address_text}

⚠️ <i>Payment is pending. Order will be processed after payment confirmation.</i>
        """.strip()
        
        return send_telegram_message(message)
        
    except Exception as e:
        logger.exception(f"Error formatting order notification: {e}")
        return False


def send_payment_notification(order_data: dict) -> bool:
    """
    Send notification when payment is completed
    
    Args:
        order_data: Dictionary containing order information
            - order_number: Order number
            - total_amount: Total order amount
            - payment_method: Payment method used
            - customer_name: Customer name
            - customer_email: Customer email
            - items: List of order items
    
    Returns:
        bool: True if notification sent successfully
    """
    try:
        order_number = order_data.get('order_number', 'N/A')
        total_amount = order_data.get('total_amount', 0)
        payment_method = order_data.get('payment_method', 'Unknown')
        customer_name = order_data.get('customer_name', 'Unknown')
        customer_email = order_data.get('customer_email', 'N/A')
        items = order_data.get('items', [])
        
        # Format items list
        items_text = ""
        for item in items[:5]:  # Show first 5 items
            item_name = item.get('name', 'Unknown Product')
            item_qty = item.get('quantity', 1)
            item_price = item.get('price', 0)
            items_text += f"  • {item_name} (Qty: {item_qty}) - ${item_price:.2f}\n"
        
        if len(items) > 5:
            items_text += f"  ... and {len(items) - 5} more item(s)\n"
        
        # Build message
        message = f"""
✅ <b>Payment Received!</b>

📦 Order Number: <code>{order_number}</code>
💰 Amount Paid: <b>${total_amount:.2f}</b>
💳 Payment Method: {payment_method}
✅ Status: <b>PAID</b>

👤 Customer:
  Name: {customer_name}
  Email: {customer_email}

📦 Items ({len(items)}):
{items_text}

🎉 <b>Order is ready to be processed!</b>
        """.strip()
        
        return send_telegram_message(message)
        
    except Exception as e:
        logger.exception(f"Error formatting payment notification: {e}")
        return False


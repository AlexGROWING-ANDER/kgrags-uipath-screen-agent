"""Explicit communication consent; payment/account destruction stays separate."""
import re

PROTECTED = re.compile(r'支付|付款|转账|下单|提交订单|确认购买|立即购买|确认收货|注销|delete account|\b(?:pay|payment|purchase|checkout|transfer money)\b',re.I)
COMMUNICATION = re.compile(r'发送|发布|分享|评论|点赞|关注|发邮件|\b(?:send|publish|share|post|comment|like|follow)\b',re.I)
# Cart cleanup is covered by communication consent. Protected actions are checked first.
CART_REMOVAL_CONTEXT = re.compile(r'购物车|移出|移除|\bcart\b',re.I)
CART_REMOVAL_VERB = re.compile(r'移出|移除|删除|删掉|清空|清除|remove|delete|clear|empty',re.I)

# Use the task intent when a cart action description omits cart context.
# Match explicit add-to-cart wording in the action description.
# through to the side-effect gate below.
CART_ADD_CONTEXT = re.compile(r'加入购物车|加入购物|移入购物车|加购|add to cart',re.I)

TASK_INTENT = ''

def set_task_intent(intent: str) -> None:
    global TASK_INTENT
    TASK_INTENT = str(intent or '')

def authorized_communication(description: str) -> bool:
    text=str(description or '')
    if PROTECTED.search(text):
        return False
    if COMMUNICATION.search(text):
        return True
    if CART_REMOVAL_CONTEXT.search(text) and CART_REMOVAL_VERB.search(text):
        return True
    if CART_REMOVAL_CONTEXT.search(TASK_INTENT) and CART_REMOVAL_VERB.search(text):
        return True
    if CART_REMOVAL_CONTEXT.search(TASK_INTENT) and CART_ADD_CONTEXT.search(text):
        return True
    return False

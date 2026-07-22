"""Small polyglot quality gate for the explainable intent-profile stage."""

from itertools import combinations

from redup.core.scanner_types import CodeBlock
from redup.core.semantic import build_intent_profile, intent_profile_similarity


def _block(file: str, name: str, text: str) -> CodeBlock:
    return CodeBlock(file, 1, len(text.splitlines()), text, function_name=name)


def test_polyglot_intent_profile_precision_and_recall():
    cases = [
        (
            "cart",
            _block(
                "cart.py",
                "calculate_order_total",
                "def calculate_order_total(items):\n"
                "    total = 0\n"
                "    for item in items:\n"
                "        total += item['price'] * item['quantity']\n"
                "    return total\n",
            ),
        ),
        (
            "cart",
            _block(
                "cart.js",
                "computeCartAmount",
                "function computeCartAmount(products) {\n"
                " return products.reduce((sum, item) => sum + item.price * item.quantity, 0);\n"
                "}\n",
            ),
        ),
        (
            "cart",
            _block(
                "cart.php",
                "sumBasket",
                "function sumBasket($items) {\n"
                " $total = 0; foreach ($items as $item) { $total += $item['price']; }\n"
                " return $total;\n}\n",
            ),
        ),
        (
            "auth",
            _block(
                "auth.py",
                "validate_access_token",
                "def validate_access_token(token):\n"
                "    if not token:\n        raise ValueError('missing token')\n"
                "    return jwt.decode(token, SECRET)\n",
            ),
        ),
        (
            "email",
            _block(
                "mail.js",
                "sendWelcomeEmail",
                "async function sendWelcomeEmail(user) {\n"
                " await mailer.send(user.email, 'welcome');\n return true;\n}\n",
            ),
        ),
        (
            "image",
            _block(
                "image.php",
                "resizeImage",
                "function resizeImage($path) {\n"
                " $image = load($path);\n return scale($image, 200, 200);\n}\n",
            ),
        ),
    ]
    profiles = [build_intent_profile(block) for _, block in cases]
    threshold = 0.60
    true_positive = false_positive = false_negative = 0

    for left, right in combinations(range(len(cases)), 2):
        expected = cases[left][0] == cases[right][0]
        predicted = intent_profile_similarity(profiles[left], profiles[right]) >= threshold
        true_positive += int(expected and predicted)
        false_positive += int(not expected and predicted)
        false_negative += int(expected and not predicted)

    precision = true_positive / max(true_positive + false_positive, 1)
    recall = true_positive / max(true_positive + false_negative, 1)

    assert precision == 1.0
    assert recall == 1.0
